"""
Game Routes - HTTP endpoints for game operations.

Endpoints for starting games, getting rounds, and retrieving game status.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.game_repository import GameRepository
from app.schemas import (
    GameCreateResponse,
    GameRoundResponse,
    GameStatusResponse,
)
from app.services.game import GameService

router = APIRouter(prefix="/api/games", tags=["games"])


@router.post(
    "",
    response_model=GameCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_game(db: Session = Depends(get_db)):
    """Create a game session and return its first question."""
    try:
        # TODO: Replace the placeholder with the authenticated user ID.
        user_id = "test-user"

        return GameService.create_game_with_first_round(db, user_id)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating game: {str(error)}",
        ) from error


@router.get("/{game_id}", response_model=GameStatusResponse)
def get_game_status(
    game_id: str,
    db: Session = Depends(get_db),
):
    """Return the status and current round of a game."""
    game = GameRepository.get_game_by_id(db, game_id)

    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found",
        )

    rounds = GameRepository.get_game_rounds(db, game_id)
    current_round = max(
        (round_.round_number for round_ in rounds),
        default=0,
    )

    return {
        "game_id": game.id,
        "status": game.status.value,
        "round_number": current_round,
        "finished_at": game.finished_at,
    }


@router.get("/{game_id}/next", response_model=GameRoundResponse | None)
def get_next_question(
    game_id: str,
    db: Session = Depends(get_db),
):
    """Return the next question or None if the game is finished."""
    try:
        # TODO: Replace the placeholder with the authenticated user ID.
        user_id = "test-user"

        return GameService.get_next_question(db, user_id, game_id)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting next question: {str(error)}",
        ) from error
