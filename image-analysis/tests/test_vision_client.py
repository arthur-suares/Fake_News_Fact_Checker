import base64
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import vision_client


def test_openrouter_request_uses_configured_multimodal_model(monkeypatch):
    captured = {}

    class FakeCompletions:
        @staticmethod
        def create(**kwargs):
            captured["request"] = kwargs
            message = types.SimpleNamespace(
                content=(
                    '{"description":"Pessoa recebendo uma vacina.",'
                    '"visible_text":["Vacina"],'
                    '"possible_manipulation":false,"confidence":0.82,'
                    '"analysis":"A imagem é compatível, mas não comprova a afirmação."}'
                )
            )
            choice = types.SimpleNamespace(message=message)
            return types.SimpleNamespace(choices=[choice])

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.chat = types.SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "google/gemma-4-31b-it:free")

    result = vision_client.request_image_analysis(
        b"png-bytes",
        "Vacina causa autismo",
        "image/png",
    )

    assert result["confidence"] == 0.82
    assert captured["client"]["api_key"] == "test-key"
    assert captured["client"]["base_url"] == vision_client.OPENROUTER_BASE_URL
    request = captured["request"]
    assert request["model"] == "google/gemma-4-31b-it:free"
    assert request["extra_body"]["models"] == ["qwen/qwen3.8-27b:free"]
    assert request["messages"][0]["content"][1]["image_url"]["url"] == (
        "data:image/png;base64," + base64.b64encode(b"png-bytes").decode("ascii")
    )


def test_image_data_url_rejects_unsupported_media_type():
    try:
        vision_client._image_data_url(b"image-bytes", "image/svg+xml")
    except ValueError as error:
        assert "Unsupported image type" in str(error)
    else:
        raise AssertionError("Unsupported image type was accepted")