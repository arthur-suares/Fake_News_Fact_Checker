from typing import Any

import httpx

from app.config import settings


GOOGLE_FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


def search_and_map_claims(text: str) -> tuple[dict[str, Any], list[dict[str, str | None]]]:
    response = httpx.get(
        GOOGLE_FACT_CHECK_URL,
        params={"key": settings.google_fact_check_api_key, "query": text, "languageCode": "pt-BR", "pageSize": 10},
        timeout=15,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Google Fact Check API error: {response.status_code} - {response.text}")

    result = response.json()
    evidence = []
    for claim in result.get("claims", []):
        for review in claim.get("claimReview", []):
            publisher = review.get("publisher", {})
            evidence.append({
                "source": publisher.get("name", "Unknown"),
                "rating": review.get("textualRating"),
                "url": review.get("url"),
            })
    return result, evidence


def verdict_from_evidence(evidence: list[dict[str, str | None]]) -> str | None:
    if not evidence:
        return None
    rating = (evidence[0].get("rating") or "").lower()
    if any(word in rating for word in ("false", "falso", "fake")):
        return "false"
    if any(word in rating for word in ("true", "verdadeiro")):
        return "true"
    return rating or None