"""
Validação do modelo de perfis sem dados reais.

O treino em treinar.py é circular: os dados são gerados a
partir de PERFIS e o GMM (principal) e o K-Means (baseline) começam
das mesmas médias. Este script
testa o que dá para testar mesmo assim:

    A. Casos-gabarito      -> respostas típicas caem no perfil certo?
    B. Robustez            -> aguenta ruído e vícios de resposta?
                              (inclui a correção de aquiescência via Q8)
    C. Estabilidade e k    -> os 6 perfis aparecem sozinhos? k=6 faz sentido
                              (silhouette no K-Means, BIC/AIC no GMM)?
    D. GMM x K-Means x regra simples -> os modelos aprendem algo além
                              das médias de PERFIS?
    E. Alertas             -> classificador.py sinaliza respostas suspeitas?

Uso:

    python validar_modelo.py
"""

from itertools import combinations
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import adjusted_rand_score, silhouette_score

from classificador import CAMINHO_MODELO, classificar_lote, corrigir_aquiescencia
from perfis import CENARIOS, PERFIS, desquantizar, gerar_dados, nomes_perfis


PASTA = Path(__file__).resolve().parent

pd.set_option('display.width', 250)


# ============================================================
# 1. CARREGAR MODELO E DADOS
# ============================================================

modelo = joblib.load(CAMINHO_MODELO)

pipeline = modelo['pipeline']
features = modelo['features']
entradas = modelo['entradas']
mapa_clusters = modelo['mapa_clusters']

scaler = pipeline.named_steps['scaler']

df_sintetico = pd.read_csv(PASTA / 'dados' / 'respostas_sinteticas.csv')

vereditos = {}


def prever(X):

    # X = 8 respostas brutas (Q1..Q8); a correção é feita no classificador
    return classificar_lote(modelo, X)['perfil'].to_numpy()


def com_q8_coerente(resposta):

    # Casos escritos com 7 respostas ganham a Q8 coerente (6 - Q4)
    resposta = list(resposta)

    return resposta + [6 - resposta[3]]


def titulo(texto):

    print("\n" + "#" * 70)
    print(texto)
    print("#" * 70)


def distribuicao(perfis):

    return (
        pd.Series(perfis)
        .value_counts(normalize=True)
        .reindex(nomes_perfis, fill_value=0)
        * 100
    ).round(1)


# ============================================================
# 2. A — CASOS-GABARITO
# ============================================================
#
# Ordem: Q1, Q2, Q3, Q4, Q5, Q6, Q7 (a Q8 coerente é acrescentada)
#
# Para cada perfil: a média exata, a média arredondada, duas
# respostas "de livro" escritas à mão e a média arredondada de
# alguém que concorda com tudo (+1 em Q1..Q8). Todas deveriam acertar.
#

CASOS_MANUAIS = {
    'Verificador crítico':        [[2, 2, 5, 2, 5, 1, 3], [1, 2, 5, 3, 4, 1, 3]],
    'Crente resistente':          [[5, 5, 1, 5, 1, 3, 3], [5, 5, 2, 4, 1, 3, 3]],
    'Crente flexível':            [[5, 5, 4, 3, 5, 2, 3], [4, 4, 4, 3, 5, 2, 2]],
    'Compartilhador impulsivo':   [[3, 3, 1, 5, 4, 5, 4], [3, 3, 1, 5, 3, 5, 3]],
    'Cético de baixa circulação': [[1, 1, 2, 1, 2, 1, 1], [2, 2, 2, 1, 2, 1, 2]],
    'Reativo emocional':          [[4, 4, 3, 2, 4, 3, 5], [4, 3, 2, 2, 3, 3, 5]],
}

titulo("A. CASOS-GABARITO")

casos = []

for nome, medias in PERFIS.items():

    casos.append((nome, 'média exata', medias))
    casos.append((nome, 'média arredondada', np.floor(np.array(medias) + 0.5)))

    for i, resposta in enumerate(CASOS_MANUAIS[nome], start=1):
        casos.append((nome, f'manual {i}', resposta))

casos = [(nome, caso, com_q8_coerente(r)) for nome, caso, r in casos]

for nome, medias in PERFIS.items():

    arredondada = com_q8_coerente(np.floor(np.array(medias) + 0.5))

    casos.append((nome, 'concorda c/ tudo', list(np.clip(np.array(arredondada) + 1, 1, 5))))

tabela_a = pd.DataFrame({
    'esperado': [c[0] for c in casos],
    'caso': [c[1] for c in casos],
    'respostas': [','.join(str(int(v)) if float(v).is_integer() else str(v) for v in c[2]) for c in casos],
    'previsto': prever([c[2] for c in casos]),
})

tabela_a['ok'] = np.where(tabela_a['esperado'] == tabela_a['previsto'], 'OK', 'ERRO')

print(tabela_a.to_string(index=False))

acertos_a = (tabela_a['ok'] == 'OK').mean()

print(f"\nAcertos: {acertos_a:.0%}")

vereditos['A. Casos-gabarito'] = (
    'OK' if acertos_a == 1 else 'ATENÇÃO',
    f'{acertos_a:.0%} dos casos no perfil esperado'
)


# ============================================================
# 3. B — ROBUSTEZ A RUÍDO E VÍCIOS DE RESPOSTA
# ============================================================
#
# Usa o modelo SALVO (sem retreinar) em dados novos.
#

titulo("B. ROBUSTEZ")

print("\n" + "=" * 70)
print("B1. ACURÁCIA x RUÍDO (cenário balanceado, dados novos)")
print("=" * 70)

linhas_ruido = []

for ruido in [0.5, 0.7, 1.0, 1.3]:

    np.random.seed(123)

    df = gerar_dados(CENARIOS['balanceado'], ruido=ruido)

    acerto = pd.Series(prever(df[entradas]) == df['perfil_original'])
    recall = acerto.groupby(df['perfil_original']).mean()

    linhas_ruido.append({
        'ruído (desvio)': ruido,
        'acurácia': round(acerto.mean(), 3),
        'pior recall': round(recall.min(), 3),
        'perfil com pior recall': recall.idxmin(),
    })

tabela_ruido = pd.DataFrame(linhas_ruido)

print(tabela_ruido.to_string(index=False))

acc_treino = tabela_ruido.loc[tabela_ruido['ruído (desvio)'] == 0.7, 'acurácia'].iloc[0]
acc_alto = tabela_ruido.loc[tabela_ruido['ruído (desvio)'] == 1.3, 'acurácia'].iloc[0]

vereditos['B1. Ruído'] = (
    'OK' if acc_alto >= 0.6 else 'ATENÇÃO',
    f'acurácia {acc_treino:.0%} no ruído do treino e {acc_alto:.0%} com ruído 1.3'
)

# ------------------------------------------------------------
# B2. VÍCIOS DE RESPOSTA
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("B2. VÍCIOS DE RESPOSTA (% de respondentes em cada perfil)")
print("=" * 70)

np.random.seed(456)

base = gerar_dados(CENARIOS['balanceado'])
X_base = base[entradas].to_numpy()

# Os vícios valem para as 8 respostas, inclusive a Q8 invertida
vicios = {
    'sem vício': X_base,
    'tendência central': np.floor(3 + 0.5 * (X_base - 3) + 0.5).clip(1, 5),
    'aquiescência (+1)': (X_base + 1).clip(1, 5),
    'discorda de tudo (-1)': (X_base - 1).clip(1, 5),
    'aleatório': np.random.randint(1, 6, size=X_base.shape),
}

tabela_vicios = pd.DataFrame({
    nome: distribuicao(prever(X))
    for nome, X in vicios.items()
})

mantem = {
    nome: (prever(X) == base['perfil_original']).mean() * 100
    for nome, X in vicios.items()
    if nome != 'aleatório'
}

print(tabela_vicios.astype(str) + '%')

print("\n% que mantém o perfil original:")
for nome, valor in mantem.items():
    print(f"  {nome:<20} {valor:.1f}%")

maior_aleatorio = tabela_vicios['aleatório'].max()
perfil_lixeira = tabela_vicios['aleatório'].idxmax()

vereditos['B2. Vícios'] = (
    'OK' if maior_aleatorio <= 50 else 'ATENÇÃO',
    f"aleatórios: o perfil mais comum é '{perfil_lixeira}' ({maior_aleatorio:.0f}%)"
)

# ------------------------------------------------------------
# B3. EFEITO DA CORREÇÃO DE AQUIESCÊNCIA (Q8)
# ------------------------------------------------------------
#
# Mesmo GMM, mas ignorando a Q8 (sem corrigir). Mostra quanto
# a pergunta invertida recupera, principalmente para o Cético,
# que some quando a pessoa concorda com tudo.
#

print("\n" + "=" * 70)
print("B3. COM x SEM CORREÇÃO DE AQUIESCÊNCIA (% que mantém o perfil)")
print("=" * 70)


def prever_sem_correcao(X):

    X = pd.DataFrame(np.asarray(X)[:, :len(features)], columns=features)

    return pd.Series(pipeline.predict(X)).map(mapa_clusters).to_numpy()


cetico = (base['perfil_original'] == 'Cético de baixa circulação').to_numpy()

linhas_b3 = []

for nome in ['sem vício', 'aquiescência (+1)', 'discorda de tudo (-1)']:

    X = vicios[nome]
    com, sem = prever(X), prever_sem_correcao(X)
    verdade = base['perfil_original'].to_numpy()

    linhas_b3.append({
        'vício': nome,
        'sem correção': f'{(sem == verdade).mean():.1%}',
        'com correção': f'{(com == verdade).mean():.1%}',
        'Cético sem': f'{(sem[cetico] == verdade[cetico]).mean():.1%}',
        'Cético com': f'{(com[cetico] == verdade[cetico]).mean():.1%}',
    })

print(pd.DataFrame(linhas_b3).to_string(index=False))

X_aq = vicios['aquiescência (+1)']
cetico_aq = (prever(X_aq)[cetico] == 'Cético de baixa circulação').mean()
mantem_aq = (prever(X_aq) == base['perfil_original']).mean()

vereditos['B3. Aquiescência'] = (
    'OK' if cetico_aq >= 0.8 and mantem_aq >= 0.9 else 'ATENÇÃO',
    f'concordando com tudo: {mantem_aq:.0%} mantêm o perfil; '
    f'Cético reconhecido em {cetico_aq:.0%}'
)


# ============================================================
# 4. C — ESTABILIDADE E ESCOLHA DE k
# ============================================================

titulo("C. ESTABILIDADE E ESCOLHA DE k")

# Dados BALANCEADOS e novos: no CSV desbalanceado, o K-Means livre
# tende a dividir o perfil maior em dois só por causa do tamanho,
# o que confunde a escolha de k.

np.random.seed(321)

df_balanceado = gerar_dados(CENARIOS['balanceado'])

X_sint = scaler.transform(corrigir_aquiescencia(df_balanceado[entradas])[0])

# ------------------------------------------------------------
# C1. BOOTSTRAP
# ------------------------------------------------------------
#
# 30 reamostragens com reposição; K-Means livre (sem init fixo)
# em cada uma. Os rótulos são comparados em TODAS as linhas
# originais. ARI alto entre rodadas = clusters estáveis.
#

print("\n" + "=" * 70)
print("C1. BOOTSTRAP (30 reamostragens, K-Means livre)")
print("=" * 70)

rng = np.random.default_rng(789)

rotulos = []

for b in range(30):

    idx = rng.choice(len(X_sint), size=len(X_sint), replace=True)

    km = KMeans(n_clusters=len(PERFIS), n_init=10, random_state=b).fit(X_sint[idx])

    rotulos.append(km.predict(X_sint))

ari_entre = [adjusted_rand_score(a, b) for a, b in combinations(rotulos, 2)]
ari_original = [adjusted_rand_score(df_balanceado['perfil_original'], r) for r in rotulos]

print(f"ARI entre rodadas:         média {np.mean(ari_entre):.3f} | mínimo {np.min(ari_entre):.3f}")
print(f"ARI vs perfis originais:   média {np.mean(ari_original):.3f} | mínimo {np.min(ari_original):.3f}")

vereditos['C1. Estabilidade'] = (
    'OK' if np.mean(ari_entre) >= 0.8 else 'ATENÇÃO',
    f'ARI médio entre rodadas {np.mean(ari_entre):.2f}'
)

# ------------------------------------------------------------
# C2. SILHOUETTE PARA k = 2..10
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("C2. SILHOUETTE x NÚMERO DE CLUSTERS (K-Means livre)")
print("=" * 70)

silhuetas = {}

for k in range(2, 11):

    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X_sint)

    silhuetas[k] = silhouette_score(X_sint, km.labels_)

for k, valor in silhuetas.items():
    marca = '  <- melhor' if k == max(silhuetas, key=silhuetas.get) else ''
    marca += '  (usado)' if k == len(PERFIS) else ''
    print(f"k = {k:>2}: {valor:.3f}{marca}")

melhor_k = max(silhuetas, key=silhuetas.get)
diferenca = silhuetas[melhor_k] - silhuetas[len(PERFIS)]

vereditos['C2. Escolha de k'] = (
    'OK' if diferenca <= 0.02 else 'ATENÇÃO',
    f'melhor k = {melhor_k} (silhouette {silhuetas[melhor_k]:.3f}); '
    f'k = {len(PERFIS)} tem {silhuetas[len(PERFIS)]:.3f}'
)

# ------------------------------------------------------------
# C3. BIC / AIC DO GMM PARA k = 2..10
# ------------------------------------------------------------
#
# Critério da issue para o GMM. Menor é melhor. O BIC pune mais
# componentes, então tende a escolher menos perfis que o AIC.
# Calculado nos dados desquantizados: com respostas inteiras, o BIC
# cai sem parar até k=10 (ver desquantizar em perfis.py).
#

X_criterio = desquantizar(X_sint, scaler)

print("\n" + "=" * 70)
print(f"C3. BIC / AIC x NÚMERO DE COMPONENTES (GMM livre, covariance_type='{modelo['covariance_type']}')")
print("=" * 70)

criterios = {}

for k in range(2, 11):

    g = GaussianMixture(
        n_components=k,
        covariance_type=modelo['covariance_type'],
        n_init=3,
        random_state=42
    ).fit(X_criterio)

    criterios[k] = {'BIC': g.bic(X_criterio), 'AIC': g.aic(X_criterio)}

tabela_criterios = pd.DataFrame(criterios).T

melhor_bic = tabela_criterios['BIC'].idxmin()
melhor_aic = tabela_criterios['AIC'].idxmin()

tabela_criterios['melhor'] = [
    ' '.join(nome for nome, m in (('BIC', melhor_bic), ('AIC', melhor_aic)) if m == k)
    + ('  (usado)' if k == len(PERFIS) else '')
    for k in tabela_criterios.index
]

print(tabela_criterios.round(1).to_string())

vereditos['C3. BIC/AIC (GMM)'] = (
    'OK' if melhor_bic == len(PERFIS) else 'ATENÇÃO',
    f'melhor k pelo BIC = {melhor_bic}, pelo AIC = {melhor_aic}'
)


# ============================================================
# 5. D — GMM x K-MEANS x REGRA SIMPLES (SEM TREINO)
# ============================================================
#
# "Centroide mais próximo" usando direto as médias de PERFIS,
# normalizadas com o mesmo scaler. Se os modelos concordarem ~100%
# com ela, o treino não acrescenta nada: a qualidade depende só
# de PERFIS estar certo.
#

titulo("D. GMM x K-MEANS x REGRA SIMPLES (média de PERFIS mais próxima)")

centroides_perfis = scaler.transform(
    pd.DataFrame(list(PERFIS.values()), columns=features)
)


def regra_simples(X):

    corrigidas = corrigir_aquiescencia(pd.DataFrame(np.asarray(X), columns=entradas))[0]

    Xs = scaler.transform(corrigidas)

    distancias = np.linalg.norm(Xs[:, None, :] - centroides_perfis[None, :, :], axis=2)

    return np.array(nomes_perfis)[distancias.argmin(axis=1)]


conjuntos = {
    'CSV sintético': (df_sintetico[entradas], df_sintetico['perfil_original']),
    'ruído 1.3': None,
    'aleatório': (vicios['aleatório'], None),
}

np.random.seed(123)
df_ruidoso = gerar_dados(CENARIOS['balanceado'], ruido=1.3)
conjuntos['ruído 1.3'] = (df_ruidoso[entradas], df_ruidoso['perfil_original'])

linhas_d = []

for nome, (X, verdade) in conjuntos.items():

    lote = classificar_lote(modelo, X)
    p_gmm = lote['perfil'].to_numpy()
    p_kmeans = lote['perfil_kmeans'].to_numpy()
    p_regra = regra_simples(X)

    linha = {
        'conjunto': nome,
        'GMM = regra': f'{(p_gmm == p_regra).mean():.1%}',
        'GMM = K-Means': f'{(p_gmm == p_kmeans).mean():.1%}',
    }

    for rotulo, previsto in (('GMM', p_gmm), ('K-Means', p_kmeans), ('regra', p_regra)):
        linha[f'acurácia {rotulo}'] = (
            f'{(previsto == verdade).mean():.1%}' if verdade is not None else '-'
        )

    linhas_d.append(linha)

tabela_d = pd.DataFrame(linhas_d)

print(tabela_d.to_string(index=False))

concordancia_csv = (prever(df_sintetico[entradas]) == regra_simples(df_sintetico[entradas])).mean()

vereditos['D. Regra simples'] = (
    'INFO',
    f'{concordancia_csv:.0%} de concordância no CSV — '
    + ('o GMM praticamente reproduz as médias de PERFIS'
       if concordancia_csv >= 0.95 else
       'o GMM se afasta das médias de PERFIS')
)


# ============================================================
# 6. E — ALERTAS DO CLASSIFICADOR
# ============================================================
#
# Bom alerta: dispara pouco em respostas normais e muito em
# respostas aleatórias.
#

titulo("E. ALERTAS DO CLASSIFICADOR (% das respostas com cada alerta)")

conjuntos_e = {
    'normal (ruído 0.7)': vicios['sem vício'],
    'ruído 1.3': df_ruidoso[entradas],
    'tendência central': vicios['tendência central'],
    'aquiescência (+1)': vicios['aquiescência (+1)'],
    'discorda de tudo (-1)': vicios['discorda de tudo (-1)'],
    'aleatório': vicios['aleatório'],
}

colunas_alerta = [
    'respostas_iguais', 'vies_de_resposta', 'fora_do_padrao',
    'entre_dois_perfis', 'tem_alerta',
]

tabela_e = pd.DataFrame({
    nome: classificar_lote(modelo, X)[colunas_alerta].mean() * 100
    for nome, X in conjuntos_e.items()
}).T.round(1)

tabela_e['confiança média'] = [
    f"{classificar_lote(modelo, X)['confianca'].mean():.0%}"
    for X in conjuntos_e.values()
]

print(tabela_e.to_string())

alerta_normal = tabela_e.loc['normal (ruído 0.7)', 'tem_alerta']
alerta_aleatorio = tabela_e.loc['aleatório', 'tem_alerta']

vereditos['E. Alertas'] = (
    'OK' if alerta_aleatorio >= 2 * alerta_normal else 'ATENÇÃO',
    f'alerta em {alerta_normal:.0f}% das respostas normais e '
    f'{alerta_aleatorio:.0f}% das aleatórias'
)


# ============================================================
# 7. RESUMO
# ============================================================

titulo("RESUMO")

for teste, (status, detalhe) in vereditos.items():
    print(f"[{status:^8}] {teste:<20} {detalhe}")

print(
    "\nLembrete: estes testes usam dados sintéticos gerados a partir de\n"
    "PERFIS. Eles checam coerência e robustez, não se os perfis\n"
    "existem de verdade. Para isso: validação por especialistas,\n"
    "piloto com pessoas reais e teste-reteste."
)
