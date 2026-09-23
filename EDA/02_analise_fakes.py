"""Análise exploratória apenas do dataset de fake news."""

import matplotlib.pyplot as plt
import pandas as pd

from utils import COR_FAKE, barh, carregar_fakes, contar_bigramas, contar_palavras, plataforma_da_origem, salvar

df = carregar_fakes()
print(f"Fake news: {len(df)} registros\n")

# Assuntos mais comentados: palavras e bigramas nos títulos + textos
palavras = pd.Series(dict(contar_palavras(df["texto_completo"]).most_common(25)))
bigramas = pd.Series(dict(contar_bigramas(df["texto_completo"]).most_common(20)))
print("=== Top 25 palavras ===\n", palavras, "\n")
print("=== Top 20 bigramas ===\n", bigramas, "\n")

fig, axes = plt.subplots(1, 2, figsize=(15, 8))
barh(palavras, "Palavras mais frequentes em fake news", COR_FAKE, ax=axes[0])
barh(bigramas, "Bigramas mais frequentes em fake news", COR_FAKE, ax=axes[1])
salvar(fig, "02_fakes_palavras.png")

# Onde as fake news circulam
plataformas = df["origin"].apply(plataforma_da_origem).value_counts()
origens = df["origin"].str.lower().value_counts().head(15)
print("=== Plataforma de origem ===\n", plataformas, "\n")

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
barh(plataformas, "Plataforma de origem (inferida do campo 'origin')", COR_FAKE, ax=axes[0])
barh(origens, "Top 15 valores do campo 'origin'", COR_FAKE, ax=axes[1])
salvar(fig, "02_fakes_origem.png")

# Agências de checagem
publishers = df["publisher_name"].value_counts().head(12)
fig = barh(publishers, "Agências que mais checaram fake news", COR_FAKE).figure
salvar(fig, "02_fakes_publishers.png")

# Evolução no tempo
por_mes = df.dropna(subset=["date"]).set_index("date").resample("MS").size()
por_mes = por_mes[por_mes.index >= "2018-01-01"]  # poucos registros antes disso
fig, ax = plt.subplots(figsize=(13, 4.5))
ax.plot(por_mes.index, por_mes.values, color=COR_FAKE)
ax.fill_between(por_mes.index, por_mes.values, alpha=0.2, color=COR_FAKE)
ax.set_title("Fake news checadas por mês")
ax.set_ylabel("Quantidade")
salvar(fig, "02_fakes_por_mes.png")
print("=== Meses com mais checagens ===\n", por_mes.nlargest(5), "\n")
