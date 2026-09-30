from typing import Any

import requests

from app.config import settings


GOOGLE_FACT_CHECK_URL = (
    "https://factchecktools.googleapis.com/v1alpha1/claims:search"
)


class GoogleFactCheckService:

    @staticmethod
    def search_claims(
        query: str,
        language_code: str = "pt-BR",
        max_age_days: int | None = None,
        page_size: int = 10,
        page_token: str | None = None,
    ):
        params = {
            "key": settings.google_fact_check_api_key,
            "query": query,
            "languageCode": language_code,
            "pageSize": page_size,
        }

        if max_age_days is not None:
            params["maxAgeDays"] = max_age_days

        if page_token:
            params["pageToken"] = page_token

        response = requests.get(
            GOOGLE_FACT_CHECK_URL,
            params=params,
            timeout=15,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Google Fact Check API error: "
                f"{response.status_code} - {response.text}"
            )

        return response.json()


def map_claim_reviews(result: dict[str, Any]) -> list[dict[str, Any]]:
    reviews = []
    for claim in result.get("claims", []):
        publisher_claim = claim.get("text")
        claimant = claim.get("claimant")
        for review in claim.get("claimReview", []):
            publisher = review.get("publisher") or {}
            reviews.append(
                {
                    "claim": publisher_claim,
                    "claimant": claimant,
                    "publisher": publisher.get("name", "Unknown"),
                    "publisher_site": publisher.get("site"),
                    "title": review.get("title"),
                    "rating": review.get("textualRating"),
                    "url": review.get("url"),
                    "review_date": review.get("reviewDate"),
                    "language_code": review.get("languageCode"),
                }
            )
    return reviews


def search_fact_check_reviews(
    query: str,
    language_code: str = "pt-BR",
    max_age_days: int | None = None,
    page_size: int = 10,
    page_token: str | None = None,
) -> dict[str, Any]:
    result = GoogleFactCheckService.search_claims(
        query=query,
        language_code=language_code,
        max_age_days=max_age_days,
        page_size=page_size,
        page_token=page_token,
    )
    reviews = map_claim_reviews(result)
    return {
        "query": query,
        "status": "reviews_found" if reviews else "no_reviews_found",
        "review_count": len(reviews),
        "reviews": reviews,
        "next_page_token": result.get("nextPageToken"),
        "note": "No matching review does not establish that a claim is true.",
    }
