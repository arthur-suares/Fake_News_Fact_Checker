"""
Adaptive Question Selector.

Selects the next question based on user's skill mastery profile.

MVP Strategy (simple and functional):
1. Get mastery levels for all four skills
2. Find the skill with lowest mastery
3. Select an unanswered question for that skill
4. If no questions available, use fallback strategy

This keeps the MVP simple while leaving room for more sophisticated algorithms.
"""

from sqlalchemy.orm import Session
from app.bkt.manager import BKTManager
from app.repositories.answer_repository import AnswerRepository
from app.repositories.skill_repository import SkillRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.game_repository import GameRepository
from app.models import Question, News


class QuestionSelector:
    """Selects questions adaptively based on user skill profile."""

    @staticmethod
    def select_next_question(
        db: Session,
        user_id: str,
        game_id: str,
    ) -> tuple[Question, News] | None:
        """
        Select the next question for a user in a game.

        Skills are considered from lowest to highest mastery, with BKT skill
        order breaking mastery ties. Prefer unused news within the game, then
        match difficulty to mastery; question ID breaks remaining ties.

        Args:
            db: Database session
            user_id: ID of the user
            game_id: ID of the game

        Returns:
            Tuple of (Question, News) or None if no questions available
        """
        # News repetition is secondary to avoiding previously answered questions.
        game_rounds = GameRepository.get_game_rounds(db, game_id)
        used_news_ids = {game_round.news_id for game_round in game_rounds}
        answered_question_ids = AnswerRepository.get_answered_question_ids_for_user(
            db, user_id
        )

        user_skill_states = SkillRepository.get_user_skill_states(db, user_id)
        mastery_by_code = {
            state.skill.code: state.mastery_probability
            for state in user_skill_states
        }
        skill_order = {
            skill_code: position
            for position, skill_code in enumerate(BKTManager.VALID_SKILLS)
        }
        mastery_by_code = {
            skill_code: mastery_by_code.get(skill_code, 0.3)
            for skill_code in BKTManager.VALID_SKILLS
        }
        ordered_skill_codes = sorted(
            BKTManager.VALID_SKILLS,
            key=lambda code: (mastery_by_code[code], skill_order[code]),
        )

        unanswered_by_skill: dict[str, list[Question]] = {}
        for skill_code in ordered_skill_codes:
            skill = SkillRepository.get_skill_by_code(db, skill_code)
            if not skill:
                continue

            questions = QuestionRepository.get_questions_by_skill(
                db, skill.id, limit=None
            )
            unanswered_by_skill[skill_code] = [
                question
                for question in questions
                if question.id not in answered_question_ids
            ]

        # First pass avoids repeating a news item whenever another question exists.
        for skill_code in ordered_skill_codes:
            fresh_news_questions = [
                question
                for question in unanswered_by_skill.get(skill_code, [])
                if question.news_id not in used_news_ids
            ]
            selected = QuestionSelector._closest_difficulty_question(
                fresh_news_questions, mastery_by_code[skill_code]
            )
            if selected:
                return (selected, selected.news)

        # If every remaining question uses an existing news item, keep the skill
        # priority and choose the closest difficulty rather than returning None.
        for skill_code in ordered_skill_codes:
            selected = QuestionSelector._closest_difficulty_question(
                unanswered_by_skill.get(skill_code, []), mastery_by_code[skill_code]
            )
            if selected:
                return (selected, selected.news)

        # Global fallback also covers content whose skill is not yet in the BKT registry.
        unanswered_questions = [
            question
            for question in QuestionRepository.get_all_questions(db)
            if question.id not in answered_question_ids
        ]
        if not unanswered_questions:
            return None

        priority_by_code = {
            code: index for index, code in enumerate(ordered_skill_codes)
        }
        selected = min(
            unanswered_questions,
            key=lambda question: (
                question.news_id in used_news_ids,
                priority_by_code.get(question.skill.code, len(priority_by_code)),
                abs(
                    question.difficulty
                    - mastery_by_code.get(question.skill.code, 0.3)
                ),
                question.id,
            ),
        )
        return (selected, selected.news)

    @staticmethod
    def _closest_difficulty_question(
        questions: list[Question],
        mastery: float,
    ) -> Question | None:
        """Choose nearest difficulty; stable question ID resolves equal distances."""
        if not questions:
            return None
        return min(
            questions,
            key=lambda question: (abs(question.difficulty - mastery), question.id),
        )
