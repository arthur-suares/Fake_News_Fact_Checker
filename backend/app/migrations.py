"""Small explicit schema migrations for projects without Alembic configured."""

from sqlalchemy import Engine, inspect, text


def upgrade_game_round_question(engine: Engine) -> None:
    """Add and backfill game_rounds.question_id on existing databases."""
    inspector = inspect(engine)
    if "game_rounds" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("game_rounds")}
    with engine.begin() as connection:
        if "question_id" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE game_rounds "
                    "ADD COLUMN question_id VARCHAR(36) REFERENCES questions(id)"
                )
            )

        tables = set(inspect(connection).get_table_names())
        if {"answers", "questions"}.issubset(tables):
            connection.execute(
                text(
                    """
                    UPDATE game_rounds
                    SET question_id = COALESCE(
                        (
                            SELECT answers.question_id
                            FROM answers
                            WHERE answers.game_round_id = game_rounds.id
                            ORDER BY answers.created_at, answers.id
                            LIMIT 1
                        ),
                        (
                            SELECT questions.id
                            FROM questions
                            WHERE questions.news_id = game_rounds.news_id
                            ORDER BY questions.id
                            LIMIT 1
                        )
                    )
                    WHERE question_id IS NULL
                    """
                )
            )

        indexes = {index["name"] for index in inspect(connection).get_indexes("game_rounds")}
        if "ix_game_rounds_question_id" not in indexes:
            connection.execute(
                text("CREATE INDEX ix_game_rounds_question_id ON game_rounds (question_id)")
            )

        if "answers" in tables:
            duplicate_round = connection.execute(
                text(
                    """
                    SELECT game_round_id
                    FROM answers
                    GROUP BY game_round_id
                    HAVING COUNT(*) > 1
                    LIMIT 1
                    """
                )
            ).first()
            if duplicate_round:
                raise RuntimeError(
                    "Cannot enforce one answer per round: duplicate historical answers exist. "
                    "Review the answers table before applying this migration."
                )

            unique_constraints = inspect(connection).get_unique_constraints("answers")
            unique_indexes = inspect(connection).get_indexes("answers")
            has_round_unique = any(
                constraint.get("column_names") == ["game_round_id"]
                for constraint in unique_constraints
            ) or any(
                index.get("unique") and index.get("column_names") == ["game_round_id"]
                for index in unique_indexes
            )
            if not has_round_unique:
                connection.execute(
                    text(
                        "CREATE UNIQUE INDEX uq_answers_game_round_id "
                        "ON answers (game_round_id)"
                    )
                )

        round_columns = {column["name"] for column in inspect(connection).get_columns("game_rounds")}
        if {"game_id", "round_number"}.issubset(round_columns):
            duplicate_round = connection.execute(
                text(
                    """
                    SELECT game_id, round_number
                    FROM game_rounds
                    GROUP BY game_id, round_number
                    HAVING COUNT(*) > 1
                    LIMIT 1
                    """
                )
            ).first()
            if duplicate_round:
                raise RuntimeError(
                    "Cannot enforce sequential game rounds: duplicate game_id/round_number rows exist. "
                    "Review the game_rounds table before applying this migration."
                )

            unique_constraints = inspect(connection).get_unique_constraints("game_rounds")
            unique_indexes = inspect(connection).get_indexes("game_rounds")
            has_round_number_unique = any(
                constraint.get("column_names") == ["game_id", "round_number"]
                for constraint in unique_constraints
            ) or any(
                index.get("unique") and index.get("column_names") == ["game_id", "round_number"]
                for index in unique_indexes
            )
            if not has_round_number_unique:
                connection.execute(
                    text(
                        "CREATE UNIQUE INDEX uq_game_round_number "
                        "ON game_rounds (game_id, round_number)"
                    )
                )


if __name__ == "__main__":
    from app.database import Base, engine
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    upgrade_game_round_question(engine)
    print("Migrações do banco aplicadas.")