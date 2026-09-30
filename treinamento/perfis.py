"""
Dados sintéticos do questionário: perguntas usadas no modelo, os 6
perfis (médias esperadas das respostas) e o gerador de respostas.

Não treina nem salva nada, então pode ser importado por qualquer
script desta pasta (treinar.py, validar_modelo.py, matriz_confusao.py).
"""

import numpy as np
import pandas as pd

from classificador import ENTRADAS, ORDEM_EXIBICAO, PERGUNTAS

# ============================================================
# 1. PERGUNTAS UTILIZADAS PARA DEFINIR O PERFIL
# ============================================================
#
# Textos completos e escalas: PERGUNTAS em classificador.py.
#
# TODAS AS RESPOSTAS:
# 1 = mínimo
# 5 = máximo
#
# Q1 - Antes da verificação, você achava que a notícia era
#      verdadeira?
#
# Q2 - O quanto você acreditava na notícia?
#
# Q3 - Você costuma verificar informações antes de
#      compartilhá-las?
#
# Q4 - "Eu confio nas notícias que recebo pelas redes sociais."
#      (discordo totalmente ... concordo totalmente)
#
# Q5 - Se a verificação indicar o oposto do que você acha,
#      o quão aberto você está para mudar de opinião?
#
# Q6 - Qual a probabilidade de você compartilhar essa notícia?
#
# Q7 - O quanto o assunto dessa notícia mexeu com suas emoções?
#
# Q8 - "Quando uma notícia chega pelo WhatsApp ou Instagram,
#      eu desconfio dela." (discordo totalmente ... concordo totalmente)
#      PERGUNTA INVERTIDA: é o contrário da Q4. Quem responde com
#      coerência tem Q4 + Q8 ≈ 6. Ela não entra no K-Means como
#      pergunta própria; serve para medir e corrigir a
#      AQUIESCÊNCIA (tendência de concordar com tudo) ou o
#      contrário (discordar de tudo). Ver corrigir_aquiescencia()
#      em classificador.py.
#      Q4 e Q8 têm o MESMO formato (afirmação + concordância) para
#      o viés atuar igual nas duas, e redação diferente para a
#      pessoa não perceber que são opostas.
#
# ORDEM NA TELA (ORDEM_EXIBICAO em classificador.py):
#      Q3, Q4, Q1, Q2, Q5, Q6, Q7, Q8 -> 5 perguntas entre Q4 e Q8.
#      A numeração e a ordem que o modelo recebe continuam Q1..Q8.
#
# Q9 NÃO entra no K-Means.
# Ela é respondida depois da verificação.
#


features = [
    'q1_crenca_inicial',
    'q2_credibilidade',
    'q3_verificacao',
    'q4_confianca_redes',
    'q5_abertura_mudanca',
    'q6_compartilhamento',
    'q7_emocao'
]

# Pergunta invertida (Q8) e a lista completa do que o usuário responde
# antes da verificação, na ordem em que o modelo recebe.
ITEM_INVERTIDO = 'q8_desconfia_redes'

entradas = features + [ITEM_INVERTIDO]

# Os nomes e a ordem precisam bater com o backend (app/ml/perfil.py),
# que monta o vetor de entrada a partir do JSON `answers`.
assert entradas == ENTRADAS, 'entradas fora da ordem esperada pelo backend'
assert set(entradas) <= set(PERGUNTAS), 'coluna sem texto em PERGUNTAS'
assert sorted(ORDEM_EXIBICAO) == sorted(entradas), 'ORDEM_EXIBICAO incompleta'


# ============================================================
# 2. OS 6 PERFIS (MÉDIAS ESPERADAS DAS RESPOSTAS)
# ============================================================
#
# A ordem deste dicionário define o cluster_id:
# cluster 0 = Verificador crítico, cluster 1 = Crente resistente...
#
# Ordem das médias: Q1, Q2, Q3, Q4, Q5, Q6, Q7
#
# Cada perfil tem um traço dominante que o separa dos outros.
# Na versão anterior, Crente resistente, Compartilhador impulsivo
# e Reativo emocional eram quase iguais (distância de 1,5 ponto),
# o que limitava o acerto de QUALQUER modelo a ~75% nesses perfis.
#
#   Verificador crítico      -> verifica sempre (Q3) + aberto a mudar (Q5)
#   Crente resistente        -> crença máxima + fechado a mudar (Q5)
#   Crente flexível          -> crença alta, mas verifica e muda (Q3, Q5)
#   Compartilhador impulsivo -> confia nas redes (Q4) + compartilha
#                               tudo (Q6) + nunca verifica (Q3)
#   Cético de baixa circulação -> não acredita, não verifica, não muda
#                               e não compartilha (desengajado)
#   Reativo emocional        -> emoção máxima (Q7), resto intermediário
#
# Ajuste feito a partir do validar_modelo.py:
#   - Verificador crítico e Cético eram o par mais próximo (2,78) e
#     se fundiam com k=5. O Cético agora quase não verifica (Q3=2)
#     e é fechado (Q5=2); o Verificador confia um pouco mais nas
#     redes (Q4=2,5).
#   - Compartilhador e Reativo emocional estavam próximos (3,39):
#     o Compartilhador ficou com emoção moderada (Q7=3,5) e o
#     Reativo confia menos nas redes (Q4=2) e compartilha menos (Q6=3).
#   Resultado: menor distância entre perfis 3,74 e k=6 passou a ser
#   o melhor k pela silhouette.
#

PERFIS = {
    'Verificador crítico':        [2.0, 2.0, 5.0, 2.5, 4.5, 1.5, 3.0],
    'Crente resistente':          [5.0, 5.0, 1.5, 4.5, 1.0, 3.0, 3.0],
    'Crente flexível':            [4.5, 4.5, 4.0, 3.0, 5.0, 2.0, 2.5],
    'Compartilhador impulsivo':   [3.0, 3.0, 1.0, 5.0, 3.5, 5.0, 3.5],
    'Cético de baixa circulação': [1.5, 1.5, 2.0, 1.0, 2.0, 1.0, 1.5],
    'Reativo emocional':          [4.0, 3.5, 2.5, 2.0, 3.5, 3.0, 5.0],
}

nomes_perfis = list(PERFIS.keys())

mapa_clusters = dict(enumerate(nomes_perfis))


# ============================================================
# 3. CENÁRIOS (QUANTIDADE DE RESPOSTAS POR PERFIL)
# ============================================================
#
# Edite os números para simular outros desbalanceamentos.
#

CENARIOS = {
    'balanceado': {nome: 100 for nome in nomes_perfis},
    'desbalanceado': {
        'Verificador crítico':        50,
        'Crente resistente':          120,
        'Crente flexível':            80,
        'Compartilhador impulsivo':   250,
        'Cético de baixa circulação': 40,
        'Reativo emocional':          180,
    },
}

# ============================================================
# 4. FUNÇÃO PARA GERAR RESPOSTAS INTEIRAS DE 1 A 5
# ============================================================

def gerar_perfil(medias, n, ruido=0.7):

    # Gerar valores ao redor das médias
    dados = np.random.normal(
        loc=medias,
        scale=ruido,
        size=(n, len(medias))
    )

    # Arredondar para o inteiro mais próximo e limitar de 1 a 5
    dados = np.rint(dados).clip(1, 5).astype(int)

    return dados


# ============================================================
# 5. FUNÇÃO PARA GERAR O DATAFRAME DE UM CENÁRIO
# ============================================================

def gerar_dados(quantidades, ruido=0.7):

    blocos = []

    for nome, medias in PERFIS.items():

        bloco = pd.DataFrame(
            gerar_perfil(medias, quantidades[nome], ruido),
            columns=features
        )

        bloco['perfil_original'] = nome

        blocos.append(bloco)

    df = pd.concat(blocos, ignore_index=True)

    # --------------------------------------------------------
    # Q8 — PERGUNTA INVERTIDA
    # --------------------------------------------------------
    #
    # Respondente coerente: o oposto da Q4, com o mesmo ruído.
    #

    df[ITEM_INVERTIDO] = (
        np.rint(np.random.normal(6 - df['q4_confianca_redes'], ruido))
        .clip(1, 5)
        .astype(int)
    )

    # --------------------------------------------------------
    # RESULTADO DA VERIFICAÇÃO
    # --------------------------------------------------------
    #
    # Essa informação vem de fora do questionário.
    #

    df['resultado_verificacao'] = np.random.choice(
        ['VERDADEIRA', 'FALSA'],
        size=len(df)
    )

    # --------------------------------------------------------
    # Q9 — MUDANÇA DE OPINIÃO
    # --------------------------------------------------------
    #
    # Resposta inteira de 1 a 5. NÃO entra no K-Means.
    #
    # 1 = pouca/nenhuma mudança
    # 5 = mudança muito grande
    #
    # HIPÓTESE SIMULADA: só há o que mudar quando a verificação
    # contradiz a crença inicial (Q1). Nesse caso, a mudança
    # acompanha a abertura declarada (Q5). Quando confirma,
    # a mudança fica baixa. Com dados reais, isto é o que se
    # quer TESTAR, não assumir.
    #

    contradiz = (
        ((df['q1_crenca_inicial'] >= 4) & (df['resultado_verificacao'] == 'FALSA')) |
        ((df['q1_crenca_inicial'] <= 2) & (df['resultado_verificacao'] == 'VERDADEIRA'))
    )

    q9_base = np.where(contradiz, df['q5_abertura_mudanca'], 1.5)

    df['q9_mudanca_opiniao'] = (
        np.rint(np.random.normal(q9_base, 0.7))
        .clip(1, 5)
        .astype(int)
    )

    return df


# ============================================================
# 6. BIC / AIC EM RESPOSTAS INTEIRAS
# ============================================================

def desquantizar(X_scaled, scaler, seed=0):
    """
    Soma ruído uniforme de ±0,5 ponto (na escala 1–5) às respostas.

    Usado SÓ para calcular BIC/AIC. As respostas são inteiras, e
    o GMM consegue colocar componentes "em cima" dos valores
    inteiros: a verossimilhança sempre melhora com mais componentes
    e o BIC nunca para de cair. Espalhar cada resposta dentro do
    seu intervalo (ex.: 4 -> entre 3,5 e 4,5) desfaz isso.
    """

    rng = np.random.default_rng(seed)

    return X_scaled + rng.uniform(-0.5, 0.5, X_scaled.shape) / scaler.scale_

