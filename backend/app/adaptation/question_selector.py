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
from app.repositories.skill_repository import SkillRepository
from app.repositories.question_repository import QuestionRepository, NewsRepository
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

        Strategy:
        1. Get user's mastery levels for all skills
        2. Find skill with lowest mastery
        3. Select an unanswered question for that skill from a new news item
        4. If no questions available, fallback to any available question

        Args:
            db: Database session
            user_id: ID of the user
            game_id: ID of the game

        Returns:
            Tuple of (Question, News) or None if no questions available
        """
        # Get all existing game rounds to avoid repeating news
        game_rounds = GameRepository.get_game_rounds(db, game_id)
        used_news_ids = [round.news_id for round in game_rounds]

        # Get user's skill states
        user_skill_states = SkillRepository.get_user_skill_states(db, user_id)
        
        if not user_skill_states:
            # If no skill states exist, this shouldn't happen in normal flow
            # but handle gracefully by selecting a random question
            return QuestionSelector._select_fallback_question(db, used_news_ids)

        # Map skill states by skill code (need to join with skills table)
        skill_states_by_code = {}
        for state in user_skill_states:
            skill = state.skill
            skill_states_by_code[skill.code] = state

        # Order skills from lowest to highest mastery (skill to focus on first).
        # Skills not initialized yet get priority.
        def mastery_of(skill_code: str) -> float:
            state = skill_states_by_code.get(skill_code)
            return state.mastery_probability if state else -1.0

        ordered_skill_codes = sorted(BKTManager.VALID_SKILLS, key=mastery_of)

        # Try the weakest skill first; if all its news were already used in this
        # game, move on to the next weakest instead of repeating news.
        reusable: tuple[Question, News] | None = None
        for skill_code in ordered_skill_codes:
            skill = SkillRepository.get_skill_by_code(db, skill_code)
            if not skill:
                continue

            questions = QuestionRepository.get_questions_by_skill(db, skill.id)
            for question in questions:
                if question.news_id not in used_news_ids:
                    return (question, question.news)

            if questions and reusable is None:
                reusable = (questions[0], questions[0].news)

        # No unused news for any skill: try any unused news, then allow repeating
        fallback = QuestionSelector._select_fallback_question(db, used_news_ids)
        return fallback or reusable

    @staticmethod
    def _select_fallback_question(
        db: Session,
        exclude_news_ids: list[str],
    ) -> tuple[Question, News] | None:
        """
        Fallback: select any available question.

        Args:
            db: Database session
            exclude_news_ids: News IDs to avoid if possible

        Returns:
            Tuple of (Question, News) or None if none available
        """
        # Try to get news that hasn't been used
        news = NewsRepository.get_random_news(db, exclude_ids=exclude_news_ids)
        
        if news:
            questions = QuestionRepository.get_questions_by_news(db, news.id)
            if questions:
                return (questions[0], news)

        # If that doesn't work, get any news
        all_news = NewsRepository.get_all_news(db, limit=1)
        if all_news:
            news = all_news[0]
            questions = QuestionRepository.get_questions_by_news(db, news.id)
            if questions:
                return (questions[0], news)

        return None
