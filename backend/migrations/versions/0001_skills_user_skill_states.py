"""[RF-02] Skill e UserSkillState

Cria as tabelas skills e user_skill_states, cadastra as quatro skills
avaliadas pelo BKT e garante as regras de UserSkillState:
- no máximo um estado por usuário + skill (uq_user_skill);
- mastery_probability entre 0 e 1 (ck_user_skill_mastery_range).

A migration é idempotente: funciona num banco vazio e num banco já
criado por Base.metadata.create_all (app/main.py), completando só o
que estiver faltando.

Revision ID: 0001
Revises:
Create Date: 2026-10-09
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


SKILLS = [
    {
        "code": "SOURCE",
        "name": "Source Analysis",
        "description": "Ability to analyze the origin and source of information",
    },
    {
        "code": "EVIDENCE",
        "name": "Evidence Evaluation",
        "description": "Ability to evaluate the evidence presented to support a claim",
    },
    {
        "code": "CONTEXT",
        "name": "Context Perception",
        "description": "Ability to perceive omitted, distorted, or incompatible context",
    },
    {
        "code": "VISUAL",
        "name": "Visual Analysis",
        "description": "Ability to evaluate if an image really supports the presented claim",
    },
]

MASTERY_CHECK = "mastery_probability >= 0 AND mastery_probability <= 1"


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _check_constraints(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_check_constraints(table)}


def upgrade() -> None:
    tables = _tables()

    # user_skill_states.user_id referencia users
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("email", sa.String(255), nullable=False, unique=True),
            sa.Column("phone", sa.String(20), nullable=False),
            sa.Column("password", sa.String(255), nullable=False),
        )

    if "skills" not in tables:
        op.create_table(
            "skills",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("code", sa.String(50), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_skills_code", "skills", ["code"], unique=True)

    if "user_skill_states" not in tables:
        op.create_table(
            "user_skill_states",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("skill_id", sa.String(36), sa.ForeignKey("skills.id"), nullable=False),
            sa.Column("mastery_probability", sa.Float(), nullable=False, server_default="0.3"),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
            sa.CheckConstraint(MASTERY_CHECK, name="ck_user_skill_mastery_range"),
        )
        op.create_index("ix_user_skill_states_user_id", "user_skill_states", ["user_id"])
        op.create_index("ix_user_skill_states_skill_id", "user_skill_states", ["skill_id"])
    elif "ck_user_skill_mastery_range" not in _check_constraints("user_skill_states"):
        # Banco criado antes da regra: corrige valores fora da faixa e adiciona o CHECK
        op.execute(
            "UPDATE user_skill_states SET mastery_probability = "
            "CASE WHEN mastery_probability < 0 THEN 0 ELSE 1 END "
            "WHERE mastery_probability < 0 OR mastery_probability > 1"
        )
        with op.batch_alter_table("user_skill_states") as batch:
            batch.create_check_constraint("ck_user_skill_mastery_range", MASTERY_CHECK)

    # Cadastra as quatro skills que ainda não existirem
    skills = sa.table(
        "skills",
        sa.column("id", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("created_at", sa.DateTime),
    )
    existing = {row[0] for row in op.get_bind().execute(sa.select(skills.c.code))}
    missing = [
        {**skill, "id": str(uuid.uuid4()), "created_at": datetime.utcnow()}
        for skill in SKILLS
        if skill["code"] not in existing
    ]
    if missing:
        op.bulk_insert(skills, missing)


def downgrade() -> None:
    # users não é removida: pertence à autenticação e pode já existir antes desta migration
    op.drop_index("ix_user_skill_states_skill_id", table_name="user_skill_states")
    op.drop_index("ix_user_skill_states_user_id", table_name="user_skill_states")
    op.drop_table("user_skill_states")
    op.drop_index("ix_skills_code", table_name="skills")
    op.drop_table("skills")
