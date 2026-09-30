from __future__ import annotations

import hashlib
import logging
import math
import os
import re
import unicodedata
from typing import Any, List

import requests

logger = logging.getLogger(__name__)

Documents = List[str]
Embeddings = List[List[float]]


class BaseEmbeddingFunction:
    """Interface base para funções de geração de embeddings."""

    dimension: int = 384

    def name(self) -> str:
        return "base_embedding_function"

    def __call__(self, input: Documents) -> Embeddings:
        raise NotImplementedError

    def embed_query(self, input: Documents) -> Embeddings:
        return self(input)

    def embed_documents(self, input: Documents) -> Embeddings:
        return self(input)

    def is_legacy(self) -> bool:
        return False

    def default_space(self) -> str:
        return "cosine"

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]


class LocalONNXEmbeddingFunction(BaseEmbeddingFunction):
    """
    Gera embeddings localmente utilizando o modelo ONNX all-MiniLM-L6-v2.
    Não requer conexão com a internet após o download local do modelo.
    """

    dimension: int = 384

    def name(self) -> str:
        return "local_onnx"

    def __init__(self, model_dir: str | None = None) -> None:
        self.model_dir = model_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "models", "all-MiniLM-L6-v2")
        )
        self._ef = None
        self._initialize_onnx()

    def _initialize_onnx(self) -> None:
        try:
            from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import ONNXMiniLM_L6_V2

            if os.path.exists(self.model_dir):
                ONNXMiniLM_L6_V2.DOWNLOAD_PATH = self.model_dir
            self._ef = ONNXMiniLM_L6_V2()
            logger.info("LocalONNXEmbeddingFunction inicializado com sucesso em %s", self.model_dir)
        except Exception as exc:
            logger.warning("Falha ao inicializar ONNXMiniLM_L6_V2 (%s). Usando fallback determinístico.", exc)
            self._ef = None

    def __call__(self, input: Documents) -> Embeddings:
        if self._ef is not None:
            try:
                embeddings = self._ef(input)
                # Garantir tipo float nativo
                return [[float(val) for val in vec] for vec in embeddings]
            except Exception as exc:
                logger.error("Erro na inferência ONNX: %s. Usando fallback.", exc)
        # Fallback se ONNX falhar
        fallback = DeterministicSparseEmbeddingFunction(dimension=self.dimension)
        return fallback(input)


class DeterministicSparseEmbeddingFunction(BaseEmbeddingFunction):
    """
    Função de embedding determinística baseada em n-gramas e hashing (Feature Hashing / TF-IDF aproximado).
    100% offline, sem bibliotecas pesadas, ideal para fallback, testes rápidos e ambientes com restrições.
    """

    dimension: int = 384

    def name(self) -> str:
        return "deterministic"

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = unicodedata.normalize("NFKD", text.lower())
        text = "".join(c for c in text if not unicodedata.combining(c))
        return re.sub(r"[^a-z0-9\s]", " ", text).strip()

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: Embeddings = []
        for doc in input:
            norm_doc = self._normalize_text(doc)
            words = norm_doc.split()
            tokens: list[str] = list(words)

            # Bi-gramas de palavras
            for i in range(len(words) - 1):
                tokens.append(f"{words[i]}_{words[i+1]}")

            # Tri-gramas de caracteres
            compact = "".join(words)
            for i in range(len(compact) - 2):
                tokens.append(compact[i : i + 3])

            vector = [0.0] * self.dimension
            if not tokens:
                embeddings.append(vector)
                continue

            for token in tokens:
                # Hash determinístico com md5
                idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.dimension
                vector[idx] += 1.0

            # Normalização L2 para distância cosseno
            norm = math.sqrt(sum(v * v for v in vector))
            if norm > 0.0:
                vector = [v / norm for v in vector]
            embeddings.append(vector)
        return embeddings


class GoogleGeminiEmbeddingFunction(BaseEmbeddingFunction):
    """Gera embeddings via Google Gemini Embedding API (text-embedding-004)."""

    dimension: int = 768

    def name(self) -> str:
        return "google_gemini"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.endpoint = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: Embeddings = []
        for text in input:
            try:
                res = requests.post(
                    f"{self.endpoint}?key={self.api_key}",
                    json={"model": "models/text-embedding-004", "content": {"parts": [{"text": text}]}},
                    timeout=10,
                )
                if res.status_code == 200:
                    values = res.json().get("embedding", {}).get("values", [])
                    embeddings.append([float(x) for x in values])
                else:
                    logger.warning("Falha na API Gemini embeddings: %s. Usando fallback.", res.text)
                    fallback = DeterministicSparseEmbeddingFunction(dimension=self.dimension)
                    embeddings.append(fallback([text])[0])
            except Exception as exc:
                logger.error("Exceção ao chamar Gemini embeddings: %s", exc)
                fallback = DeterministicSparseEmbeddingFunction(dimension=self.dimension)
                embeddings.append(fallback([text])[0])
        return embeddings


class OpenRouterEmbeddingFunction(BaseEmbeddingFunction):
    """Gera embeddings via OpenRouter."""

    dimension: int = 1536

    def name(self) -> str:
        return "openrouter"

    def __init__(self, api_key: str, model: str = "openai/text-embedding-3-small") -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://openrouter.ai/api/v1/embeddings"

    def __call__(self, input: Documents) -> Embeddings:
        try:
            res = requests.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": input},
                timeout=15,
            )
            if res.status_code == 200:
                data = res.json().get("data", [])
                return [[float(x) for x in item.get("embedding", [])] for item in data]
        except Exception as exc:
            logger.error("Erro na API OpenRouter embeddings: %s", exc)
        fallback = DeterministicSparseEmbeddingFunction(dimension=self.dimension)
        return fallback(input)


def get_embedding_function(
    provider: str = "auto",
    model_dir: str | None = None,
    api_key: str | None = None,
) -> BaseEmbeddingFunction:
    """Factory para instanciar a função de embedding apropriada."""
    provider_clean = (provider or "auto").strip().lower()

    if provider_clean in ("deterministic", "hash", "sparse"):
        return DeterministicSparseEmbeddingFunction()

    if provider_clean == "google" and api_key:
        return GoogleGeminiEmbeddingFunction(api_key=api_key)

    if provider_clean == "openrouter" and api_key:
        return OpenRouterEmbeddingFunction(api_key=api_key)

    # Modo padrão/auto ou onnx:
    # Se modelo local ONNX existir, prioriza LocalONNXEmbeddingFunction
    onnx_path = model_dir or os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "models", "all-MiniLM-L6-v2")
    )
    if os.path.exists(os.path.join(onnx_path, "onnx", "model.onnx")) or os.path.exists(
        os.path.join(onnx_path, "model.onnx")
    ):
        return LocalONNXEmbeddingFunction(model_dir=onnx_path)

    if provider_clean == "onnx":
        return LocalONNXEmbeddingFunction(model_dir=onnx_path)

    # Fallback determinístico
    return DeterministicSparseEmbeddingFunction()
