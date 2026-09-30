from typing import Any
import logging
import httpx

from app.config import settings
from app.services.vector_service import VectorFactCheckService

logger = logging.getLogger(__name__)

GOOGLE_FACT_CHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


def search_and_map_claims(text: str) -> tuple[dict[str, Any], list[dict[str, str | None]]]:
    """
    Busca verificações de fatos híbrida:
    1. Consulta o banco vetorial de checagens curadas (Lupa, Aos Fatos, Boatos.org, etc.).
    2. Consulta a Google Fact Check Tools API (se configurada e funcional).
    3. Combina as evidências encontradas.
    """
    evidence: list[dict[str, str | None]] = []
    google_result: dict[str, Any] = {"claims": []}

    # 1. Consulta no Banco Vetorial
    try:
        _, vector_evidences = VectorFactCheckService.verify_claim(
            query=text,
            top_k=5,
            min_confidence=0.55,
        )
        for v_ev in vector_evidences:
            evidence.append({
                "source": v_ev.get("source", "Banco Vetorial"),
                "rating": v_ev.get("rating"),
                "url": v_ev.get("url"),
            })
    except Exception as exc:
        logger.warning("Falha na consulta ao banco vetorial: %s", exc)

    # 2. Consulta à Google Fact Check Tools API
    api_key = (settings.google_fact_check_api_key or "").strip()
    is_valid_key = bool(api_key and not api_key.lower().startswith("replace") and "your" not in api_key.lower())

    if is_valid_key:
        try:
            response = httpx.get(
                GOOGLE_FACT_CHECK_URL,
                params={"key": api_key, "query": text, "languageCode": "pt-BR", "pageSize": 10},
                timeout=15,
            )
            if response.status_code == 200:
                google_result = response.json()
                for claim in google_result.get("claims", []):
                    for review in claim.get("claimReview", []):
                        publisher = review.get("publisher", {})
                        evidence.append({
                            "source": publisher.get("name", "Unknown"),
                            "rating": review.get("textualRating"),
                            "url": review.get("url"),
                        })
            else:
                logger.warning("Google Fact Check API retornou status %s", response.status_code)
        except Exception as exc:
            logger.warning("Erro ao consultar Google Fact Check API: %s", exc)
    else:
        # Se nenhuma chave Google configurada e não houver evidências vetoriais, mock amigável
        if not evidence:
            google_result = {
                "claims": [
                    {
                        "text": f"Busca local/mock para: {text}",
                        "claimReview": [
                            {
                                "publisher": {"name": "Sistema Local"},
                                "title": "Verificação local",
                                "textualRating": "Não verificado no Google",
                            }
                        ],
                    }
                ]
            }

    result = {
        "google_fact_check": google_result,
        "vector_evidences_count": len([e for e in evidence if "Banco Vetorial" in (e.get("source") or "")]),
        "total_evidences": len(evidence),
    }

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