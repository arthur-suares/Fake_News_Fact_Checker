import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.pipeline import Pipeline
from sklearn.metrics import adjusted_rand_score, silhouette_score
import joblib


# ============================================================
# 1. CONFIGURAÇÕES
# ============================================================

np.random.seed(42)

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 250)


# ============================================================
# 2. PERGUNTAS UTILIZADAS PARA DEFINIR O PERFIL
# ============================================================
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
# Q4 - Com que frequência você confia em informações
#      recebidas pelas redes sociais?
#
# Q6 - Se a verificação indicar o oposto do que você acha,
#      o quão aberto você está para mudar de opinião?
#
# Q7 - Qual a probabilidade de você compartilhar essa notícia?
#
# Q8 - O quanto o assunto dessa notícia mexeu com suas emoções?
#
# Q5 NÃO entra no K-Means.
# Ela é respondida depois da verificação.
#


features = [
    'q1_crenca_inicial',
    'q2_credibilidade',
    'q3_verificacao',
    'q4_confianca_redes',
    'q6_abertura_mudanca',
    'q7_compartilhamento',
    'q8_emocao'
]


# ============================================================
# 3. OS 6 PERFIS (MÉDIAS ESPERADAS DAS RESPOSTAS)
# ============================================================
#
# A ordem deste dicionário define o cluster_id:
# cluster 0 = Verificador crítico, cluster 1 = Crente resistente...
#
# Ordem das médias: Q1, Q2, Q3, Q4, Q6, Q7, Q8
#

PERFIS = {
    'Verificador crítico':        [2.0, 2.0, 5.0, 2.0, 5.0, 1.5, 2.5],
    'Crente resistente':          [5.0, 5.0, 1.5, 4.5, 1.5, 4.5, 4.0],
    'Crente flexível':            [4.5, 4.5, 4.0, 3.0, 5.0, 2.5, 3.0],
    'Compartilhador impulsivo':   [4.5, 4.5, 1.5, 4.0, 2.0, 5.0, 5.0],
    'Cético de baixa circulação': [2.0, 2.0, 3.5, 1.0, 4.0, 1.0, 1.5],
    'Reativo emocional':          [4.0, 4.0, 2.0, 3.5, 3.0, 4.0, 5.0],
}

nomes_perfis = list(PERFIS.keys())

mapa_clusters = dict(enumerate(nomes_perfis))


# ============================================================
# 4. CENÁRIOS (QUANTIDADE DE RESPOSTAS POR PERFIL)
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

# Cenário usado para treinar o modelo que será salvo
CENARIO_FINAL = 'desbalanceado'


# ============================================================
# 5. FUNÇÃO PARA GERAR RESPOSTAS INTEIRAS DE 1 A 5
# ============================================================

def gerar_perfil(medias, n):

    # Gerar valores ao redor das médias
    dados = np.random.normal(
        loc=medias,
        scale=0.7,
        size=(n, len(medias))
    )

    # Arredondar para o inteiro mais próximo e limitar de 1 a 5
    dados = np.rint(dados).clip(1, 5).astype(int)

    return dados


# ============================================================
# 6. FUNÇÃO PARA GERAR O DATAFRAME DE UM CENÁRIO
# ============================================================

def gerar_dados(quantidades):

    blocos = []

    for nome, medias in PERFIS.items():

        bloco = pd.DataFrame(
            gerar_perfil(medias, quantidades[nome]),
            columns=features
        )

        bloco['perfil_original'] = nome

        blocos.append(bloco)

    df = pd.concat(blocos, ignore_index=True)

    # --------------------------------------------------------
    # Q5 — MUDANÇA DE OPINIÃO
    # --------------------------------------------------------
    #
    # Resposta inteira de 1 a 5. NÃO entra no K-Means.
    #
    # 1 = pouca/nenhuma mudança
    # 5 = mudança muito grande
    #

    df['q5_mudanca_opiniao'] = np.random.randint(
        1,
        6,
        size=len(df)
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

    return df


# ============================================================
# 7. FUNÇÃO PARA TREINAR E AVALIAR O K-MEANS
# ============================================================

def treinar_e_avaliar(nome_cenario):

    print("\n" + "#" * 70)
    print(f"CENÁRIO: {nome_cenario.upper()}")
    print("#" * 70)

    df = gerar_dados(CENARIOS[nome_cenario])

    # --------------------------------------------------------
    # NORMALIZAÇÃO
    # --------------------------------------------------------

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(df[features])

    # --------------------------------------------------------
    # K-MEANS COM CENTROIDES INICIAIS = MÉDIAS DOS PERFIS
    # --------------------------------------------------------
    #
    # Começar das médias dos perfis faz com que o cluster i
    # corresponda sempre ao perfil i, mesmo com desbalanceamento.
    #

    centroides_iniciais = scaler.transform(
        pd.DataFrame(list(PERFIS.values()), columns=features)
    )

    kmeans = KMeans(
        n_clusters=len(PERFIS),
        init=centroides_iniciais,
        n_init=1,
        random_state=42
    )

    kmeans.fit(X_scaled)

    df['cluster_id'] = kmeans.labels_
    df['perfil_previsto'] = df['cluster_id'].map(mapa_clusters)

    # --------------------------------------------------------
    # SANIDADE: ALGUM CLUSTER "FUGIU" PARA OUTRO PERFIL?
    # --------------------------------------------------------

    distancias = np.linalg.norm(
        kmeans.cluster_centers_[:, None, :] - centroides_iniciais[None, :, :],
        axis=2
    )

    for i, mais_proximo in enumerate(distancias.argmin(axis=1)):

        if mais_proximo != i:
            print(
                f"\nAVISO: o cluster de '{mapa_clusters[i]}' terminou "
                f"mais perto de '{mapa_clusters[mais_proximo]}'."
            )

    # --------------------------------------------------------
    # DISTRIBUIÇÃO DOS CLUSTERS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DISTRIBUIÇÃO: REAL x PREVISTA")
    print("=" * 70)

    distribuicao = pd.DataFrame({
        'real': df['perfil_original'].value_counts(),
        'previsto': df['perfil_previsto'].value_counts(),
    }).reindex(nomes_perfis).fillna(0).astype(int)

    print(distribuicao)

    # --------------------------------------------------------
    # CENTROIDES (ESCALA 1–5)
    # --------------------------------------------------------

    centroides_df = pd.DataFrame(
        scaler.inverse_transform(kmeans.cluster_centers_),
        columns=features,
        index=nomes_perfis
    )

    print("\n" + "=" * 70)
    print("CENTROIDES DOS CLUSTERS")
    print("=" * 70)

    print(centroides_df.round(2))

    # --------------------------------------------------------
    # PERFIL ORIGINAL x PERFIL PREVISTO
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PERFIL ORIGINAL x PERFIL PREVISTO")
    print("=" * 70)

    tabela_cruzada = pd.crosstab(
        df['perfil_original'],
        df['perfil_previsto']
    ).reindex(index=nomes_perfis, columns=nomes_perfis, fill_value=0)

    print(tabela_cruzada)

    # --------------------------------------------------------
    # MÉTRICAS
    # --------------------------------------------------------
    #
    # Recall por perfil: % das respostas de cada perfil que
    # caíram no cluster certo. Mostra se perfis pequenos estão
    # sendo "engolidos" pelos grandes.
    #

    recall = (
        (df['perfil_original'] == df['perfil_previsto'])
        .groupby(df['perfil_original'])
        .mean()
        .reindex(nomes_perfis)
    )

    ari = adjusted_rand_score(df['perfil_original'], df['perfil_previsto'])
    silhueta = silhouette_score(X_scaled, df['cluster_id'])

    print("\n" + "=" * 70)
    print("MÉTRICAS")
    print("=" * 70)

    print("Recall por perfil:")
    print((recall * 100).round(1).astype(str) + '%')
    print(f"\nAdjusted Rand Index: {ari:.3f}")
    print(f"Silhouette:          {silhueta:.3f}")

    metricas = {'ARI': ari, 'Silhouette': silhueta}
    metricas.update({f'Recall {nome}': valor for nome, valor in recall.items()})

    return df, scaler, kmeans, metricas


# ============================================================
# 8. TREINAR OS CENÁRIOS
# ============================================================

resultados = {
    nome: treinar_e_avaliar(nome)
    for nome in CENARIOS
}


# ============================================================
# 9. COMPARAÇÃO ENTRE CENÁRIOS
# ============================================================

print("\n" + "#" * 70)
print("COMPARAÇÃO ENTRE CENÁRIOS")
print("#" * 70)

comparacao = pd.DataFrame({
    nome: resultado[3]
    for nome, resultado in resultados.items()
})

print(comparacao.round(3))


# ============================================================
# 10. ANÁLISES DO CENÁRIO FINAL
# ============================================================

df, scaler, kmeans, _ = resultados[CENARIO_FINAL]

print("\n" + "#" * 70)
print(f"ANÁLISES DO CENÁRIO FINAL: {CENARIO_FINAL.upper()}")
print("#" * 70)


# ============================================================
# 11. MÉDIAS POR PERFIL PREVISTO
# ============================================================

print("\n" + "=" * 70)
print("MÉDIAS DAS RESPOSTAS POR PERFIL PREVISTO")
print("=" * 70)

medias_clusters = (
    df.groupby('perfil_previsto')[features]
    .mean()
    .reindex(nomes_perfis)
    .round(2)
)

print(medias_clusters)


# ============================================================
# 12. Q5 — MUDANÇA DE OPINIÃO POR PERFIL
# ============================================================

print("\n" + "=" * 70)
print("Q5 — MUDANÇA DE OPINIÃO POR PERFIL")
print("=" * 70)

q5_por_cluster = (
    df.groupby('perfil_previsto')['q5_mudanca_opiniao']
    .mean()
    .reindex(nomes_perfis)
    .round(2)
)

print(q5_por_cluster)


# ============================================================
# 13. Q5 x RESULTADO DA VERIFICAÇÃO
# ============================================================

print("\n" + "=" * 70)
print("Q5 x RESULTADO DA VERIFICAÇÃO")
print("=" * 70)

q5_resultado = (
    df.groupby('resultado_verificacao')
    ['q5_mudanca_opiniao']
    .mean()
    .round(2)
)

print(q5_resultado)


# ============================================================
# 14. PERFIL x RESULTADO x Q5
# ============================================================

print("\n" + "=" * 70)
print("PERFIL x RESULTADO DA VERIFICAÇÃO x Q5")
print("=" * 70)

analise_completa = (
    df.groupby(
        ['perfil_previsto', 'resultado_verificacao']
    )['q5_mudanca_opiniao']
    .agg(['count', 'mean'])
    .round(2)
)

print(analise_completa)


# ============================================================
# 15. SALVAR MODELO
# ============================================================
#
# Scaler + K-Means ficam juntos num Pipeline, então quem usar o
# modelo não precisa lembrar de normalizar antes do predict.
#

pipeline = Pipeline([
    ('scaler', scaler),
    ('kmeans', kmeans)
])

joblib.dump(
    {
        'pipeline': pipeline,
        'features': features,
        'mapa_clusters': mapa_clusters,
    },
    'modelo_perfis.joblib'
)


# ============================================================
# 16. SALVAR DADOS SINTÉTICOS
# ============================================================

df.to_csv(
    'respostas_sinteticas.csv',
    index=False
)


# ============================================================
# 17. EXEMPLO DE USO (COMO O BACKEND VAI USAR)
# ============================================================

modelo = joblib.load('modelo_perfis.joblib')

nova_resposta = pd.DataFrame(
    [[5, 5, 1, 4, 2, 5, 5]],
    columns=modelo['features']
)

cluster = modelo['pipeline'].predict(nova_resposta)[0]

print("\n" + "=" * 70)
print("EXEMPLO DE PREVISÃO")
print("=" * 70)

print(nova_resposta.to_string(index=False))
print(f"\nPerfil previsto: {modelo['mapa_clusters'][cluster]}")


# ============================================================
# 18. FINAL
# ============================================================

print("\n" + "=" * 70)
print("MODELO SALVO COM SUCESSO!")
print("=" * 70)

print("\nArquivos gerados:")
print("- modelo_perfis.joblib")
print("- respostas_sinteticas.csv")
