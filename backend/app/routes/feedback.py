from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Feedback, Verification
from app.schemas import FeedbackCreate, FeedbackResponse


router = APIRouter(prefix="/api/verifications", tags=["feedback"])


@router.post("/{verification_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(verification_id: UUID, payload: FeedbackCreate, database: Session = Depends(get_db)):
    verification = database.get(Verification, str(verification_id))
    if verification is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    feedback = Feedback(verification_id=verification.id, answers=payload.answers)
    database.add(feedback)
    database.commit()
    database.refresh(feedback)
    return feedback