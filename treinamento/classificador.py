"""
Atalho para o módulo de perfilamento do backend (backend/app/ml/perfil.py).

O código de classificação vive no backend, que é quem o usa em
produção. Os scripts desta pasta (treino, validação, teste no
terminal) importam daqui para usar exatamente o mesmo código.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))

from app.ml.perfil import (  # noqa: E402,F401
    CAMINHO_MODELO,
    ENTRADAS,
    ORDEM_EXIBICAO,
    PERGUNTAS,
    RespostasInvalidas,
    classificar,
    classificar_lote,
    corrigir_aquiescencia,
    vetor_de_respostas,
)
