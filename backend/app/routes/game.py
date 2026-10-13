"""
Game Routes - HTTP endpoints for game operations.

Endpoints for starting games, getting rounds, and retrieving game status.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_id
from app.services.game import (
    GameConflictError,
    GameForbiddenError,
    GameNotFoundError,
    GameService,
)
from app.repositories.game_repository import GameRepository
from app.schemas import GameCreateResponse, GameStatusResponse, GameRoundResponse

router = APIRouter(prefix="/api/games", tags=["games"])


@router.post("", response_model=GameCreateResponse, status_code=status.HTTP_201_CREATED)
def create_game(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Create a new game session for the current user.

    Returns the game ID and the first round with its question.

    Response:
        {
            "game_id": "...",
            "round": {
                "id": "...",
                "number": 1,
                "news_id": "...",
                "question_id": "..."
            },
            "news": {...},
            "question": {...}
        }
    """
    try:
        result = GameService.create_game_with_first_round(db, user_id)
        return result
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating game: {str(error)}",
        )


@router.get("/{game_id}", response_model=GameStatusResponse)
def get_game_status(
    game_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get the status of a game.

    Args:
        game_id: ID of the game

    Returns:
        Game status and current round number
    """
    game = GameRepository.get_game_by_id(db, game_id)
    
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found",
        )
    if game.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not own this game",
        )

    # Get current round number
    rounds = GameRepository.get_game_rounds(db, game_id)
    current_round = max((r.round_number for r in rounds), default=0) if rounds else 0

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
    user_id: str = Depends(get_current_user_id),
):
    """
    Get the next question for a game.

    Returns the next round with question details.
    Returns None if game is finished.

    Args:
        game_id: ID of the game

    Raises:
        HTTPException: If game not found
    """
    try:
        result = GameService.get_next_question(db, user_id, game_id)
        return result
    except ValueError as error:
        if isinstance(error, GameConflictError):
            status_code = status.HTTP_409_CONFLICT
        elif isinstance(error, GameForbiddenError):
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting next question: {str(error)}",
        )
