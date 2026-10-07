"""
Answer Service - Business logic for handling user answers.

Processes answers, updates skill mastery using BKT, and returns feedback.
"""

from sqlalchemy.orm import Session

from app.repositories.answer_repository import AnswerRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.game_repository import GameRepository
from app.repositories.skill_repository import SkillRepository
from app.bkt.manager import BKTManager
from app.models import Answer, Question, Skill


class AnswerService:
    """Service for answer-related business logic."""

    @staticmethod
    def process_answer(
        db: Session,
        user_id: str,
        game_round_id: str,
        question_id: str,
        selected_option: str,
        confidence: int | None = None,
        response_time: int | None = None,
    ) -> dict:
        """
        Process a user's answer to a question.

        This:
        1. Validates the answer
        2. Stores it in the database
        3. Updates user's skill mastery using BKT
        4. Returns feedback

        Args:
            db: Database session
            user_id: ID of the user
            game_round_id: ID of the game round
            question_id: ID of the question
            selected_option: The option selected (e.g., "A", "B", "C")
            confidence: User's confidence (1-5)
            response_time: Time taken in milliseconds

        Returns:
            Dictionary with feedback including correctness, skill, and new mastery

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        if confidence is not None and not (1 <= confidence <= 5):
            raise ValueError("confidence must be between 1 and 5")

        if response_time is not None and response_time < 0:
            raise ValueError("response_time must be non-negative")

        # Get question details
        question = QuestionRepository.get_question_by_id(db, question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")

        # Check if answer is correct
        is_correct = selected_option == question.correct_option

        # Get skill associated with question
        skill = question.skill
        if not skill:
            raise ValueError(f"Question {question_id} has no skill associated")

        # Get current user skill state
        user_skill_state = SkillRepository.get_user_skill_state(
            db,
            user_id,
            skill.id,
        )

        if not user_skill_state:
            # Should not happen if initialization was done properly
            user_skill_state = SkillRepository.get_or_create_user_skill_state(
                db,
                user_id,
                skill.id,
            )

        current_mastery = user_skill_state.mastery_probability

        # Update mastery using BKT
        new_mastery = BKTManager.update(
            skill.code,
            current_mastery,
            is_correct,
        )

        # Save answer
        answer = AnswerRepository.create_answer(
            db,
            user_id,
            game_round_id,
            question_id,
            selected_option,
            is_correct,
            confidence,
            response_time,
        )

        # Update skill state in database
        SkillRepository.update_user_skill_mastery(
            db,
            user_id,
            skill.id,
            new_mastery,
        )

        # Prepare response
        return {
            "answer_id": answer.id,
            "correct": is_correct,
            "skill_code": skill.code,
            "skill_name": skill.name,
            "old_mastery": current_mastery,
            "new_mastery": new_mastery,
            "explanation": question.explanation,
            "correct_option": question.correct_option,
        }

    @staticmethod
    def get_user_skill_profile(db: Session, user_id: str) -> dict:
        """
        Get a user's complete skill profile.

        Returns mastery probabilities for all four skills.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            Dictionary with skills and their mastery probabilities
        """
        user_skill_states = SkillRepository.get_user_skill_states(db, user_id)

        skills = []
        for state in user_skill_states:
            skills.append({
                "skill_id": state.skill_id,
                "skill_code": state.skill.code,
                "skill_name": state.skill.name,
                "mastery_probability": state.mastery_probability,
                "updated_at": state.updated_at.isoformat(),
            })

        return {
            "user_id": user_id,
            "skills": sorted(skills, key=lambda x: x["skill_code"]),
            "updated_at": max(
                (s["updated_at"] for s in skills),
                default=None,
            ),
        }
