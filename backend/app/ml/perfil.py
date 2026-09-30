"""
Perfilamento de usuários a partir do questionário.

Modelo principal: Gaussian Mixture (GMM), que dá a probabilidade de
cada perfil (soft clustering). K-Means fica salvo como baseline.
O treino está em treinamento/treinar.py (ver treinamento/README.md).

Entrada: o dicionário `answers` salvo pelo frontend, com as 8
respostas dadas ANTES da verificação (escala de 1 a 5):

    q1..q7 : perguntas do perfil
    q8     : pergunta invertida da q4 (corrige quem concorda ou
             discorda de tudo; ver corrigir_aquiescencia)

q9 (mudança de opinião, depois da verificação) pode vir junto e é
ignorada pelo modelo.

Uso:

    from app.ml.perfil import carregar_modelo, classificar, vetor_de_respostas

    modelo = carregar_modelo()
    classificar(modelo, vetor_de_respostas(answers))
"""

import logging
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn


logger = logging.getLogger(__name__)

CAMINHO_MODELO = Path(__file__).resolve().parent / 'modelo_perfis.joblib'


# ============================================================
# PERGUNTAS DO QUESTIONÁRIO
# ============================================================
#
# Fonte única dos textos (o frontend repete em lib/types.ts).
# Todas as respostas vão de 1 a 5.
#
# Q4 e Q8 são o par que mede a aquiescência. Por isso:
#   - as duas são AFIRMAÇÕES no mesmo formato (discordo ... concordo),
#     porque a tendência de concordar com tudo atua nesse formato;
#   - a Q8 fala da mesma coisa com outras palavras, para a pessoa
#     não reconhecer o par e responder em espelho de propósito.
#
# Cada chave é o nome da coluna usada no treino; CHAVES_API traz o
# nome usado no JSON `answers` (q1..q9).
#

ESCALA_CONCORDANCIA = ('Discordo totalmente', 'Concordo totalmente')

PERGUNTAS = {
    'q1_crenca_inicial':   ('Antes da verificação, você achava que a notícia era verdadeira?',
                            ('Definitivamente falsa', 'Definitivamente verdadeira')),
    'q2_credibilidade':    ('O quanto você acreditava na notícia?',
                            ('Nada', 'Totalmente')),
    'q3_verificacao':      ('Você costuma verificar informações antes de compartilhá-las?',
                            ('Nunca', 'Sempre')),
    'q4_confianca_redes':  ('Eu confio nas notícias que recebo pelas redes sociais.',
                            ESCALA_CONCORDANCIA),
    'q5_abertura_mudanca': ('Se a verificação indicar o oposto do que você acha, '
                            'o quão aberto você está para mudar de opinião?',
                            ('Nada aberto', 'Totalmente aberto')),
    'q6_compartilhamento': ('Qual a probabilidade de você compartilhar essa notícia com outras '
                            'pessoas (grupos de app, redes sociais, amigos)?',
                            ('Muito improvável', 'Muito provável')),
    'q7_emocao':           ('O quanto o assunto desta notícia mexeu com suas emoções?',
                            ('Nada', 'Muito')),
    'q8_desconfia_redes':  ('Quando uma notícia chega pelo WhatsApp ou Instagram, '
                            'eu desconfio dela.',
                            ESCALA_CONCORDANCIA),
    'q9_mudanca_opiniao':  ('Depois da verificação, sua opinião mudou?',
                            ('Não mudou', 'Mudou totalmente')),
}

CHAVES_API = {coluna: coluna.split('_')[0] for coluna in PERGUNTAS}

# Ordem em que as perguntas APARECEM na tela (antes da verificação).
# Hábitos gerais primeiro, depois a notícia, e a Q8 por último: assim
# ficam 5 perguntas entre Q4 e Q8. O modelo continua recebendo as
# respostas na ordem Q1..Q8 (modelo['entradas']); só a exibição muda.
ORDEM_EXIBICAO = [
    'q3_verificacao',
    'q4_confianca_redes',
    'q1_crenca_inicial',
    'q2_credibilidade',
    'q5_abertura_mudanca',
    'q6_compartilhamento',
    'q7_emocao',
    'q8_desconfia_redes',
]

# Maior probabilidade abaixo disso = resposta "entre dois perfis"
LIMIAR_EMPATE = 0.6

# |aquiescência| a partir da qual vale avisar (ex.: Q4=5 e Q8=5 -> 2)
LIMIAR_AQUIESCENCIA = 1

# Posições (0-based) da Q4 e da Q8 invertida dentro das 8 respostas
POSICAO_Q4 = 3
POSICAO_INVERTIDA = 7


# ============================================================
# ENTRADA
# ============================================================

# Ordem das 8 entradas do modelo (Q1..Q8): tudo menos a Q9
ENTRADAS = [coluna for coluna in PERGUNTAS if coluna != 'q9_mudanca_opiniao']


class RespostasInvalidas(ValueError):
    """Respostas incompletas ou fora da escala: o registro é ignorado."""


def vetor_de_respostas(answers, entradas=None):
    """
    Converte o JSON `answers` ({"q1": 4, ..., "q8": 2}) no vetor
    [q1..q8] que o modelo recebe. Levanta RespostasInvalidas se
    faltar alguma resposta ou se algum valor não for inteiro de 1 a 5.
    """

    entradas = entradas or ENTRADAS

    if not isinstance(answers, dict):
        raise RespostasInvalidas('answers precisa ser um objeto')

    chaves = [CHAVES_API[coluna] for coluna in entradas]

    faltando = [chave for chave in chaves if answers.get(chave) is None]

    if faltando:
        raise RespostasInvalidas(f"respostas incompletas: falta {', '.join(faltando)}")

    vetor = []

    for chave in chaves:

        valor = answers[chave]

        # bool é subclasse de int em Python; true/false não é resposta
        if isinstance(valor, bool) or not isinstance(valor, int) or not 1 <= valor <= 5:
            raise RespostasInvalidas(f'{chave} deve ser um inteiro de 1 a 5 (recebido {valor!r})')

        vetor.append(valor)

    return vetor



# ============================================================
# CORREÇÃO DE AQUIESCÊNCIA
# ============================================================

def corrigir_aquiescencia(respostas):
    """
    Recebe as 8 respostas (Q1..Q8) e devolve (Q1..Q7 corrigidas, aquiescência).

    Q8 é o oposto da Q4, então quem responde com coerência tem
    Q4 + Q8 ≈ 6. O que passar disso é viés de resposta:

        aquiescência = (Q4 + Q8 - 6) / 2

    Ex.: Q4=5 e Q8=5 -> +2 (concorda com tudo). O viés vale para
    todas as perguntas, então é descontado de Q1..Q7.
    """

    X = np.asarray(respostas, dtype=float)

    aquiescencia = (X[:, POSICAO_Q4] + X[:, POSICAO_INVERTIDA] - 6) / 2

    corrigidas = (X[:, :POSICAO_INVERTIDA] - aquiescencia[:, None]).clip(1, 5)

    colunas = (
        list(respostas.columns[:POSICAO_INVERTIDA])
        if isinstance(respostas, pd.DataFrame) else None
    )

    return pd.DataFrame(corrigidas, columns=colunas), aquiescencia


# ============================================================
# CLASSIFICAÇÃO
# ============================================================

@lru_cache(maxsize=1)
def carregar_modelo(caminho=CAMINHO_MODELO):

    modelo = joblib.load(caminho)

    # Entradas diferentes = modelo treinado para outro questionário
    if modelo['entradas'] != ENTRADAS:
        raise RuntimeError(
            f"{caminho} espera {modelo['entradas']}, mas a API envia {ENTRADAS}. "
            'Retreine com treinamento/treinar.py.'
        )

    # Modelos antigos não têm a versão salva
    versao = modelo.get('versao_sklearn')

    if versao and versao != sklearn.__version__:
        logger.warning(
            'modelo treinado com scikit-learn %s, mas o instalado é %s; '
            'fixe a versão em requirements.txt ou retreine',
            versao, sklearn.__version__,
        )

    return modelo


def classificar_lote(modelo, respostas):

    X = pd.DataFrame(np.asarray(respostas), columns=modelo['entradas'])

    corrigidas, aquiescencia = corrigir_aquiescencia(X)

    # Probabilidade de cada perfil (GMM)
    probabilidades = modelo['pipeline'].predict_proba(corrigidas)

    ordem = probabilidades.argsort(axis=1)[:, ::-1]
    linhas = np.arange(len(X))

    p1 = probabilidades[linhas, ordem[:, 0]]

    # Log-verossimilhança: muito baixa = não se parece com nenhum perfil
    verossimilhanca = modelo['pipeline'].score_samples(corrigidas)

    nomes = np.array([modelo['mapa_clusters'][i] for i in range(probabilidades.shape[1])])

    resultado = pd.DataFrame({
        'cluster': ordem[:, 0],
        'perfil': nomes[ordem[:, 0]],
        'segundo_perfil': nomes[ordem[:, 1]],
        'confianca': p1.round(3),
        'perfil_kmeans': nomes[modelo['pipeline_kmeans'].predict(corrigidas)],
        'aquiescencia': aquiescencia,
        'respostas_iguais': X.nunique(axis=1).to_numpy() == 1,
        'vies_de_resposta': np.abs(aquiescencia) >= LIMIAR_AQUIESCENCIA,
        'fora_do_padrao': verossimilhanca < modelo['limiar_verossimilhanca'],
        'entre_dois_perfis': p1 < LIMIAR_EMPATE,
    })

    resultado['tem_alerta'] = resultado[
        ['respostas_iguais', 'vies_de_resposta', 'fora_do_padrao', 'entre_dois_perfis']
    ].any(axis=1)

    resultado['probabilidades'] = list(probabilidades)

    return resultado


def classificar(modelo, respostas):
    """
    Classifica UMA pessoa (8 respostas, Q1..Q8) e devolve no formato
    de `profile_result` da issue, mais os detalhes do nosso modelo.
    """

    linha = classificar_lote(modelo, [respostas]).iloc[0]

    alertas = []

    if linha['respostas_iguais']:
        alertas.append('todas as respostas são iguais')

    if linha['vies_de_resposta']:
        tendencia = 'concordar' if linha['aquiescencia'] > 0 else 'discordar'
        alertas.append(
            f'Q4 e Q8 se contradizem: tendência a {tendencia} com tudo '
            f'(respostas corrigidas em {-linha["aquiescencia"]:+.1f})'
        )

    if linha['fora_do_padrao']:
        alertas.append('respostas não se parecem com nenhum perfil')

    if linha['entre_dois_perfis']:
        alertas.append(
            f"resposta entre '{linha['perfil']}' e '{linha['segundo_perfil']}'"
        )

    return {
        'assigned_cluster': int(linha['cluster']),
        'cluster_label': linha['perfil'],
        'probabilities': {
            f'cluster_{i}': round(float(p), 4)
            for i, p in enumerate(linha['probabilidades'])
        },
        'details': {
            'confidence': float(linha['confianca']),
            'second_label': linha['segundo_perfil'],
            'kmeans_label': linha['perfil_kmeans'],
            'acquiescence': float(linha['aquiescencia']),
            'alerts': alertas,
        },
    }
