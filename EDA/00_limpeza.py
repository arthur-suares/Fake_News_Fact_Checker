"""Limpeza dos datasets.

Lê os CSVs originais em datasets/ (sem alterá-los) e grava as versões tratadas em
datasets/limpos/, junto com um relatório do que foi alterado.

Registros com problemas que a limpeza não consegue resolver vão para
datasets/limpos/nao_tratados.csv, com a coluna 'motivo'. Os removidos (duplicados e sem
campos obrigatórios) só aparecem lá; os demais continuam também nos datasets limpos.
"""

import re
from pathlib import Path

import pandas as pd

EDA_DIR = Path(__file__).resolve().parent
ORIGINAIS = EDA_DIR / "datasets"
LIMPOS = ORIGINAIS / "limpos"

# O mesmo site aparece com nomes diferentes em 'publisher_name' (acento, variações, nulos),
# então o nome padronizado é definido a partir de 'publisher_site'.
PUBLISHERS = {
    "aosfatos.org": "Aos Fatos",
    "boatos.org": "Boatos.org",
    "bol.uol.com.br": "BOL - UOL",
    "checamos.afp.com": "AFP Checamos",
    "e-farsas.com": "E-farsas",
    "lupa.uol.com.br": "Lupa - UOL",
    "noticias.uol.com.br": "UOL Notícias",
    "observador.pt": "Observador",
    "piaui.folha.uol.com.br": "Revista Piauí",
    "poligrafo.sapo.pt": "Polígrafo - SAPO",
    "politica.estadao.com.br": "Estadão",
    "projetocomprova.com.br": "Projeto Comprova",
}

# Variações de escrita de 'origin' que significam a mesma coisa (chave em minúsculas)
ORIGENS_SINONIMOS = {
    "utilizador de facebook": "Utilizador do Facebook",
    "utilizador do facebook": "Utilizador do Facebook",
    "post do facebook": "Post no Facebook",
    "post no facebook": "Post no Facebook",
    "publicação no facebook": "Post no Facebook",
    "boato de redes sociais": "Boatos de redes sociais",
    "boatos de redes sociais": "Boatos de redes sociais",
    "boato de rede sociais": "Boatos de redes sociais",
    "boatos nas redes sociais": "Boatos de redes sociais",
    "múltiplas fontes": "Várias fontes",
    "várias fontes": "Várias fontes",
    "mensagem no whatsapp": "Mensagem no WhatsApp",
    "post no whatsapp": "Mensagem no WhatsApp",
    "lula": "Luiz Inácio Lula da Silva",
}

# Valores de 'origin' que não indicam a origem de fato (rótulos genéricos das agências)
ORIGENS_INVALIDAS = {"desinformação", "checamos"}

DATA_MINIMA = "2010-01-01"
MIN_PALAVRAS = 3             # textos mais curtos que isso não têm conteúdo para análise
MAX_DIAS_DATA_VS_URL = 60    # as agências do dataset começaram a checar depois disso
ASPAS = "\"'“”‘’«»"


def limpar_texto(s: pd.Series) -> pd.Series:
    s = s.str.replace(r"[ ​‌‍﻿]", " ", regex=True)                               # espaços invisíveis
    s = s.str.replace(r"\s+", " ", regex=True).str.strip()                    # quebras e espaços extras
    s = s.str.strip(ASPAS).str.strip()                                        # aspas nas bordas
    return s.replace("", pd.NA)


def padronizar_origem(origem: pd.Series) -> pd.Series:
    origem = limpar_texto(origem)
    chave = origem.str.lower()
    # Para variações só de maiúsculas/minúsculas, usa a grafia mais frequente
    grafia_mais_comum = origem.groupby(chave).agg(lambda g: g.value_counts().index[0])
    padrao = chave.map(ORIGENS_SINONIMOS).fillna(chave.map(grafia_mais_comum))
    return padrao.mask(chave.isin(ORIGENS_INVALIDAS))


def data_da_url(url: pd.Series) -> pd.Series:
    partes = url.str.extract(r"/(20\d\d)/(\d\d)/(\d\d)/")
    return pd.to_datetime(partes[0] + "-" + partes[1] + "-" + partes[2], errors="coerce")


def limpar(df: pd.DataFrame, nome: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Retorna (dados limpos, registros com problemas não resolvidos)."""
    relatorio = {}
    removidos = []
    df = df.copy()

    # Textos
    for col in ["title", "text", "url", "publisher_site"]:
        df[col] = limpar_texto(df[col])
    so_url = df["text"].str.fullmatch(r"https?://\S+", na=False)
    df.loc[so_url, "text"] = pd.NA
    sem_texto = df["text"].isna()
    df.loc[sem_texto, "text"] = df.loc[sem_texto, "title"]
    relatorio["text vazio/só URL substituído pelo title"] = int(sem_texto.sum())

    antes = len(df)
    sem_campos = df[["title", "text", "url"]].isna().any(axis=1)
    removidos.append(df[sem_campos].assign(motivo="sem title/text/url (removido)"))
    df = df[~sem_campos]
    relatorio["linhas removidas sem title/text/url"] = antes - len(df)

    df["text_igual_title"] = df["text"].str.lower() == df["title"].str.lower()
    relatorio["text idêntico ao title (marcado em 'text_igual_title')"] = int(df["text_igual_title"].sum())

    # Duplicados: mesma alegação no mesmo artigo
    antes = len(df)
    duplicado = df.duplicated(subset=["title", "text", "url"])
    removidos.append(df[duplicado].assign(motivo="duplicado (removido)"))
    df = df[~duplicado]
    relatorio["duplicados removidos (title+text+url)"] = antes - len(df)

    # Agência
    antes = df["publisher_name"].nunique()
    df["publisher_name"] = (df["publisher_site"].map(PUBLISHERS)
                            .fillna(df["publisher_name"])
                            .fillna(df["publisher_site"]))
    relatorio["nomes de agência (antes -> depois)"] = f"{antes} -> {df['publisher_name'].nunique()}"

    # Origem
    antes = df["origin"].nunique()
    df["origin"] = padronizar_origem(df["origin"])
    relatorio["valores distintos de origin (antes -> depois)"] = f"{antes} -> {df['origin'].nunique()}"

    # Datas
    datas = pd.to_datetime(df["date"], errors="coerce", utc=True, format="ISO8601").dt.tz_convert(None)
    invalidas = datas < DATA_MINIMA
    relatorio[f"datas anteriores a {DATA_MINIMA} anuladas"] = int(invalidas.sum())
    datas = datas.mask(invalidas)
    df["date_fonte"] = datas.notna().map({True: "original", False: pd.NA})
    da_url = data_da_url(df["url"])
    recuperar = datas.isna() & da_url.notna()
    datas = datas.fillna(da_url)
    df.loc[recuperar, "date_fonte"] = "url"
    df["date"] = datas
    relatorio["datas vazias recuperadas da URL"] = int(recuperar.sum())
    diverge_url = (datas - da_url).dt.days.abs() > MAX_DIAS_DATA_VS_URL
    relatorio["datas ainda vazias"] = int(df["date"].isna().sum())

    # Rótulo
    rotulos = set(df["label"].unique())
    if not rotulos <= {0, 1}:
        raise ValueError(f"{nome}: rótulos inesperados em 'label': {rotulos}")

    # Problemas que continuam nos dados limpos
    motivos = {
        "sem data (nem na URL)": df["date"].isna(),
        f"texto com menos de {MIN_PALAVRAS} palavras": df["text"].str.split().str.len() < MIN_PALAVRAS,
        f"date difere da data da URL em mais de {MAX_DIAS_DATA_VS_URL} dias": diverge_url,
        f"data anterior a {DATA_MINIMA} (anulada)": invalidas,
    }
    motivo = pd.Series("", index=df.index)
    for descricao, mascara in motivos.items():
        motivo = motivo.mask(mascara, motivo + "; " + descricao)
    com_problema = df[motivo != ""].assign(motivo=motivo.str.lstrip("; "))

    nao_tratados = pd.concat([*removidos, com_problema], ignore_index=True)
    nao_tratados.insert(0, "dataset", nome)
    nao_tratados["mantido_no_limpo"] = ~nao_tratados["motivo"].str.contains("removido")
    relatorio["registros com problema não resolvido"] = len(nao_tratados)

    print(f"\n=== {nome}: {len(df)} linhas após limpeza ===")
    for item, valor in relatorio.items():
        print(f"  {item}: {valor}")
    return df, nao_tratados


def main():
    LIMPOS.mkdir(exist_ok=True)
    limpos, nao_tratados = {}, []
    for arquivo in ["fakes.csv", "true.csv"]:
        limpos[arquivo], problemas = limpar(pd.read_csv(ORIGINAIS / arquivo), arquivo)
        limpos[arquivo].to_csv(LIMPOS / arquivo, index=False)
        nao_tratados.append(problemas)

    nao_tratados = pd.concat(nao_tratados, ignore_index=True)
    nao_tratados.to_csv(LIMPOS / "nao_tratados.csv", index=False)
    print(f"\n=== Registros não tratados: {len(nao_tratados)} (em nao_tratados.csv) ===")
    print(nao_tratados["motivo"].str.split("; ").explode()
          .groupby([nao_tratados["dataset"]]).value_counts().to_string())

    # Checagem entre os datasets: mesma alegação com rótulos opostos
    chave = ["url", "text"]
    conflito = limpos["fakes.csv"][chave].merge(limpos["true.csv"][chave])
    print(f"\nAlegações presentes nos dois datasets (rótulos conflitantes): {len(conflito)}")
    print(f"Arquivos limpos salvos em {LIMPOS.relative_to(EDA_DIR)}/")


if __name__ == "__main__":
    main()
