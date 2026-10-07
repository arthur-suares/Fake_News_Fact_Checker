"""
Skill Repository - Database access layer for skill-related entities.

Handles Skill and UserSkillState operations.
"""

from sqlalchemy.orm import Session
from app.models import Skill, UserSkillState


class SkillRepository:
    """Repository for skill-related database operations."""

    @staticmethod
    def get_skill_by_code(db: Session, code: str) -> Skill | None:
        """
        Retrieve a skill by its code (SOURCE, EVIDENCE, CONTEXT, VISUAL).

        Args:
            db: Database session
            code: Skill code

        Returns:
            Skill instance or None if not found
        """
        return db.query(Skill).filter(Skill.code == code).first()

    @staticmethod
    def get_skill_by_id(db: Session, skill_id: str) -> Skill | None:
        """
        Retrieve a skill by ID.

        Args:
            db: Database session
            skill_id: ID of the skill

        Returns:
            Skill instance or None if not found
        """
        return db.query(Skill).filter(Skill.id == skill_id).first()

    @staticmethod
    def get_all_skills(db: Session) -> list[Skill]:
        """
        Get all skills.

        Args:
            db: Database session

        Returns:
            List of all Skill instances
        """
        return db.query(Skill).order_by(Skill.code).all()

    @staticmethod
    def get_or_create_user_skill_state(
        db: Session,
        user_id: str,
        skill_id: str,
        initial_mastery: float = 0.3,
    ) -> UserSkillState:
        """
        Get or create a user's skill state.

        Args:
            db: Database session
            user_id: ID of the user
            skill_id: ID of the skill
            initial_mastery: Initial mastery probability if creating new state

        Returns:
            UserSkillState instance
        """
        state = (
            db.query(UserSkillState)
            .filter(
                UserSkillState.user_id == user_id,
                UserSkillState.skill_id == skill_id,
            )
            .first()
        )

        if not state:
            state = UserSkillState(
                user_id=user_id,
                skill_id=skill_id,
                mastery_probability=initial_mastery,
            )
            db.add(state)
            db.commit()
            db.refresh(state)

        return state

    @staticmethod
    def update_user_skill_mastery(
        db: Session,
        user_id: str,
        skill_id: str,
        new_mastery: float,
    ) -> UserSkillState:
        """
        Update a user's skill mastery probability.

        Args:
            db: Database session
            user_id: ID of the user
            skill_id: ID of the skill
            new_mastery: New mastery probability (0 to 1)

        Returns:
            Updated UserSkillState instance

        Raises:
            ValueError: If skill state not found or mastery out of range
        """
        if not (0 <= new_mastery <= 1):
            raise ValueError(f"mastery must be between 0 and 1, got {new_mastery}")

        state = (
            db.query(UserSkillState)
            .filter(
                UserSkillState.user_id == user_id,
                UserSkillState.skill_id == skill_id,
            )
            .first()
        )

        if not state:
            raise ValueError(
                f"UserSkillState not found for user {user_id} and skill {skill_id}"
            )

        state.mastery_probability = new_mastery
        db.commit()
        db.refresh(state)
        return state

    @staticmethod
    def get_user_skill_states(db: Session, user_id: str) -> list[UserSkillState]:
        """
        Get all skill states for a user.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            List of UserSkillState instances
        """
        return (
            db.query(UserSkillState)
            .filter(UserSkillState.user_id == user_id)
            .all()
        )

    @staticmethod
    def get_user_skill_state(
        db: Session,
        user_id: str,
        skill_id: str,
    ) -> UserSkillState | None:
        """
        Get a specific user's skill state.

        Args:
            db: Database session
            user_id: ID of the user
            skill_id: ID of the skill

        Returns:
            UserSkillState instance or None if not found
        """
        return (
            db.query(UserSkillState)
            .filter(
                UserSkillState.user_id == user_id,
                UserSkillState.skill_id == skill_id,
            )
            .first()
        )
