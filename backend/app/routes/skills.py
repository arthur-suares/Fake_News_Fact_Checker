"""
Skills Routes - HTTP endpoints for skill-related operations.

Endpoints for getting user skill profile and answer submission.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.answer import AnswerService
from app.schemas import AnswerCreate, AnswerResponse, UserSkillProfileResponse

router = APIRouter(prefix="/api", tags=["skills"])


@router.get("/users/me/skills", response_model=UserSkillProfileResponse)
def get_user_skills(db: Session = Depends(get_db)):
    """
    Get the current user's skill profile.

    Returns mastery probabilities for all four skills (SOURCE, EVIDENCE, CONTEXT, VISUAL).

    Response:
        {
            "skills": [
                {
                    "skill_id": "...",
                    "skill_code": "SOURCE",
                    "mastery_probability": 0.72,
                    "updated_at": "2024-01-01T12:00:00"
                },
                ...
            ]
        }
    """
    try:
        # TODO: Get actual user from auth token
        user_id = "test-user"  # Placeholder
        
        profile = AnswerService.get_user_skill_profile(db, user_id)
        
        return {
            "skills": [
                {
                    "skill_id": s["skill_id"],
                    "skill_code": s["skill_code"],
                    "mastery_probability": s["mastery_probability"],
                    "updated_at": s["updated_at"],
                }
                for s in profile["skills"]
            ]
        }
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching skills: {str(error)}",
        )


@router.post("/games/{game_id}/answers", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
def submit_answer(
    game_id: str,
    answer: AnswerCreate,
    db: Session = Depends(get_db),
):
    """
    Submit an answer to a question.

    This endpoint:
    1. Validates the answer
    2. Stores it in the database
    3. Updates user's skill mastery using BKT
    4. Returns feedback including correctness and new mastery level

    Request:
        {
            "question_id": "...",
            "game_round_id": "...",
            "selected_option": "A",
            "confidence": 4,
            "response_time": 5320
        }

    Response:
        {
            "id": "...",
            "correct": true,
            "skill_code": "SOURCE",
            "mastery_probability": 0.57,
            "previous_mastery_probability": 0.30,
            "correct_option": "A",
            "explanation": "..."
        }
    """
    try:
        # TODO: Get actual user from auth token
        user_id = "test-user"  # Placeholder
        
        result = AnswerService.process_answer(
            db,
            user_id,
            answer.game_round_id,
            answer.question_id,
            answer.selected_option,
            answer.confidence,
            answer.response_time,
        )

        return {
            "id": result["answer_id"],
            "correct": result["correct"],
            "skill_code": result["skill_code"],
            "mastery_probability": result["new_mastery"],
            "previous_mastery_probability": result["old_mastery"],
            "correct_option": result["correct_option"],
            "explanation": result["explanation"],
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting answer: {str(error)}",
        )
