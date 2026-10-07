from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# LEGACY SCHEMAS (Verification, Feedback, Profile)
# ============================================================================

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


class ProfileResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assigned_cluster: int
    cluster_label: str
    probabilities: dict[str, float]
    details: dict[str, Any] | None = None
    processed_at: datetime


class ProfileResponse(BaseModel):
    verification_id: str
    profile_result: ProfileResult

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str
    phone: str
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: str
    password: str


# ============================================================================
# NEW SCHEMAS (Game, Skills, Knowledge Tracing)
# ============================================================================

class SkillResponse(BaseModel):
    """Response schema for a skill."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    description: str | None = None


class UserSkillStateResponse(BaseModel):
    """Response schema for user's skill state."""
    model_config = ConfigDict(from_attributes=True)

    skill_id: str
    skill_code: str
    mastery_probability: float
    updated_at: datetime


class UserSkillProfileResponse(BaseModel):
    """User's complete skill profile."""
    skills: list[UserSkillStateResponse]


class NewsResponse(BaseModel):
    """Response schema for news."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    image_url: str | None = None
    verdict: str | None = None
    created_at: datetime


class QuestionOptionResponse(BaseModel):
    """Response schema for question with options."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    text: str
    difficulty: float
    options: dict[str, str]
    skill_id: str
    explanation: str | None = None


class AnswerCreate(BaseModel):
    """Request schema for submitting an answer."""
    question_id: str
    game_round_id: str
    selected_option: str = Field(min_length=1, max_length=10)
    confidence: int | None = Field(None, ge=1, le=5)
    response_time: int | None = Field(None, ge=0)


class AnswerResponse(BaseModel):
    """Response schema after answer submission."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    correct: bool
    skill_code: str
    mastery_probability: float
    explanation: str | None = None


class GameRoundResponse(BaseModel):
    """Response schema for a game round."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    round_number: int
    news: NewsResponse
    questions: list[QuestionOptionResponse]
    started_at: datetime
    finished_at: datetime | None = None


class GameCreateResponse(BaseModel):
    """Response when creating a new game."""
    game_id: str
    round: GameRoundResponse


class GameStatusResponse(BaseModel):
    """Response with game status."""
    model_config = ConfigDict(from_attributes=True)

    game_id: str
    status: str
    round_number: int | None = None
    finished_at: datetime | None = None
