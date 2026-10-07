import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Game, GameStatusEnum, News, Skill, User, UserSkillState
from app.repositories.game_repository import GameRepository
from app.repositories.skill_repository import SkillRepository
from seed import seed_skills


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def create_user(db: Session) -> User:
    user = User(
        name="Test User",
        email="test@example.com",
        phone="0000000000",
        password="hashed-password",
    )
    db.add(user)
    db.commit()
    return user


def test_seed_skills_creates_the_four_core_skills(db):
    seed_skills(db)

    assert {skill.code for skill in SkillRepository.get_all_skills(db)} == {
        "SOURCE",
        "EVIDENCE",
        "CONTEXT",
        "VISUAL",
    }


def test_game_rounds_are_sequential_and_retrievable(db):
    user = create_user(db)
    news_items = [News(title=f"News {index}", content="Claim") for index in (1, 2)]
    db.add_all(news_items)
    db.commit()

    game = GameRepository.create_game(db, user.id)
    GameRepository.create_game_round(db, game.id, news_items[0].id, 1)
    GameRepository.create_game_round(db, game.id, news_items[1].id, 2)

    rounds = GameRepository.get_game_rounds(db, game.id)
    assert [game_round.round_number for game_round in rounds] == [1, 2]
    assert [game_round.news_id for game_round in rounds] == [item.id for item in news_items]
    assert game.status == GameStatusEnum.IN_PROGRESS

    with pytest.raises(ValueError, match="Round number must be 3"):
        GameRepository.create_game_round(db, game.id, news_items[0].id, 4)


def test_user_skill_state_can_be_read_updated_and_is_unique(db):
    user = create_user(db)
    seed_skills(db)
    skill = SkillRepository.get_skill_by_code(db, "SOURCE")

    state = SkillRepository.get_or_create_user_skill_state(db, user.id, skill.id)
    updated = SkillRepository.update_user_skill_mastery(db, user.id, skill.id, 0.8)

    assert SkillRepository.get_user_skill_state(db, user.id, skill.id).id == state.id
    assert updated.mastery_probability == pytest.approx(0.8)
    assert len(SkillRepository.get_user_skill_states(db, user.id)) == 1

    db.add(UserSkillState(user_id=user.id, skill_id=skill.id, mastery_probability=0.4))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("mastery", [-0.01, 1.01])
def test_database_rejects_mastery_outside_probability_range(db, mastery):
    user = create_user(db)
    seed_skills(db)
    skill = SkillRepository.get_skill_by_code(db, "SOURCE")
    db.add(UserSkillState(user_id=user.id, skill_id=skill.id, mastery_probability=mastery))

    with pytest.raises(IntegrityError):
        db.flush()