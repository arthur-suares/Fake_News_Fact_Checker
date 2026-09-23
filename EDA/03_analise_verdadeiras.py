"""Análise exploratória apenas do dataset de notícias/declarações verdadeiras."""

import matplotlib.pyplot as plt
import pandas as pd

from utils import COR_TRUE, barh, carregar_true, contar_bigramas, contar_palavras, salvar

df = carregar_true()
print(f"Verdadeiras: {len(df)} registros\n")

palavras = pd.Series(dict(contar_palavras(df["texto_completo"]).most_common(25)))
bigramas = pd.Series(dict(contar_bigramas(df["texto_completo"]).most_common(20)))
print("=== Top 25 palavras ===\n", palavras, "\n")

fig, axes = plt.subplots(1, 2, figsize=(15, 8))
barh(palavras, "Palavras mais frequentes em verdadeiras", COR_TRUE, ax=axes[0])
barh(bigramas, "Bigramas mais frequentes em verdadeiras", COR_TRUE, ax=axes[1])
salvar(fig, "03_true_palavras.png")

# No dataset de verdadeiras, 'origin' é quase sempre quem fez a declaração (políticos)
autores = df["origin"].value_counts().head(15)
print("=== Autores mais checados ===\n", autores, "\n")
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
barh(autores, "Quem mais fez declarações verdadeiras checadas", COR_TRUE, ax=axes[0])
barh(df["publisher_name"].value_counts().head(8), "Agências de checagem", COR_TRUE, ax=axes[1])
salvar(fig, "03_true_autores_publishers.png")

por_ano = df.dropna(subset=["date"])["date"].dt.year.value_counts().sort_index()
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(por_ano.index.astype(str), por_ano.values, color=COR_TRUE)
ax.set_title("Verdadeiras checadas por ano")
salvar(fig, "03_true_por_ano.png")
