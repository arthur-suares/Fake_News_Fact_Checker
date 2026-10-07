"""
Game Repository - Database access layer for game-related entities.

Handles Game and GameRound operations.
"""

from sqlalchemy.orm import Session
from app.models import Game, GameRound, GameStatusEnum


class GameRepository:
    """Repository for game-related database operations."""

    @staticmethod
    def create_game(db: Session, user_id: str) -> Game:
        """
        Create a new game for a user.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            Created Game instance
        """
        game = Game(user_id=user_id, status=GameStatusEnum.IN_PROGRESS)
        db.add(game)
        db.commit()
        db.refresh(game)
        return game

    @staticmethod
    def get_game_by_id(db: Session, game_id: str) -> Game | None:
        """
        Retrieve a game by ID.

        Args:
            db: Database session
            game_id: ID of the game

        Returns:
            Game instance or None if not found
        """
        return db.query(Game).filter(Game.id == game_id).first()

    @staticmethod
    def get_user_games(db: Session, user_id: str, limit: int = 10) -> list[Game]:
        """
        Get recent games for a user.

        Args:
            db: Database session
            user_id: ID of the user
            limit: Maximum number of games to retrieve

        Returns:
            List of Game instances
        """
        return (
            db.query(Game)
            .filter(Game.user_id == user_id)
            .order_by(Game.started_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def create_game_round(
        db: Session,
        game_id: str,
        news_id: str,
        round_number: int,
    ) -> GameRound:
        """
        Create a new game round.

        Args:
            db: Database session
            game_id: ID of the parent game
            news_id: ID of the news for this round
            round_number: Sequential round number

        Returns:
            Created GameRound instance
        """
        game_round = GameRound(
            game_id=game_id,
            news_id=news_id,
            round_number=round_number,
        )
        db.add(game_round)
        db.commit()
        db.refresh(game_round)
        return game_round

    @staticmethod
    def get_game_round_by_id(db: Session, round_id: str) -> GameRound | None:
        """
        Retrieve a game round by ID.

        Args:
            db: Database session
            round_id: ID of the round

        Returns:
            GameRound instance or None if not found
        """
        return db.query(GameRound).filter(GameRound.id == round_id).first()

    @staticmethod
    def get_game_rounds(db: Session, game_id: str) -> list[GameRound]:
        """
        Get all rounds for a game.

        Args:
            db: Database session
            game_id: ID of the game

        Returns:
            List of GameRound instances ordered by round number
        """
        return (
            db.query(GameRound)
            .filter(GameRound.game_id == game_id)
            .order_by(GameRound.round_number)
            .all()
        )

    @staticmethod
    def finish_game(db: Session, game_id: str) -> Game:
        """
        Mark a game as finished.

        Args:
            db: Database session
            game_id: ID of the game to finish

        Returns:
            Updated Game instance

        Raises:
            ValueError: If game not found
        """
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise ValueError(f"Game {game_id} not found")

        from datetime import datetime
        game.status = GameStatusEnum.FINISHED
        game.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(game)
        return game
