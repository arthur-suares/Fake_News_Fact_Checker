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
