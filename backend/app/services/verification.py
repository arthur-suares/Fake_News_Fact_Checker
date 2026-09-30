from typing import Any

from app.services.google_fact_check import GoogleFactCheckService, map_claim_reviews


def search_and_map_claims(text: str) -> tuple[dict[str, Any], list[dict[str, str | None]]]:
    result = GoogleFactCheckService.search_claims(query=text)
    evidence = [
        {"source": review["publisher"], "rating": review["rating"], "url": review["url"]}
        for review in map_claim_reviews(result)
    ]
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