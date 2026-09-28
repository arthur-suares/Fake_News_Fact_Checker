from pathlib import Path

from schemas import ImageAnalysis
from vision_client import request_image_analysis


def analyze_image(
    image: bytes | str | Path,
    text: str | None = None,
    media_type: str | None = None,
) -> dict:
    """Analyze an image, optionally comparing its visible content with a claim."""
    result = ImageAnalysis.model_validate(request_image_analysis(image, text, media_type))
    if text and not result.analysis:
        raise ValueError("The vision model must return an analysis when text is provided")
    return result.model_dump()