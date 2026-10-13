import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.adaptation.question_selector import QuestionSelector
from app.database import Base
from app.models import Answer, Game, GameRound, News, Question, Skill, User, UserSkillState


@pytest.fixture
def selector_context():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_factory()

    user = User(
        name="Selector Test",
        email="selector@example.com",
        phone="0000000000",
        password="test",
    )
    db.add(user)
    skills = {
        code: Skill(code=code, name=code)
        for code in ("SOURCE", "EVIDENCE", "CONTEXT", "VISUAL")
    }
    db.add_all(skills.values())
    db.flush()
    for skill in skills.values():
        db.add(
            UserSkillState(
                user_id=user.id,
                skill_id=skill.id,
                mastery_probability=0.5,
            )
        )
    game = Game(user_id=user.id)
    db.add(game)
    db.commit()

    yield db, user, skills, game

    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def add_question(db, skill, question_id, difficulty, news=None):
    if news is None:
        news = News(
            title=question_id,
            content="Content with enough detail",
            image_url="/test-image.png" if skill.code == "VISUAL" else None,
        )
        db.add(news)
        db.flush()
    question = Question(
        id=question_id,
        news_id=news.id,
        skill_id=skill.id,
        text=question_id,
        difficulty=difficulty,
        options={"A": "Option A", "B": "Option B"},
        correct_option="A",
        explanation="Reviewed test explanation.",
    )
    db.add(question)
    db.flush()
    return question


def set_mastery(db, user, skills, values):
    for code, mastery in values.items():
        state = (
            db.query(UserSkillState)
            .filter_by(user_id=user.id, skill_id=skills[code].id)
            .one()
        )
        state.mastery_probability = mastery
    db.commit()


def record_answer(db, user, question, game=None):
    game = game or Game(user_id=user.id)
    db.add(game)
    db.flush()
    game_round = GameRound(
        game_id=game.id,
        news_id=question.news_id,
        round_number=1,
    )
    db.add(game_round)
    db.flush()
    db.add(
        Answer(
            user_id=user.id,
            game_round_id=game_round.id,
            question_id=question.id,
            selected_option="A",
            correct=True,
        )
    )
    db.commit()
    return game


def test_selects_question_for_lowest_mastery_skill(selector_context):
    db, user, skills, game = selector_context
    set_mastery(
        db,
        user,
        skills,
        {"SOURCE": 0.8, "EVIDENCE": 0.6, "CONTEXT": 0.4, "VISUAL": 0.2},
    )
    questions = [
        add_question(db, skill, f"q-{code}", 0.3)
        for code, skill in skills.items()
    ]
    db.commit()

    selected, _ = QuestionSelector.select_next_question(db, user.id, game.id)

    assert selected.skill.code == "VISUAL"
    assert selected in questions


def test_ignores_answered_question(selector_context):
    db, user, skills, game = selector_context
    set_mastery(db, user, skills, {"SOURCE": 0.1})
    answered = add_question(db, skills["SOURCE"], "q-answered", 0.1)
    available = add_question(db, skills["SOURCE"], "q-available", 0.2)
    db.commit()
    record_answer(db, user, answered, game)

    selected, _ = QuestionSelector.select_next_question(db, user.id, game.id)

    assert selected.id == available.id


def test_answer_from_previous_game_is_still_excluded(selector_context):
    db, user, skills, current_game = selector_context
    set_mastery(db, user, skills, {"SOURCE": 0.1})
    answered = add_question(db, skills["SOURCE"], "q-old-game", 0.1)
    available = add_question(db, skills["SOURCE"], "q-new-game", 0.2)
    db.commit()
    record_answer(db, user, answered)

    selected, _ = QuestionSelector.select_next_question(
        db, user.id, current_game.id
    )

    assert selected.id == available.id


def test_prefers_difficulty_closest_to_mastery(selector_context):
    db, user, skills, game = selector_context
    set_mastery(db, user, skills, {"SOURCE": 0.3})
    add_question(db, skills["SOURCE"], "q-0.10", 0.10)
    expected = add_question(db, skills["SOURCE"], "q-0.25", 0.25)
    add_question(db, skills["SOURCE"], "q-0.60", 0.60)
    db.commit()

    selected, _ = QuestionSelector.select_next_question(db, user.id, game.id)

    assert selected.id == expected.id


def test_falls_back_to_another_tracked_skill(selector_context):
    db, user, skills, game = selector_context
    set_mastery(
        db,
        user,
        skills,
        {"SOURCE": 0.5, "EVIDENCE": 0.6, "CONTEXT": 0.7, "VISUAL": 0.1},
    )
    exhausted = add_question(db, skills["VISUAL"], "q-exhausted", 0.1)
    available = add_question(db, skills["SOURCE"], "q-fallback-skill", 0.5)
    db.commit()
    record_answer(db, user, exhausted)

    selected, _ = QuestionSelector.select_next_question(db, user.id, game.id)

    assert selected.id == available.id


def test_global_fallback_rejects_question_from_untracked_skill(selector_context):
    db, user, skills, game = selector_context
    for code, mastery in {
        "SOURCE": 0.5,
        "EVIDENCE": 0.6,
        "CONTEXT": 0.7,
        "VISUAL": 0.8,
    }.items():
        set_mastery(db, user, skills, {code: mastery})
    extra_skill = Skill(code="EXTRA", name="Extra")
    db.add(extra_skill)
    db.flush()
    add_question(db, extra_skill, "q-global", 0.4)
    db.commit()

    assert QuestionSelector.select_next_question(db, user.id, game.id) is None


def test_returns_none_when_all_questions_were_answered(selector_context):
    db, user, skills, game = selector_context
    questions = [
        add_question(db, skill, f"q-{code}", 0.3)
        for code, skill in skills.items()
    ]
    db.commit()
    for question in questions:
        record_answer(db, user, question)

    assert QuestionSelector.select_next_question(db, user.id, game.id) is None


def test_incomplete_question_is_not_eligible(selector_context):
    db, user, skills, game = selector_context
    invalid = add_question(db, skills["SOURCE"], "q-no-explanation", 0.2)
    invalid.explanation = None
    db.commit()

    assert QuestionSelector.select_next_question(db, user.id, game.id) is None


def test_selection_is_deterministic_for_equal_candidates(selector_context):
    db, user, skills, game = selector_context
    set_mastery(db, user, skills, {"SOURCE": 0.3})
    expected = add_question(db, skills["SOURCE"], "q-a", 0.3)
    add_question(db, skills["SOURCE"], "q-b", 0.3)
    db.commit()

    first = QuestionSelector.select_next_question(db, user.id, game.id)
    second = QuestionSelector.select_next_question(db, user.id, game.id)

    assert first[0].id == second[0].id == expected.id


def test_answering_question_does_not_hide_other_question_for_same_news(
    selector_context,
):
    db, user, skills, game = selector_context
    set_mastery(db, user, skills, {"SOURCE": 0.2, "CONTEXT": 0.3})
    news = News(title="Shared news", content="Content")
    db.add(news)
    db.flush()
    answered = add_question(db, skills["SOURCE"], "q-source", 0.2, news)
    available = add_question(db, skills["CONTEXT"], "q-context", 0.3, news)
    db.commit()
    record_answer(db, user, answered, game)

    selected, _ = QuestionSelector.select_next_question(db, user.id, game.id)

    assert selected.id == available.id
    assert selected.news_id == answered.news_id