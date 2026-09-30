import re
from typing import Any

import httpx

from app.config import settings


GOOGLE_FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

MAX_QUERY_WORDS = 12
MAX_KEYWORDS = 6

STOPWORDS = {
    "a", "ao", "aos", "as", "até", "com", "como", "da", "das", "de", "do", "dos", "e", "é", "ela", "elas",
    "ele", "eles", "em", "entre", "era", "essa", "esse", "esta", "está", "este", "eu", "foi", "foram", "há",
    "isso", "isto", "já", "lhe", "mais", "mas", "me", "mesmo", "muito", "na", "nas", "não", "no", "nos",
    "num", "numa", "o", "os", "ou", "para", "pela", "pelas", "pelo", "pelos", "por", "qual", "quando",
    "que", "quem", "se", "sem", "ser", "seu", "seus", "só", "sua", "suas", "também", "tem", "têm", "um",
    "uma", "umas", "uns", "vai", "você", "afirma", "afirmam", "diz", "dizem", "segundo", "mensagem",
    "circula", "notícia", "post", "publicação", "vídeo", "whatsapp", "redes", "sociais",
}


def _search(query: str) -> dict[str, Any]:
    response = httpx.get(
        GOOGLE_FACT_CHECK_URL,
        params={"key": settings.google_fact_check_api_key, "query": query, "languageCode": "pt-BR", "pageSize": 10},
        timeout=15,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Google Fact Check API error: {response.status_code} - {response.text}")
    return response.json()


def build_queries(text: str) -> list[str]:
    """A API busca afirmações curtas: para notícias longas, tenta versões mais enxutas do texto."""
    text = " ".join(text.split())
    queries = [text]

    first_sentence = re.split(r"(?<=[.!?])\s+", text)[0]
    queries.append(" ".join(first_sentence.split()[:MAX_QUERY_WORDS]))

    words = re.findall(r"\w+", text.lower())
    keywords = list(dict.fromkeys(w for w in words if len(w) > 2 and w not in STOPWORDS))
    queries.append(" ".join(keywords[:MAX_KEYWORDS]))

    return [q for q in dict.fromkeys(queries) if len(q) >= 3]


def search_and_map_claims(text: str) -> tuple[dict[str, Any], list[dict[str, str | None]]]:
    result: dict[str, Any] = {}
    for query in build_queries(text):
        result = _search(query)
        if result.get("claims"):
            break

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
