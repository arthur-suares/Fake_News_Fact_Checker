from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Feedback, Verification
from app.schemas import FeedbackCreate, FeedbackResponse
from app.services.profile import assign_profile_after_feedback
from app.security import get_current_user


router = APIRouter(prefix="/api/verifications", tags=["feedback"])


@router.post("/{verification_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(verification_id: UUID, payload: FeedbackCreate, database: Session = Depends(get_db), current_user = Depends(get_current_user)):
    verification = database.query(Verification).filter(
    Verification.id == str(verification_id),
    Verification.user_id == current_user.id
).first()
    if verification is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    feedback = Feedback(verification_id=verification.id, answers=payload.answers)
    database.add(feedback)
    database.commit()
    database.refresh(feedback)
    # Hook síncrono: calcula o perfil assim que o questionário é salvo
    assign_profile_after_feedback(database, verification.id)
    return feedback