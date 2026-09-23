"""Visão geral dos dois datasets: tamanho, nulos, duplicados e balanceamento das classes."""

import matplotlib.pyplot as plt

from utils import COR_FAKE, COR_TRUE, carregar_combinado, salvar

df = carregar_combinado()

print("=== Dimensões por classe ===")
print(df["classe"].value_counts(), "\n")

print("=== Valores nulos (%) por classe ===")
colunas = ["title", "text", "origin", "publisher_name", "date"]
nulos = df.groupby("classe")[colunas].apply(lambda g: g.isna().mean() * 100).round(1)
print(nulos, "\n")

print("=== Duplicados ===")
for classe, g in df.groupby("classe"):
    print(f"{classe}: {g.duplicated(['title', 'text']).sum()} linhas duplicadas (title+text), "
          f"{g['url'].nunique()} URLs únicas para {len(g)} linhas")
print()

print("=== Período coberto ===")
print(df.groupby("classe")["date"].agg(["min", "max"]), "\n")

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

contagem = df["classe"].value_counts()
axes[0].bar(contagem.index, contagem.values, color=[COR_FAKE, COR_TRUE])
axes[0].set_title("Quantidade de registros por classe")
for i, v in enumerate(contagem.values):
    axes[0].text(i, v, f"{v:,}".replace(",", "."), ha="center", va="bottom")

nulos.T.plot.bar(ax=axes[1], color=[COR_FAKE, COR_TRUE])
axes[1].set_title("% de valores nulos por coluna")
axes[1].set_ylabel("%")
axes[1].tick_params(axis="x", rotation=0)

salvar(fig, "01_visao_geral.png")
