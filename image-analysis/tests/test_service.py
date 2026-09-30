import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parents[1]))

import service


def test_analyze_image_returns_validated_result(monkeypatch):
    expected = {
        "description": "Pessoa recebendo uma vacina.",
        "visible_text": ["Vacina"],
        "possible_manipulation": False,
        "confidence": 0.82,
        "analysis": "A imagem é compatível com a afirmação, mas não comprova sua veracidade.",
    }
    captured = {}

    def fake_request(image, text, media_type):
        captured.update(image=image, text=text, media_type=media_type)
        return expected

    monkeypatch.setattr(service, "request_image_analysis", fake_request)

    result = service.analyze_image(b"image-bytes", "Vacina causa autismo")

    assert result == expected
    assert captured == {
        "image": b"image-bytes",
        "text": "Vacina causa autismo",
        "media_type": None,
    }


def test_analyze_image_rejects_invalid_confidence(monkeypatch):
    monkeypatch.setattr(
        service,
        "request_image_analysis",
        lambda _image, _text, _media_type: {
            "description": "Cena",
            "possible_manipulation": False,
            "confidence": 1.2,
        },
    )

    with pytest.raises(ValidationError):
        service.analyze_image(b"image-bytes")


def test_analyze_image_requires_comparison_when_text_is_provided(monkeypatch):
    monkeypatch.setattr(
        service,
        "request_image_analysis",
        lambda _image, _text, _media_type: {
            "description": "Pessoa recebendo uma vacina.",
            "possible_manipulation": False,
            "confidence": 0.82,
        },
    )

    with pytest.raises(ValueError, match="must return an analysis"):
        service.analyze_image(b"image-bytes", "Vacina causa autismo")