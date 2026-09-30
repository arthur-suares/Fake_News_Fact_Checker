import base64
import binascii
import sys
from collections import Counter
from pathlib import Path

from mcp.server.fastmcp import FastMCP

BACKEND_DIRECTORY = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.services.google_fact_check import search_fact_check_reviews
from service import analyze_image as analyze_image_service


MAX_IMAGE_BYTES = 10 * 1024 * 1024
mcp = FastMCP("image-analysis")


def _decode_image(image_base64: str) -> bytes:
    try:
        image = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("image_base64 must contain valid Base64 data") from error
    if len(image) > MAX_IMAGE_BYTES:
        raise ValueError("The image must not exceed 10 MiB")
    return image


@mcp.tool()
def analyze_image(image_base64: str, mime_type: str, text: str | None = None) -> dict:
    """Describe an image and optionally compare its visible content with a claim.

    Send the image bytes encoded as Base64 and its MIME type, such as image/jpeg
    or image/png. The analysis does not establish whether a claim is true.
    """
    return analyze_image_service(_decode_image(image_base64), text=text, media_type=mime_type)


@mcp.tool()
def analyze_image_file(
    image_path: str,
    text: str | None = None,
) -> dict:
    """Analyze an image from a local file."""

    path = Path(image_path).expanduser().resolve()

    if not path.is_file():
        raise ValueError(f"Image file not found: {path}")

    image = path.read_bytes()

    if len(image) > MAX_IMAGE_BYTES:
        raise ValueError("The image must not exceed 10 MiB")

    return analyze_image_service(
        image,
        text=text,
        media_type="image/jpeg",
    )

@mcp.tool()
def search_fact_checks(
    query: str,
    language_code: str = "pt-BR",
    max_age_days: int | None = None,
    page_size: int = 10,
    page_token: str | None = None,
) -> dict:
    """Search published third-party fact-check reviews for a claim or topic."""
    if len(query.strip()) < 3:
        raise ValueError("query must contain at least 3 characters")
    if not 1 <= page_size <= 100:
        raise ValueError("page_size must be between 1 and 100")
    if max_age_days is not None and max_age_days < 1:
        raise ValueError("max_age_days must be positive")
    return search_fact_check_reviews(
        query=query.strip(),
        language_code=language_code,
        max_age_days=max_age_days,
        page_size=page_size,
        page_token=page_token,
    )


@mcp.tool()
def summarize_fact_checks(
    query: str,
    language_code: str = "pt-BR",
    max_age_days: int | None = None,
    page_size: int = 10,
) -> dict:
    """Summarize matching review ratings and publishers without asserting truth."""
    result = search_fact_checks(
        query=query,
        language_code=language_code,
        max_age_days=max_age_days,
        page_size=page_size,
    )
    ratings = Counter(review["rating"] or "Sem classificação" for review in result["reviews"])
    publishers = sorted({review["publisher"] for review in result["reviews"]})
    return {
        "query": result["query"],
        "status": result["status"],
        "review_count": result["review_count"],
        "rating_counts": dict(ratings),
        "publishers": publishers,
        "next_page_token": result["next_page_token"],
        "note": result["note"],
    }


@mcp.tool()
def compare_claim_with_image(
    claim: str,
    image_base64: str,
    mime_type: str,
    language_code: str = "pt-BR",
    max_age_days: int | None = None,
    page_size: int = 10,
) -> dict:
    """Combine Google fact-check reviews with a visual comparison of an image."""
    if len(claim.strip()) < 3:
        raise ValueError("claim must contain at least 3 characters")
    fact_checks = search_fact_checks(
        query=claim,
        language_code=language_code,
        max_age_days=max_age_days,
        page_size=page_size,
    )
    visual_analysis = analyze_image_service(
        _decode_image(image_base64),
        text=claim.strip(),
        media_type=mime_type,
    )
    return {
        "claim": claim.strip(),
        "fact_checks": fact_checks,
        "visual_analysis": visual_analysis,
        "note": "Visual compatibility and third-party reviews are evidence to inspect, not proof by themselves.",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")