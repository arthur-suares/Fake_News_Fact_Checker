import requests
from typing import Any

from app.config import settings


GOOGLE_FACT_CHECK_URL = (
    "https://factchecktools.googleapis.com/v1alpha1/claims:search"
)


def _mock_response(query: str, language_code: str, page_size: int) -> dict[str, Any]:
    # Minimal mock response so the API works without a Google API key.
    return {
        "claims": [
            {
                "text": f"Mocked search results for: {query}",
                "claimant": "mocked source",
                "claimReview": [
                    {
                        "publisher": {"name": "Mock Publisher", "site": "mock.local"},
                        "title": "Resposta mock",
                        "textualRating": "Não verificado (mock)",
                        "languageCode": language_code,
                    }
                ],
            }
            for _ in range(min(1, page_size))
        ]
    }


class GoogleFactCheckService:

    @staticmethod
    def search_claims(
        query: str,
        language_code: str = "pt-BR",
        max_age_days: int | None = None,
        page_size: int = 10,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        key = (settings.google_fact_check_api_key or "").strip()

        # If no API key is configured (or it's the placeholder), return a mock response
        if not key or key.lower().startswith("replace") or "your" in key.lower():
            return _mock_response(query=query, language_code=language_code, page_size=page_size)

        params = {
            "key": key,
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
