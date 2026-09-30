"""
Matriz de confusão do modelo de perfis (GMM principal e K-Means baseline).

Dois conjuntos:

    treino  -> dados/respostas_sinteticas.csv (cenário desbalanceado usado no treino)
    teste   -> dados NOVOS, cenário balanceado (100 por perfil), mesmo ruído

As células são coloridas pelo % da linha (recall de cada perfil) e
mostram a contagem e o %. Lembrete: os dados são sintéticos, gerados
a partir de PERFIS — a matriz mede coerência, não validade real.

Uso:

    python matriz_confusao.py

Gera relatorios/matriz_confusao.png.
"""

from pathlib import Path

import joblib
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from sklearn.metrics import classification_report, confusion_matrix  # noqa: E402

from classificador import CAMINHO_MODELO, classificar_lote  # noqa: E402
from perfis import CENARIOS, gerar_dados, nomes_perfis  # noqa: E402


PASTA = Path(__file__).resolve().parent

pd.set_option('display.width', 250)

# Rampa sequencial azul (claro -> escuro)
AZUIS = LinearSegmentedColormap.from_list(
    'azuis',
    ['#f4f8fe', '#cde2fb', '#86b6ef', '#3987e5', '#256abf', '#184f95', '#0d366b']
)

TINTA = '#1f1f1e'
TINTA_SECUNDARIA = '#5f5e5a'

# Nomes quebrados em duas linhas para caber nos eixos
ROTULOS = [nome.replace(' ', '\n', 1) for nome in nomes_perfis]


# ============================================================
# 1. MODELO E DADOS
# ============================================================

modelo = joblib.load(CAMINHO_MODELO)
entradas = modelo['entradas']

df_treino = pd.read_csv(PASTA / 'dados' / 'respostas_sinteticas.csv')

np.random.seed(2024)
df_teste = gerar_dados(CENARIOS['balanceado'])

conjuntos = {
    f'Treino (CSV desbalanceado, n={len(df_treino)})': df_treino,
    f'Teste (dados novos balanceados, n={len(df_teste)})': df_teste,
}


# ============================================================
# 2. MATRIZES
# ============================================================

def matriz(verdade, previsto):

    return confusion_matrix(verdade, previsto, labels=nomes_perfis)


resultados = {}

for nome, df in conjuntos.items():

    lote = classificar_lote(modelo, df[entradas])
    verdade = df['perfil_original'].to_numpy()

    for rotulo, coluna in (('GMM', 'perfil'), ('K-Means', 'perfil_kmeans')):

        previsto = lote[coluna].to_numpy()
        resultados[(rotulo, nome)] = (matriz(verdade, previsto), (previsto == verdade).mean())

        print("\n" + "=" * 70)
        print(f"{rotulo} — {nome}")
        print("=" * 70)
        print(pd.DataFrame(
            matriz(verdade, previsto),
            index=[f'real: {n}' for n in nomes_perfis],
            columns=nomes_perfis,
        ).to_string())
        print()
        print(classification_report(verdade, previsto, labels=nomes_perfis, digits=3, zero_division=0))


# ============================================================
# 3. FIGURA
# ============================================================

def desenhar(ax, cm, titulo):

    percentual = cm / cm.sum(axis=1, keepdims=True).clip(min=1)

    ax.imshow(percentual, cmap=AZUIS, vmin=0, vmax=1)

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):

            escuro = percentual[i, j] >= 0.55
            cor = 'white' if escuro else TINTA

            if cm[i, j] == 0:
                ax.text(j, i, '·', ha='center', va='center', color=TINTA_SECUNDARIA, fontsize=10)
                continue

            ax.text(j, i - 0.12, f'{cm[i, j]}', ha='center', va='center',
                    color=cor, fontsize=11, fontweight='bold')
            texto_pct = '<1%' if percentual[i, j] < 0.005 else f'{percentual[i, j]:.0%}'

            ax.text(j, i + 0.22, texto_pct, ha='center', va='center',
                    color=cor, fontsize=8)

    ax.set_xticks(range(len(ROTULOS)), ROTULOS, fontsize=8, color=TINTA_SECUNDARIA)
    ax.set_yticks(range(len(ROTULOS)), ROTULOS, fontsize=8, color=TINTA_SECUNDARIA)
    ax.set_xlabel('Perfil previsto', color=TINTA, fontsize=9)
    ax.set_ylabel('Perfil real', color=TINTA, fontsize=9)
    ax.set_title(titulo, loc='left', color=TINTA, fontsize=10, pad=10)

    # Separação de 2px entre as células
    ax.set_xticks(np.arange(-0.5, cm.shape[1]), minor=True)
    ax.set_yticks(np.arange(-0.5, cm.shape[0]), minor=True)
    ax.grid(which='minor', color='white', linewidth=2)
    ax.tick_params(which='both', length=0)

    for borda in ax.spines.values():
        borda.set_visible(False)


fig, eixos = plt.subplots(2, 2, figsize=(15, 14), facecolor='white')

for linha, rotulo in enumerate(('GMM', 'K-Means')):
    for coluna, nome in enumerate(conjuntos):

        cm, acuracia = resultados[(rotulo, nome)]
        desenhar(eixos[linha, coluna], cm, f'{rotulo} — {nome}\nacurácia {acuracia:.1%}')

fig.suptitle(
    'Matriz de confusão — perfis de leitor (cor = % da linha / recall)',
    x=0.02, ha='left', fontsize=14, color=TINTA,
)
fig.text(
    0.02, 0.005,
    'Dados sintéticos gerados a partir de PERFIS (perfis.py): mede coerência do modelo, não validade com pessoas reais.',
    fontsize=8, color=TINTA_SECUNDARIA,
)

fig.tight_layout(rect=(0, 0.02, 1, 0.97))

saida = PASTA / 'relatorios' / 'matriz_confusao.png'
saida.parent.mkdir(exist_ok=True)
fig.savefig(saida, dpi=150)

print(f"\nFigura salva em: {saida}")
