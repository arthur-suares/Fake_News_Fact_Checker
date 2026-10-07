import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Base, User, Skill, News, Question
import uuid

# Setup in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_question_creation_with_skill(db):
    # Create a skill
    skill = Skill(code="SOURCE", name="Source Analysis")
    db.add(skill)
    db.commit()

    # Create news
    news = News(title="Test News", content="Content")
    db.add(news)
    db.commit()

    # Create question
    question = Question(
        news_id=news.id,
        skill_id=skill.id,
        text="Test Question",
        difficulty=0.5,
        options={"A": "Opt A", "B": "Opt B"},
        correct_option="A"
    )
    db.add(question)
    db.commit()

    assert question.skill_id == skill.id
    assert question.difficulty == 0.5

def test_skill_recovery_from_question(db):
    skill = Skill(code="EVIDENCE", name="Evidence Evaluation")
    db.add(skill)
    db.commit()

    news = News(title="Test News", content="Content")
    db.add(news)
    db.commit()

    question = Question(
        news_id=news.id,
        skill_id=skill.id,
        text="Test Question",
        difficulty=0.5,
        options={"A": "Opt A", "B": "Opt B"},
        correct_option="A"
    )
    db.add(question)
    db.commit()

    # Test recovery of Skill object
    assert question.skill is not None
    assert question.skill.id == skill.id
    assert question.skill.code == "EVIDENCE"

def test_difficulty_boundaries(db):
    skill = Skill(code="CONTEXT", name="Context Perception")
    db.add(skill)
    db.commit()

    news = News(title="Test News", content="Content")
    db.add(news)
    db.commit()

    # Valid values
    for diff in [0, 0.5, 1]:
        q = Question(
            news_id=news.id,
            skill_id=skill.id,
            text=f"Diff {diff}",
            difficulty=diff,
            options={"A": "A"},
            correct_option="A"
        )
        db.add(q)
    db.commit()

    # We can't easily test DB-level constraints without a specific check,
    # but we can verify they were saved correctly.
    questions = db.query(Question).all()
    difficulties = [q.difficulty for q in questions]
    assert 0 in difficulties
    assert 0.5 in difficulties
    assert 1 in difficulties

def test_mvp_seed_data_consistency(db):
    from seed import seed_skills, seed_sample_news_and_questions

    seed_skills(db)
    seed_sample_news_and_questions(db)

    questions = db.query(Question).all()
    assert len(questions) > 0

    for q in questions:
        assert q.skill_id is not None
        assert q.difficulty is not None
        assert 0 <= q.difficulty <= 1
        assert q.skill is not None
