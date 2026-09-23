"""Comparação entre fake news e verdadeiras: tamanho dos textos, tempo e vocabulário característico."""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from utils import COR_FAKE, COR_TRUE, barh, carregar_combinado, contar_palavras, salvar

df = carregar_combinado()
cores = {"Fake": COR_FAKE, "Verdadeira": COR_TRUE}

# Tamanho dos textos
print("=== Estatísticas do nº de palavras em 'text' ===")
print(df.groupby("classe")["palavras_text"].describe().round(1), "\n")

fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
limite = df["palavras_text"].quantile(0.95)
for classe, g in df.groupby("classe"):
    axes[0].hist(g["palavras_text"].clip(upper=limite), bins=40, density=True,
                 alpha=0.55, color=cores[classe], label=classe)
axes[0].set_title("Distribuição do nº de palavras (normalizada)")
axes[0].set_xlabel("Palavras no texto (cortado no p95)")
axes[0].legend()

df.boxplot(column="palavras_text", by="classe", ax=axes[1], showfliers=False)
axes[1].set_title("Nº de palavras por classe (sem outliers)")
axes[1].set_xlabel("")
fig.suptitle("")
salvar(fig, "04_tamanho_textos.png")

# Características de escrita
df["pct_maiusculas"] = df["text"].apply(lambda t: sum(c.isupper() for c in t) / max(sum(c.isalpha() for c in t), 1) * 100)
df["exclamacoes"] = df["text"].str.count("!")
print("=== Estilo de escrita (médias) ===")
print(df.groupby("classe")[["pct_maiusculas", "exclamacoes"]].mean().round(2), "\n")

# Proporção por ano
por_ano = (df.dropna(subset=["date"])
             .assign(ano=lambda d: d["date"].dt.year)
             .query("ano >= 2016")
             .groupby(["ano", "classe"]).size().unstack(fill_value=0))
fig, ax = plt.subplots(figsize=(11, 4.5))
por_ano.plot.bar(ax=ax, color=[COR_FAKE, COR_TRUE])
ax.set_title("Checagens por ano e classe")
ax.tick_params(axis="x", rotation=0)
salvar(fig, "04_por_ano.png")

# Vocabulário característico de cada classe (log-odds com suavização)
fake_cnt = contar_palavras(df.loc[df["classe"] == "Fake", "texto_completo"])
true_cnt = contar_palavras(df.loc[df["classe"] == "Verdadeira", "texto_completo"])
vocab = [w for w in set(fake_cnt) | set(true_cnt) if fake_cnt[w] + true_cnt[w] >= 20]
total_f, total_t = sum(fake_cnt.values()), sum(true_cnt.values())
log_odds = pd.Series({
    w: np.log((fake_cnt[w] + 1) / (total_f + len(vocab))) - np.log((true_cnt[w] + 1) / (total_t + len(vocab)))
    for w in vocab
})
mais_fake = log_odds.nlargest(20)
mais_true = log_odds.nsmallest(20).abs()
print("=== Palavras mais típicas de fake ===\n", mais_fake.round(2), "\n")
print("=== Palavras mais típicas de verdadeiras ===\n", mais_true.round(2), "\n")

fig, axes = plt.subplots(1, 2, figsize=(15, 7))
barh(mais_fake, "Palavras mais associadas a FAKE", COR_FAKE, ax=axes[0], xlabel="log-odds")
barh(mais_true, "Palavras mais associadas a VERDADEIRAS", COR_TRUE, ax=axes[1], xlabel="log-odds")
salvar(fig, "04_vocabulario_caracteristico.png")

# Agências em comum
pub = df.groupby(["publisher_name", "classe"]).size().unstack(fill_value=0)
pub = pub.loc[pub.sum(axis=1).nlargest(10).index]
fig, ax = plt.subplots(figsize=(11, 5))
pub.sort_values("Fake").plot.barh(ax=ax, stacked=True, color=[COR_FAKE, COR_TRUE])
ax.set_title("Top 10 agências: fake vs verdadeiras")
ax.set_ylabel("")
salvar(fig, "04_publishers.png")
