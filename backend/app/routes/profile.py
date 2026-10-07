from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.perfil import RespostasInvalidas
from app.models import Verification
from app.schemas import ProfileResponse
from app.services.profile import assign_profile, profile_response
from app.security import get_current_user


router = APIRouter(prefix="/api/verifications", tags=["profile"])


def get_verification_or_404(
    database: Session,
    verification_id: UUID,
    user_id: str
) -> Verification:

    verification = database.query(Verification).filter(
        Verification.id == str(verification_id),
        Verification.user_id == user_id
    ).first()

    if verification is None:
        raise HTTPException(status_code=404, detail="Verification not found")

    return verification


@router.get("/{verification_id}/profile", response_model=ProfileResponse)
def get_profile(verification_id: UUID, database: Session = Depends(get_db), current_user = Depends(get_current_user)):
    verification = get_verification_or_404(database, verification_id, current_user.id)
    if verification.profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile_response(verification.profile)


@router.post("/{verification_id}/profile", response_model=ProfileResponse)
def compute_profile(verification_id: UUID, database: Session = Depends(get_db), current_user = Depends(get_current_user)):
    verification = get_verification_or_404(database, verification_id, current_user.id)
    try:
        profile = assign_profile(database, verification.id)
    except RespostasInvalidas as error:
        raise HTTPException(status_code=422, detail=str(error))
    return profile_response(profile)
