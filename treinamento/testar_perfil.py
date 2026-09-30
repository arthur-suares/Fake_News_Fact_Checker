"""
Teste do modelo de perfis via terminal.

Formato da entrada (separado por vírgula ou espaço):

    Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, V ou F, Q9

    - Q1..Q7 : respostas inteiras de 1 a 5
    - Q8     : "Quando uma notícia chega pelo WhatsApp ou Instagram,
               eu desconfio dela." (invertida da Q4; usada para
               corrigir quem concorda ou discorda de tudo)

    Textos completos: PERGUNTAS em classificador.py.
    - V ou F : resultado da verificação (V = verdadeira, F = falsa)
    - Q9     : mudança de opinião depois da verificação (1 a 5)

Uso:

    python testar_perfil.py                      # modo interativo (uma linha)
    python testar_perfil.py --perguntas          # modo guiado (como na tela)
    python testar_perfil.py 5,5,1,4,2,5,5,2,F,3  # uma resposta direto
"""

import sys
from pathlib import Path

import joblib
import pandas as pd

from classificador import CAMINHO_MODELO, ORDEM_EXIBICAO, PERGUNTAS, classificar


PASTA = Path(__file__).resolve().parent

FORMATO = "Q1,Q2,Q3,Q4,Q5,Q6,Q7,Q8,V/F,Q9"

RESULTADOS = {'V': 'VERDADEIRA', 'F': 'FALSA'}


# ============================================================
# 1. CARREGAR MODELO
# ============================================================

modelo = joblib.load(CAMINHO_MODELO)

entradas = modelo['entradas']


# ============================================================
# 2. LER E VALIDAR A ENTRADA
# ============================================================

def ler_entrada(texto):

    partes = texto.replace(',', ' ').replace('[', ' ').replace(']', ' ').split()

    if len(partes) != 10:
        raise ValueError(
            f"esperado 10 valores ({FORMATO}), recebido {len(partes)}."
        )

    *respostas, resultado, q9 = partes

    try:
        respostas = [int(r) for r in respostas]
        q9 = int(q9)
    except ValueError:
        raise ValueError("Q1..Q9 devem ser números inteiros de 1 a 5.")

    if not all(1 <= r <= 5 for r in respostas + [q9]):
        raise ValueError("Q1..Q9 devem estar entre 1 e 5.")

    resultado = resultado.upper()

    if resultado not in RESULTADOS:
        raise ValueError("o resultado da verificação deve ser V ou F.")

    return respostas, RESULTADOS[resultado], q9


# ============================================================
# 3. PREVER O PERFIL
# ============================================================

def prever(respostas, resultado, q9):

    entrada = pd.DataFrame([respostas], columns=entradas)

    classificacao = classificar(modelo, respostas)
    perfil = classificacao['cluster_label']
    detalhes = classificacao['details']

    # Mesma regra usada em perfis.py (gerar_dados) para Q9
    q1 = respostas[0]
    contradiz = (
        (q1 >= 4 and resultado == 'FALSA') or
        (q1 <= 2 and resultado == 'VERDADEIRA')
    )

    print("\n" + "=" * 50)
    print(entrada.to_string(index=False))
    print("-" * 50)
    print(f"Resultado da verificação: {resultado}")
    print(f"Verificação contradiz Q1: {'sim' if contradiz else 'não'}")
    print(f"Q9 (mudança de opinião):  {q9}")
    print("-" * 50)
    print(f"PERFIL DO USUÁRIO: {perfil}")
    print(f"Probabilidade:     {detalhes['confidence']:.0%}"
          f"  (2º mais provável: {detalhes['second_label']})")
    print(f"K-Means (baseline): {detalhes['kmeans_label']}")
    print(f"Aquiescência:      {detalhes['acquiescence']:+.1f}"
          f"  (0 = Q4 e Q8 coerentes)")

    print("-" * 50)

    for i, p in enumerate(classificacao['probabilities'].values()):
        print(f"  {modelo['mapa_clusters'][i]:<28} {p:>6.1%}")

    for alerta in detalhes['alerts']:
        print(f"ALERTA: {alerta}")

    print("=" * 50)

    return perfil


# ============================================================
# 4. MODO GUIADO (COMO O USUÁRIO VÊ NA TELA)
# ============================================================
#
# Faz as perguntas na ORDEM_EXIBICAO, com o texto real, e monta
# as respostas na ordem que o modelo espera (Q1..Q8).
#

def perguntar_nota(chave):

    texto, (minimo, maximo) = PERGUNTAS[chave]

    while True:

        resposta = input(f"\n{texto}\n  (1 = {minimo} ... 5 = {maximo})\n> ").strip()

        if resposta in {'1', '2', '3', '4', '5'}:
            return int(resposta)

        print("Responda com um número de 1 a 5.")


def modo_guiado():

    print("Responda de 1 a 5. (Ctrl+C encerra)")

    respostas = {chave: perguntar_nota(chave) for chave in ORDEM_EXIBICAO}

    while True:

        resultado = input("\nResultado da verificação (V ou F)\n> ").strip().upper()

        if resultado in RESULTADOS:
            break

        print("Responda V ou F.")

    q9 = perguntar_nota('q9_mudanca_opiniao')

    prever([respostas[chave] for chave in entradas], RESULTADOS[resultado], q9)


# ============================================================
# 5. EXECUÇÃO
# ============================================================

def main():

    if sys.argv[1:] == ['--perguntas']:
        try:
            modo_guiado()
        except (EOFError, KeyboardInterrupt):
            print()
        return

    if len(sys.argv) > 1:
        try:
            prever(*ler_entrada(' '.join(sys.argv[1:])))
        except ValueError as erro:
            sys.exit(f"Erro: {erro}")
        return

    print(f"Digite as respostas no formato: {FORMATO}")
    print("Exemplo: 5,5,1,4,2,5,5,2,F,3 (ENTER vazio ou 'sair' encerra)")

    while True:

        try:
            texto = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if texto.lower() in ('', 'sair'):
            break

        try:
            prever(*ler_entrada(texto))
        except ValueError as erro:
            print(f"Erro: {erro}")


if __name__ == '__main__':
    main()
