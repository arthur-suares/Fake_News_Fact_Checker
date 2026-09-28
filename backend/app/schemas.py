from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VerificationCreate(BaseModel):
    text: str = Field(min_length=1)


class VerificationAccepted(BaseModel):
    id: str
    status: str


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source: str
    rating: str | None
    url: str | None


class VerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    verdict: str | None
    evidence: list[EvidenceResponse]
    created_at: datetime


class FeedbackCreate(BaseModel):
    answers: dict[str, Any]


class FeedbackResponse(BaseModel):
    id: str
    verification_id: str