"""
Game Routes - HTTP endpoints for game operations.

Endpoints for starting games, getting rounds, and retrieving game status.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services.game import GameService
from app.repositories.game_repository import GameRepository
from app.schemas import GameCreateResponse, GameStatusResponse, GameRoundResponse

router = APIRouter(prefix="/api/games", tags=["games"])


def get_current_user(db: Session = Depends(get_db)) -> User:
    """
    Get the current authenticated user.
    
    TODO: Implement proper authentication/authorization
    For now, this is a placeholder that returns None.
    The endpoints should include Authorization header handling.
    """
    # Placeholder - will be implemented with proper auth
    return None


@router.post("", response_model=GameCreateResponse, status_code=status.HTTP_201_CREATED)
def create_game(db: Session = Depends(get_db)):
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
        # TODO: Get actual user from auth token
        user_id = "test-user"  # Placeholder
        
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
def get_game_status(game_id: str, db: Session = Depends(get_db)):
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
def get_next_question(game_id: str, db: Session = Depends(get_db)):
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
        # TODO: Get actual user from auth token
        user_id = "test-user"  # Placeholder
        
        result = GameService.get_next_question(db, user_id, game_id)
        return result
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting next question: {str(error)}",
        )
