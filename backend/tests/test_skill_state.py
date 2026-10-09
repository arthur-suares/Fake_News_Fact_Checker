"""
[RF-02] Skill e UserSkillState: modelo, regras e migration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Skill, User, UserSkillState
from app.repositories.skill_repository import SkillRepository
from seed import seed_skills


BACKEND_DIR = Path(__file__).parents[1]
SKILL_CODES = {"SOURCE", "EVIDENCE", "CONTEXT", "VISUAL"}


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    seed_skills(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def user(db):
    user = User(name="Ana", email="ana@example.com", phone="0", password="x")
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def source(db):
    return SkillRepository.get_skill_by_code(db, "SOURCE")


# ------------------------------------------------------------
# Skills
# ------------------------------------------------------------

def test_four_skills_exist(db):
    skills = SkillRepository.get_all_skills(db)

    assert {skill.code for skill in skills} == SKILL_CODES
    assert all(skill.id and skill.name and skill.description for skill in skills)


def test_seed_skills_is_idempotent(db):
    seed_skills(db)

    assert db.query(Skill).count() == 4


def test_skill_code_is_unique(db):
    db.add(Skill(code="SOURCE", name="Duplicada"))

    with pytest.raises(IntegrityError):
        db.commit()


# ------------------------------------------------------------
# UserSkillState
# ------------------------------------------------------------

def test_only_one_state_per_user_and_skill(db, user, source):
    db.add(UserSkillState(user_id=user.id, skill_id=source.id, mastery_probability=0.3))
    db.commit()
    db.add(UserSkillState(user_id=user.id, skill_id=source.id, mastery_probability=0.5))

    with pytest.raises(IntegrityError):
        db.commit()


def test_get_or_create_does_not_duplicate_state(db, user, source):
    first = SkillRepository.get_or_create_user_skill_state(db, user.id, source.id)
    second = SkillRepository.get_or_create_user_skill_state(db, user.id, source.id)

    assert first.id == second.id
    assert db.query(UserSkillState).count() == 1


@pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
def test_mastery_accepts_values_between_0_and_1(db, user, source, value):
    db.add(UserSkillState(user_id=user.id, skill_id=source.id, mastery_probability=value))
    db.commit()


@pytest.mark.parametrize("value", [-0.1, 1.1, None])
def test_mastery_outside_0_and_1_is_rejected(user, source, value):
    with pytest.raises(ValueError):
        UserSkillState(user_id=user.id, skill_id=source.id, mastery_probability=value)


def test_database_check_rejects_mastery_outside_0_and_1(db, user, source):
    # Ignora a validação do ORM para garantir que o próprio banco barra o valor
    with pytest.raises(IntegrityError):
        db.execute(
            text(
                "INSERT INTO user_skill_states (id, user_id, skill_id, mastery_probability, updated_at) "
                "VALUES ('x', :user_id, :skill_id, 1.5, CURRENT_TIMESTAMP)"
            ),
            {"user_id": user.id, "skill_id": source.id},
        )


def test_state_can_be_queried_and_updated(db, user, source):
    SkillRepository.get_or_create_user_skill_state(db, user.id, source.id)

    state = SkillRepository.get_user_skill_state(db, user.id, source.id)
    assert state.mastery_probability == pytest.approx(0.3)
    first_updated_at = state.updated_at

    SkillRepository.update_user_skill_mastery(db, user.id, source.id, 0.72)

    state = SkillRepository.get_user_skill_state(db, user.id, source.id)
    assert state.mastery_probability == pytest.approx(0.72)
    assert state.updated_at >= first_updated_at
    assert state.skill.code == "SOURCE"


def test_update_rejects_mastery_outside_0_and_1(db, user, source):
    SkillRepository.get_or_create_user_skill_state(db, user.id, source.id)

    with pytest.raises(ValueError):
        SkillRepository.update_user_skill_mastery(db, user.id, source.id, 1.5)


# ------------------------------------------------------------
# Migration
# ------------------------------------------------------------

def _alembic(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    return config


def _check_names(engine, table):
    return {c["name"] for c in inspect(engine).get_check_constraints(table)}


def _unique_names(engine, table):
    return {c["name"] for c in inspect(engine).get_unique_constraints(table)}


def test_migration_creates_tables_and_four_skills(tmp_path):
    url = f"sqlite:///{tmp_path / 'fresh.db'}"

    command.upgrade(_alembic(url), "head")

    engine = create_engine(url)
    with engine.connect() as connection:
        codes = {row[0] for row in connection.execute(text("SELECT code FROM skills"))}
    assert codes == SKILL_CODES
    assert "uq_user_skill" in _unique_names(engine, "user_skill_states")
    assert "ck_user_skill_mastery_range" in _check_names(engine, "user_skill_states")


def test_migration_completes_database_created_without_rules(tmp_path):
    url = f"sqlite:///{tmp_path / 'legacy.db'}"
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id VARCHAR(36) PRIMARY KEY, name VARCHAR(100) NOT NULL, "
                                "email VARCHAR(255) NOT NULL, phone VARCHAR(20) NOT NULL, password VARCHAR(255) NOT NULL)"))
        connection.execute(text("CREATE TABLE skills (id VARCHAR(36) PRIMARY KEY, code VARCHAR(50) NOT NULL, "
                                "name VARCHAR(255) NOT NULL, description TEXT, created_at DATETIME NOT NULL)"))
        connection.execute(text("CREATE UNIQUE INDEX ix_skills_code ON skills (code)"))
        connection.execute(text("INSERT INTO skills VALUES ('s1', 'SOURCE', 'Source Analysis', NULL, CURRENT_TIMESTAMP)"))
        connection.execute(text(
            "CREATE TABLE user_skill_states (id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL, "
            "skill_id VARCHAR(36) NOT NULL, mastery_probability FLOAT NOT NULL, updated_at DATETIME NOT NULL, "
            "CONSTRAINT uq_user_skill UNIQUE (user_id, skill_id))"
        ))
        connection.execute(text("CREATE INDEX ix_user_skill_states_user_id ON user_skill_states (user_id)"))
        connection.execute(text("CREATE INDEX ix_user_skill_states_skill_id ON user_skill_states (skill_id)"))
        connection.execute(text("INSERT INTO user_skill_states VALUES ('st1', 'u1', 's1', 1.7, CURRENT_TIMESTAMP)"))

    command.upgrade(_alembic(url), "head")

    with engine.connect() as connection:
        codes = [row[0] for row in connection.execute(text("SELECT code FROM skills"))]
        mastery = connection.execute(text("SELECT mastery_probability FROM user_skill_states")).scalar()
    assert sorted(codes) == sorted(SKILL_CODES)  # completa sem duplicar SOURCE
    assert mastery == 1.0                        # valor fora da faixa corrigido
    assert "ck_user_skill_mastery_range" in _check_names(engine, "user_skill_states")


def test_migration_downgrade_removes_tables(tmp_path):
    url = f"sqlite:///{tmp_path / 'down.db'}"
    config = _alembic(url)
    command.upgrade(config, "head")

    command.downgrade(config, "base")

    tables = set(inspect(create_engine(url)).get_table_names())
    assert "skills" not in tables
    assert "user_skill_states" not in tables
