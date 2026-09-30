import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


BACKEND_ENV_FILE = Path(__file__).resolve().parents[1] / "backend" / ".env"
load_dotenv(BACKEND_ENV_FILE)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemma-4-31b-it:free"
DEFAULT_FALLBACK_MODELS = ("qwen/qwen3.8-27b:free",)
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _image_data_url(image: bytes | str | Path, media_type: str | None = None) -> str:
    if isinstance(image, bytes):
        content = image
        media_type = media_type or "image/jpeg"
    else:
        path = Path(image)
        content = path.read_bytes()
        media_type = media_type or mimetypes.guess_type(path.name)[0]
        if not media_type:
            raise ValueError("The image file must have a recognized image format")

    if not content:
        raise ValueError("The image cannot be empty")
    if media_type not in SUPPORTED_IMAGE_TYPES:
        raise ValueError(f"Unsupported image type: {media_type}")

    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def request_image_analysis(
    image: bytes | str | Path,
    text: str | None = None,
    media_type: str | None = None,
) -> dict[str, Any]:
    from openai import OpenAI

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required to analyze images")

    prompt = (
        "Analise a imagem com cautela. Retorne JSON com description (descrição visual objetiva), "
        "possible_manipulation (true somente se houver indícios visuais de edição ou manipulação), "
        "confidence (número entre 0 e 1 que representa a confiança na interpretação visual, "
        "não na veracidade de uma afirmação). Não infira fatos que a imagem não mostra. "
        "Retorne apenas um objeto JSON válido com essas chaves; use analysis como null "
        "quando não houver afirmação informada."
    )
    if text:
        prompt += (
            f' Afirmação informada: "{text}". Inclua também analysis, explicando se a imagem '
            "é visualmente compatível com a afirmação e deixando claro que compatibilidade visual "
            "não comprova a veracidade da afirmação."
        )
    prompt += (
        " Inclua visible_text como uma lista com a transcrição literal de todo texto legível na imagem; "
        "não complete palavras encobertas ou ilegíveis. Não identifique pessoas nem tente deduzir seus nomes; "
        "limite-se a descrever o que é visível. Descreva sinais de conferência, entrevista ou protesto como "
        "indícios visuais, sem afirmar um evento específico que não esteja comprovado pela imagem."
    )

    client = OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={"X-OpenRouter-Title": "Fake News Fact Checker"},
    )
    fallback_models = [
        model.strip()
        for model in os.getenv(
            "OPENROUTER_FALLBACK_MODELS",
            ",".join(DEFAULT_FALLBACK_MODELS),
        ).split(",")
        if model.strip() and model.strip() != os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    ]
    request_options: dict[str, Any] = {
        "model": os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
        "temperature": 0.2,
        "max_tokens": 700,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": _image_data_url(image, media_type)},
                    },
                ],
            }
        ],
    }
    if fallback_models:
        request_options["extra_body"] = {"models": fallback_models}

    response = client.chat.completions.create(
        **request_options,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The vision model returned an empty response")

    return json.loads(content)