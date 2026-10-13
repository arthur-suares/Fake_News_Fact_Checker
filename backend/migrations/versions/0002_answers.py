"""[RF-04] Persistir respostas das rodadas

Cria a tabela answers, vinculada a usuário, rodada e pergunta, com as regras:
- confidence entre 1 e 5 (ck_answer_confidence_range);
- response_time em milissegundos, >= 0 (ck_answer_response_time_non_negative).

Num banco vazio também cria as tabelas das quais answers depende
(news, questions, games, game_rounds). Como a 0001, é idempotente: num
banco já criado por Base.metadata.create_all só adiciona o que falta.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-09
"""

import sqlalchemy as sa
from alembic import op


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


CONFIDENCE_CHECK = "confidence IS NULL OR (confidence >= 1 AND confidence <= 5)"
RESPONSE_TIME_CHECK = "response_time IS NULL OR response_time >= 0"


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _check_constraints(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_check_constraints(table)}


def _create_dependencies(tables: set[str]) -> None:
    if "news" not in tables:
        op.create_table(
            "news",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("image_url", sa.String(2048), nullable=True),
            sa.Column("verdict", sa.String(100), nullable=True),
            sa.Column("fact_check_data", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

    if "questions" not in tables:
        op.create_table(
            "questions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("news_id", sa.String(36), sa.ForeignKey("news.id"), nullable=False),
            sa.Column("skill_id", sa.String(36), sa.ForeignKey("skills.id"), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("difficulty", sa.Float(), nullable=False),
            sa.Column("options", sa.JSON(), nullable=False),
            sa.Column("correct_option", sa.String(10), nullable=False),
            sa.Column("explanation", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_questions_news_id", "questions", ["news_id"])
        op.create_index("ix_questions_skill_id", "questions", ["skill_id"])

    if "games" not in tables:
        op.create_table(
            "games",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column(
                "status",
                sa.Enum("IN_PROGRESS", "FINISHED", name="gamestatusenum"),
                nullable=False,
            ),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_games_user_id", "games", ["user_id"])

    if "game_rounds" not in tables:
        op.create_table(
            "game_rounds",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("game_id", sa.String(36), sa.ForeignKey("games.id"), nullable=False),
            sa.Column("news_id", sa.String(36), sa.ForeignKey("news.id"), nullable=False),
            sa.Column("round_number", sa.Integer(), nullable=False),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_game_rounds_game_id", "game_rounds", ["game_id"])
        op.create_index("ix_game_rounds_news_id", "game_rounds", ["news_id"])


def upgrade() -> None:
    tables = _tables()
    _create_dependencies(tables)

    if "answers" not in tables:
        op.create_table(
            "answers",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("game_round_id", sa.String(36), sa.ForeignKey("game_rounds.id"), nullable=False),
            sa.Column("question_id", sa.String(36), sa.ForeignKey("questions.id"), nullable=False),
            sa.Column("selected_option", sa.String(10), nullable=False),
            sa.Column("correct", sa.Boolean(), nullable=False),
            sa.Column("confidence", sa.Integer(), nullable=True),
            sa.Column("response_time", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.CheckConstraint(CONFIDENCE_CHECK, name="ck_answer_confidence_range"),
            sa.CheckConstraint(RESPONSE_TIME_CHECK, name="ck_answer_response_time_non_negative"),
        )
        op.create_index("ix_answers_user_id", "answers", ["user_id"])
        op.create_index("ix_answers_game_round_id", "answers", ["game_round_id"])
        op.create_index("ix_answers_question_id", "answers", ["question_id"])
        return

    existing = _check_constraints("answers")
    missing = {
        "ck_answer_confidence_range": CONFIDENCE_CHECK,
        "ck_answer_response_time_non_negative": RESPONSE_TIME_CHECK,
    }
    missing = {name: rule for name, rule in missing.items() if name not in existing}
    if not missing:
        return

    # Banco criado antes das regras: valores inválidos viram "não informado"
    op.execute("UPDATE answers SET confidence = NULL WHERE confidence < 1 OR confidence > 5")
    op.execute("UPDATE answers SET response_time = NULL WHERE response_time < 0")
    with op.batch_alter_table("answers") as batch:
        for name, rule in missing.items():
            batch.create_check_constraint(name, rule)


def downgrade() -> None:
    # Remove answers e as tabelas do jogo que dependem de skills,
    # para que o downgrade da 0001 consiga remover skills em seguida.
    for table in ("answers", "game_rounds", "games", "questions", "news"):
        op.drop_table(table)
    sa.Enum(name="gamestatusenum").drop(op.get_bind(), checkfirst=True)
