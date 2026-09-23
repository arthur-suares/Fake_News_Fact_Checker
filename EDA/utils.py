"""Funções compartilhadas pelos scripts de EDA: carregamento dos dados limpos e tokenização."""

import re
import runpy
import unicodedata
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

EDA_DIR = Path(__file__).resolve().parent
LIMPOS_DIR = EDA_DIR / "datasets" / "limpos"
OUTPUT_DIR = EDA_DIR / "outputs"

COR_FAKE = "#d62728"
COR_TRUE = "#2ca02c"

STOPWORDS = set("""
a à ao aos as às até após com como contra da das de dela dele deles do dos e é em entre era
eram essa esse esta está estão este eu foi foram há isso isto já la lá lhe mais mas me mesmo
meu minha muito na nas nem no nos nós não o os ou para pela pelas pelo pelos por qual quando
que quem se sem seu seus sua suas são só também te tem têm ter um uma umas uns vai vão você
ser sobre sua seja ainda aqui ali assim cada depois desde disse diz dizem ela ele eles elas
esses essas estes estas estava estavam faz fazer foi sido sim tão todo toda todos todas tudo
vez vezes vídeo video foto imagem post publicação publicações mostra mostram falso falsa
verdadeiro verdadeira enganoso enganosa não é teria teriam após através onde porque pois
seria será serão sendo tinha tinham outro outra outros outras apenas agora ano anos dia dias
the of to and in is que
fact check checagem checado boato boatos erra erro erros acerta acertos acerto engana
confirma verdade mentira desmente desmentido falar afirma afirmou
""".split())

PLATAFORMAS = {
    "WhatsApp": r"whats|zap",
    "Facebook": r"facebook|fb\b",
    "Twitter/X": r"twitter|tweet|\bx\b",
    "Instagram": r"instagram",
    "YouTube": r"youtube",
    "TikTok": r"tiktok|tik tok",
    "Telegram": r"telegram",
    "Kwai": r"kwai",
}


def _ler(nome: str) -> pd.DataFrame:
    """Lê a versão limpa do dataset (gerada por 00_limpeza.py; roda a limpeza se ainda não existir)."""
    caminho = LIMPOS_DIR / nome
    if not caminho.exists():
        print("Datasets limpos não encontrados, rodando 00_limpeza.py...")
        runpy.run_path(str(EDA_DIR / "00_limpeza.py"), run_name="__main__")
    df = pd.read_csv(caminho)
    df["date"] = pd.to_datetime(df["date"], format="ISO8601")
    # Quando text é cópia do title, usa só o title para não contar as palavras duas vezes
    df["texto_completo"] = df["title"].where(df["text_igual_title"], df["title"] + " " + df["text"])
    df["len_text"] = df["text"].str.len()
    df["palavras_text"] = df["text"].str.split().str.len()
    return df


def carregar_fakes() -> pd.DataFrame:
    return _ler("fakes.csv")


def carregar_true() -> pd.DataFrame:
    return _ler("true.csv")


def carregar_combinado() -> pd.DataFrame:
    """Une os dois datasets com uma coluna 'classe' legível ('Fake' / 'Verdadeira')."""
    df = pd.concat([carregar_fakes(), carregar_true()], ignore_index=True)
    df["classe"] = df["label"].map({1: "Fake", 0: "Verdadeira"})
    return df


def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r"https?://\S+", " ", texto)
    return texto


def tokenizar(texto: str, min_len: int = 3) -> list[str]:
    tokens = re.findall(r"[a-zà-ÿ]+", normalizar(texto))
    return [t for t in tokens if len(t) >= min_len and t not in STOPWORDS]


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def contar_palavras(serie: pd.Series) -> Counter:
    contador = Counter()
    for texto in serie.dropna():
        contador.update(tokenizar(texto))
    return contador


def contar_bigramas(serie: pd.Series) -> Counter:
    contador = Counter()
    for texto in serie.dropna():
        tokens = tokenizar(texto)
        contador.update(" ".join(par) for par in zip(tokens, tokens[1:]))
    return contador


def plataforma_da_origem(origem) -> str:
    if not isinstance(origem, str):
        return "Não informado"
    o = origem.lower()
    for nome, padrao in PLATAFORMAS.items():
        if re.search(padrao, o):
            return nome
    return "Outros"


def barh(serie: pd.Series, titulo: str, cor: str, ax=None, xlabel: str = "Frequência"):
    """Gráfico de barras horizontais com o maior valor no topo."""
    if ax is None:
        _, ax = plt.subplots(figsize=(9, max(4, len(serie) * 0.35)))
    serie.sort_values().plot.barh(ax=ax, color=cor)
    ax.set_title(titulo)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    return ax


def salvar(fig, nome: str):
    OUTPUT_DIR.mkdir(exist_ok=True)
    caminho = OUTPUT_DIR / nome
    fig.tight_layout()
    fig.savefig(caminho, dpi=120)
    plt.close(fig)
    print(f"  -> gráfico salvo em {caminho.relative_to(EDA_DIR)}")
