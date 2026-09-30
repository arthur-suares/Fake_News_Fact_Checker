from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VerificationCreate(BaseModel):
    text: str = Field(min_length=1)


class FactCheckSearch(BaseModel):
    query: str = Field(min_length=3)
    language_code: str = Field(default="pt-BR", min_length=2)
    max_age_days: int | None = Field(default=None, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    page_token: str | None = None


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