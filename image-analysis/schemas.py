from pydantic import BaseModel, Field


class ImageAnalysis(BaseModel):
    description: str = Field(min_length=1)
    possible_manipulation: bool
    confidence: float = Field(ge=0, le=1)
    analysis: str | None = None