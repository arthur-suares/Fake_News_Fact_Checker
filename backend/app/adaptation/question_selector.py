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

        # Find skill with lowest mastery (skill to focus on)
        # If a skill hasn't been initialized yet, start with it
        lowest_skill_code = None
        lowest_mastery = 1.0

        for skill_code in BKTManager.VALID_SKILLS:
            if skill_code not in skill_states_by_code:
                # Skill not yet initialized - prioritize it
                lowest_skill_code = skill_code
                break
            
            mastery = skill_states_by_code[skill_code].mastery_probability
            if mastery < lowest_mastery:
                lowest_mastery = mastery
                lowest_skill_code = skill_code

        if not lowest_skill_code:
            # Fallback if somehow we can't determine a skill
            return QuestionSelector._select_fallback_question(db, used_news_ids)

        # Get the skill ID
        skill = SkillRepository.get_skill_by_code(db, lowest_skill_code)
        if not skill:
            return QuestionSelector._select_fallback_question(db, used_news_ids)

        # Try to find a question for this skill from a new news item
        # Strategy: Get all questions for the skill, then find one with news not yet used
        questions = QuestionRepository.get_questions_by_skill(db, skill.id)
        
        for question in questions:
            if question.news_id not in used_news_ids:
                news = question.news
                return (question, news)

        # If all news items for this skill have been used, allow re-using news
        # but pick a different question if possible
        if questions:
            question = questions[0]
            news = question.news
            return (question, news)

        # Fallback: try any available question
        return QuestionSelector._select_fallback_question(db, used_news_ids)

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
