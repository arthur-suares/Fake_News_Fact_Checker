import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import server


def _fact_check_result():
    return {
        "query": "Vacina causa autismo",
        "status": "reviews_found",
        "review_count": 2,
        "reviews": [
            {"publisher": "Agência A", "rating": "Falso", "url": "https://a.test"},
            {"publisher": "Agência B", "rating": "Inconclusivo", "url": "https://b.test"},
        ],
        "next_page_token": "next-page",
        "note": "No matching review does not establish that a claim is true.",
    }


def test_search_fact_checks_forwards_query_options(monkeypatch):
    captured = {}

    def fake_search(**kwargs):
        captured.update(kwargs)
        return _fact_check_result()

    monkeypatch.setattr(server, "search_fact_check_reviews", fake_search)

    result = server.search_fact_checks(
        "Vacina causa autismo",
        language_code="pt-BR",
        max_age_days=45,
        page_size=7,
        page_token="cursor",
    )

    assert result["review_count"] == 2
    assert captured == {
        "query": "Vacina causa autismo",
        "language_code": "pt-BR",
        "max_age_days": 45,
        "page_size": 7,
        "page_token": "cursor",
    }


def test_summarize_fact_checks_counts_ratings_without_verdict(monkeypatch):
    monkeypatch.setattr(server, "search_fact_check_reviews", lambda **_kwargs: _fact_check_result())

    result = server.summarize_fact_checks("Vacina causa autismo")

    assert result["rating_counts"] == {"Falso": 1, "Inconclusivo": 1}
    assert result["publishers"] == ["Agência A", "Agência B"]
    assert "verdict" not in result
    assert result["next_page_token"] == "next-page"


def test_compare_claim_with_image_combines_fact_check_and_visual_analysis(monkeypatch):
    monkeypatch.setattr(server, "search_fact_check_reviews", lambda **_kwargs: _fact_check_result())
    captured = {}

    def fake_analyze(image, text, media_type):
        captured.update(image=image, text=text, media_type=media_type)
        return {"description": "Pessoa recebendo vacina.", "confidence": 0.8}

    monkeypatch.setattr(server, "analyze_image_service", fake_analyze)

    result = server.compare_claim_with_image(
        "Vacina causa autismo",
        "aW1hZ2U=",
        "image/png",
    )

    assert result["fact_checks"]["review_count"] == 2
    assert result["visual_analysis"]["description"] == "Pessoa recebendo vacina."
    assert captured == {
        "image": b"image",
        "text": "Vacina causa autismo",
        "media_type": "image/png",
    }