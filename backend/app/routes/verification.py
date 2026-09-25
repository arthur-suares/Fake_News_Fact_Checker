from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models import Evidence, Verification
from app.schemas import VerificationAccepted, VerificationCreate, VerificationResponse
from app.services.verification import search_and_map_claims, verdict_from_evidence


router = APIRouter(prefix="/api/verifications", tags=["verifications"])


def process_verification(verification_id: str) -> None:
    database = SessionLocal()
    try:
        verification = database.get(Verification, verification_id)
        if verification is None:
            return
        result, evidence = search_and_map_claims(verification.text)
        verification.fact_check_result = result
        verification.verdict = verdict_from_evidence(evidence)
        verification.status = "completed"
        verification.evidence = [Evidence(**item) for item in evidence]
        database.commit()
    except Exception:
        database.rollback()
        verification = database.get(Verification, verification_id)
        if verification:
            verification.status = "failed"
            database.commit()
    finally:
        database.close()


@router.post("", response_model=VerificationAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_verification(
    request: Request,
    background_tasks: BackgroundTasks,
    text: str | None = Form(None),
    image: UploadFile | None = File(None),
    database: Session = Depends(get_db),
):
    if request.headers.get("content-type", "").startswith("application/json"):
        payload = VerificationCreate.model_validate(await request.json())
        text = payload.text
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="text is required")

    image_path = None
    if image:
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        image_path = str(upload_dir / Path(image.filename).name)
        Path(image_path).write_bytes(await image.read())

    verification = Verification(text=text.strip(), image_path=image_path)
    database.add(verification)
    database.commit()
    database.refresh(verification)
    background_tasks.add_task(process_verification, verification.id)
    return {"id": verification.id, "status": verification.status}


@router.get("/{verification_id}", response_model=VerificationResponse)
def get_verification(verification_id: UUID, database: Session = Depends(get_db)):
    verification = database.get(Verification, str(verification_id))
    if verification is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    return verification