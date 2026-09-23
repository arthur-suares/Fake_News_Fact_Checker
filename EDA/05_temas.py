"""Classifica os registros em temas por palavras-chave e compara fake vs verdadeiras.
Um registro pode pertencer a mais de um tema.
"""

import re

import matplotlib.pyplot as plt

from utils import COR_FAKE, COR_TRUE, barh, carregar_combinado, salvar, sem_acento

TEMAS = {
    "Eleições / urnas": r"eleic|urna|tse|voto|votac|eleitor|candidat|apuracao",
    "Bolsonaro": r"bolsonaro",
    "Lula / PT": r"\blula\b|\bpt\b|petista",
    "STF / Judiciário": r"\bstf\b|supremo|moraes|ministro do|justica",
    "Covid-19": r"covid|coronavirus|pandemia|quarentena|lockdown|sars",
    "Vacinas": r"vacin|imuniz|pfizer|coronavac|astrazeneca",
    "Saúde (outros)": r"cancer|doenca|remedio|medicament|hospital|cura\b|ivermectina|cloroquina",
    "Economia": r"economi|inflac|imposto|combustivel|gasolina|petrobras|salario|dolar|auxilio",
    "Portugal": r"portugal|lisboa|antonio costa|marcelo rebelo|andre ventura|\bsns\b",
    "Guerra Rússia-Ucrânia": r"russia|ucrania|putin|zelensk",
    "Meio ambiente": r"amazonia|desmat|queimad|clima|ambiental",
    "Religião": r"igreja|evangel|cristao|catolic|deus\b",
}

df = carregar_combinado()
texto = df["texto_completo"].str.lower().map(sem_acento)
for tema, padrao in TEMAS.items():
    df[tema] = texto.str.contains(padrao, regex=True)

df["qtd_temas"] = df[list(TEMAS)].sum(axis=1)
print(f"Registros sem nenhum tema: {(df['qtd_temas'] == 0).mean():.1%}\n")

# % de registros de cada classe em cada tema
pct = df.groupby("classe")[list(TEMAS)].mean().T * 100
print("=== % de registros por tema ===\n", pct.round(1), "\n")

fig, ax = plt.subplots(figsize=(11, 7))
pct.sort_values("Fake").plot.barh(ax=ax, color=[COR_FAKE, COR_TRUE])
ax.set_title("Temas: % dos registros de cada classe")
ax.set_xlabel("% dos registros")
salvar(fig, "05_temas_por_classe.png")

# Ranking de temas só nas fakes (contagem absoluta)
fakes = df[df["classe"] == "Fake"]
fig = barh(fakes[list(TEMAS)].sum(), "Assuntos mais comentados em fake news", COR_FAKE).figure
salvar(fig, "05_temas_fakes.png")

# Evolução dos principais temas de fake news ao longo do tempo
top_temas = fakes[list(TEMAS)].sum().nlargest(5).index
serie = (fakes.dropna(subset=["date"])
              .query("date >= '2019-01-01'")
              .set_index("date")[top_temas]
              .resample("QS").sum()
              .iloc[:-1])  # último trimestre está incompleto (dados vão até ~set/2022)
fig, ax = plt.subplots(figsize=(13, 5))
serie.plot(ax=ax, marker="o")
ax.set_title("Top 5 temas de fake news por trimestre")
ax.set_ylabel("Quantidade")
salvar(fig, "05_temas_no_tempo.png")
