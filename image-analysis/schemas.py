from pydantic import BaseModel, Field


class ImageAnalysis(BaseModel):
    description: str = Field(min_length=1)
    visible_text: list[str] = Field(default_factory=list)
    possible_manipulation: bool
    confidence: float = Field(ge=0, le=1)
    analysis: str | None = None