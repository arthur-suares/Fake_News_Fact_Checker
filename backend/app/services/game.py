"""
Game Service - Business logic for game operations.

Handles game creation, round initialization, and game flow.
Does not directly handle HTTP concerns or database access (delegates to repositories).
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.repositories.game_repository import GameRepository
from app.repositories.skill_repository import SkillRepository
from app.repositories.question_repository import NewsRepository
from app.adaptation.question_selector import QuestionSelector
from app.models import Game, GameRound, Question, News


class GameService:
    """Service for game-related business logic."""

    @staticmethod
    def create_game_with_first_round(db: Session, user_id: str) -> dict:
        """
        Create a new game and initialize the first round.

        This ensures that when a game starts, it already has its first question.

        Args:
            db: Database session
            user_id: ID of the user starting the game

        Returns:
            Dictionary with game_id, round details, and first question

        Raises:
            ValueError: If no questions/news available or user not found
        """
        # Initialize user skill states for all four skills if not already done
        GameService._ensure_user_skills_initialized(db, user_id)

        # Create the game
        game = GameRepository.create_game(db, user_id)

        # Select first question
        question_news = QuestionSelector.select_next_question(db, user_id, game.id)

        if not question_news:
            # Clean up the created game if we can't get a question
            raise ValueError("No questions available to start game")

        question, news = question_news

        # Create first round
        game_round = GameRepository.create_game_round(
            db,
            game.id,
            news.id,
            round_number=1,
        )

        return GameService._round_payload(game.id, game_round, question, news)

    @staticmethod
    def get_next_question(db: Session, user_id: str, game_id: str) -> dict | None:
        """
        Get the next question for a game.

        Args:
            db: Database session
            user_id: ID of the user
            game_id: ID of the game

        Returns:
            Dictionary with round and question details, or None if game is finished

        Raises:
            ValueError: If game not found or user doesn't own the game
        """
        game = GameRepository.get_game_by_id(db, game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")

        if game.user_id != user_id:
            raise ValueError("User does not own this game")

        from app.models import GameStatusEnum
        if game.status == GameStatusEnum.FINISHED:
            return None

        # Get last round number
        game_rounds = GameRepository.get_game_rounds(db, game_id)
        last_round = max((r.round_number for r in game_rounds), default=0)

        # Check if we should continue or finish game
        if last_round >= 10:  # MVP: games have 10 rounds max
            game = GameRepository.finish_game(db, game_id)
            return None

        # Select next question
        question_news = QuestionSelector.select_next_question(db, user_id, game_id)

        if not question_news:
            # No more questions - finish game
            game = GameRepository.finish_game(db, game_id)
            return None

        question, news = question_news

        # Create next round
        game_round = GameRepository.create_game_round(
            db,
            game_id,
            news.id,
            round_number=last_round + 1,
        )

        return GameService._round_payload(game_id, game_round, question, news)

    @staticmethod
    def _round_payload(game_id: str, game_round: GameRound, question: Question, news: News) -> dict:
        """Build the round payload shared by game creation and next question."""
        return {
            "game_id": game_id,
            "round": {
                "id": game_round.id,
                "number": game_round.round_number,
                "news_id": news.id,
                "question_id": question.id,
            },
            "news": {
                "id": news.id,
                "title": news.title,
                "content": news.content,
                "image_url": news.image_url,
                "verdict": news.verdict,
            },
            "question": {
                "id": question.id,
                "text": question.text,
                "difficulty": question.difficulty,
                "options": question.options,
                "skill_id": question.skill_id,
                "skill_code": question.skill.code,
            },
        }

    @staticmethod
    def _ensure_user_skills_initialized(db: Session, user_id: str) -> None:
        """
        Ensure that user has skill states for all four skills.

        If not, create them with initial mastery probability.

        Args:
            db: Database session
            user_id: ID of the user
        """
        all_skills = SkillRepository.get_all_skills(db)

        for skill in all_skills:
            SkillRepository.get_or_create_user_skill_state(
                db,
                user_id,
                skill.id,
                initial_mastery=0.3,
            )
