from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.perfil import RespostasInvalidas
from app.models import Verification
from app.schemas import ProfileResponse
from app.services.profile import assign_profile, profile_response


router = APIRouter(prefix="/api/verifications", tags=["profile"])


def get_verification_or_404(database: Session, verification_id: UUID) -> Verification:
    verification = database.get(Verification, str(verification_id))
    if verification is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    return verification


@router.get("/{verification_id}/profile", response_model=ProfileResponse)
def get_profile(verification_id: UUID, database: Session = Depends(get_db)):
    verification = get_verification_or_404(database, verification_id)
    if verification.profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile_response(verification.profile)


@router.post("/{verification_id}/profile", response_model=ProfileResponse)
def compute_profile(verification_id: UUID, database: Session = Depends(get_db)):
    verification = get_verification_or_404(database, verification_id)
    try:
        profile = assign_profile(database, verification.id)
    except RespostasInvalidas as error:
        raise HTTPException(status_code=422, detail=str(error))
    return profile_response(profile)
