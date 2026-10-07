from alembic import op

from app.database import Base
from app import models  # noqa: F401


revision = "0001_game_and_skills"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keep the first migration limited to this feature and its FK prerequisites.
    tables = [
        models.User.__table__,
        models.News.__table__,
        models.Skill.__table__,
        models.UserSkillState.__table__,
        models.Game.__table__,
        models.GameRound.__table__,
    ]
    Base.metadata.create_all(bind=op.get_bind(), tables=tables, checkfirst=True)

    connection = op.get_bind()
    for code, name, description in (
        ("SOURCE", "Source Analysis", "Ability to analyze the origin and source of information"),
        ("EVIDENCE", "Evidence Evaluation", "Ability to evaluate evidence supporting a claim"),
        ("CONTEXT", "Context Perception", "Ability to perceive omitted or distorted context"),
        ("VISUAL", "Visual Analysis", "Ability to evaluate the image-claim relationship"),
    ):
        existing = connection.execute(
            models.Skill.__table__.select().where(models.Skill.code == code)
        ).first()
        if existing is None:
            connection.execute(
                models.Skill.__table__.insert().values(
                    code=code,
                    name=name,
                    description=description,
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    for table in (
        models.GameRound.__table__,
        models.Game.__table__,
        models.UserSkillState.__table__,
        models.Skill.__table__,
    ):
        table.drop(bind=bind, checkfirst=True)