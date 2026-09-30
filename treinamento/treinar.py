"""
Treina o modelo de perfis e salva o artefato usado pela API.

    GMM (principal) + K-Means (baseline), ambos com o StandardScaler
    num Pipeline, treinados em dados sintéticos gerados a partir de
    PERFIS (perfis.py).

Saídas:

    backend/app/ml/modelo_perfis.joblib   (ou o caminho de --saida)
    dados/respostas_sinteticas.csv        (dados do cenário final)

O modelo só é salvo se a acurácia do GMM no cenário final for pelo
menos ACURACIA_MINIMA — protege a API de uma edição quebrada em PERFIS.

Uso:

    python treinar.py                          # treina e atualiza o modelo da API
    python treinar.py --saida /tmp/teste.joblib  # treina sem tocar no modelo da API
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from classificador import CAMINHO_MODELO, classificar, corrigir_aquiescencia
from perfis import (
    CENARIOS,
    PERFIS,
    desquantizar,
    entradas,
    features,
    gerar_dados,
    mapa_clusters,
    nomes_perfis,
)


# ============================================================
# 1. CONFIGURAÇÕES
# ============================================================

SEMENTE = 42

# Arquivos gerados ficam ao lado deste script, não importa de
# onde ele seja executado.
PASTA = Path(__file__).resolve().parent

CAMINHO_DADOS = PASTA / 'dados' / 'respostas_sinteticas.csv'

# Cenário usado para treinar o modelo que será salvo
CENARIO_FINAL = 'desbalanceado'

# Abaixo disso o modelo NÃO é salvo
ACURACIA_MINIMA = 0.90

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 250)


# ============================================================
# 2. FUNÇÃO PARA TREINAR E AVALIAR GMM (PRINCIPAL) E K-MEANS (BASELINE)
# ============================================================
#
# GMM é o modelo principal: além do perfil, dá a PROBABILIDADE de
# cada perfil (soft clustering). O K-Means fica como baseline para
# comparação. Os dois começam das médias de PERFIS, então o
# componente/cluster i corresponde sempre ao perfil i.
#

TIPOS_COVARIANCIA = ('full', 'diag')


def avisar_se_fugiu(centros, centroides_iniciais, modelo):

    distancias = np.linalg.norm(
        centros[:, None, :] - centroides_iniciais[None, :, :],
        axis=2
    )

    for i, mais_proximo in enumerate(distancias.argmin(axis=1)):

        if mais_proximo != i:
            print(
                f"\nAVISO ({modelo}): '{mapa_clusters[i]}' terminou "
                f"mais perto de '{mapa_clusters[mais_proximo]}'."
            )


def treinar_e_avaliar(nome_cenario):

    print("\n" + "#" * 70)
    print(f"CENÁRIO: {nome_cenario.upper()}")
    print("#" * 70)

    df = gerar_dados(CENARIOS[nome_cenario])

    # --------------------------------------------------------
    # NORMALIZAÇÃO
    # --------------------------------------------------------

    scaler = StandardScaler()

    # Respostas já corrigidas pela aquiescência (Q4 x Q8)
    X_scaled = scaler.fit_transform(corrigir_aquiescencia(df[entradas])[0])

    centroides_iniciais = scaler.transform(
        pd.DataFrame(list(PERFIS.values()), columns=features)
    )

    # --------------------------------------------------------
    # K-MEANS (BASELINE)
    # --------------------------------------------------------

    kmeans = KMeans(
        n_clusters=len(PERFIS),
        init=centroides_iniciais,
        n_init=1,
        random_state=42
    ).fit(X_scaled)

    avisar_se_fugiu(kmeans.cluster_centers_, centroides_iniciais, 'K-Means')

    df['perfil_kmeans'] = pd.Series(kmeans.labels_).map(mapa_clusters)

    # --------------------------------------------------------
    # GMM (PRINCIPAL) — covariância escolhida pelo BIC
    # --------------------------------------------------------
    #
    # BIC e AIC: menor é melhor. O BIC pune mais parâmetros, então
    # 'full' só ganha de 'diag' se as correlações entre perguntas
    # dentro de cada perfil compensarem o custo. Calculados nos
    # dados desquantizados (ver desquantizar).
    #

    X_criterio = desquantizar(X_scaled, scaler)

    gmms = {
        tipo: GaussianMixture(
            n_components=len(PERFIS),
            covariance_type=tipo,
            means_init=centroides_iniciais,
            random_state=42
        ).fit(X_scaled)
        for tipo in TIPOS_COVARIANCIA
    }

    criterios = pd.DataFrame({
        tipo: {'BIC': g.bic(X_criterio), 'AIC': g.aic(X_criterio)}
        for tipo, g in gmms.items()
    }).T

    tipo_escolhido = criterios['BIC'].idxmin()
    gmm = gmms[tipo_escolhido]

    print("\n" + "=" * 70)
    print("GMM: BIC / AIC POR TIPO DE COVARIÂNCIA")
    print("=" * 70)
    print(criterios.round(1))
    print(f"\nEscolhido: covariance_type='{tipo_escolhido}'")

    avisar_se_fugiu(gmm.means_, centroides_iniciais, 'GMM')

    probabilidades = gmm.predict_proba(X_scaled)

    df['cluster_id'] = probabilidades.argmax(axis=1)
    df['perfil_previsto'] = df['cluster_id'].map(mapa_clusters)
    df['probabilidade'] = probabilidades.max(axis=1).round(3)

    # --------------------------------------------------------
    # DISTRIBUIÇÃO DOS CLUSTERS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DISTRIBUIÇÃO: REAL x GMM x K-MEANS")
    print("=" * 70)

    distribuicao = pd.DataFrame({
        'real': df['perfil_original'].value_counts(),
        'GMM': df['perfil_previsto'].value_counts(),
        'K-Means': df['perfil_kmeans'].value_counts(),
    }).reindex(nomes_perfis).fillna(0).astype(int)

    print(distribuicao)

    # --------------------------------------------------------
    # MÉDIAS DOS COMPONENTES DO GMM (ESCALA 1–5)
    # --------------------------------------------------------

    medias_gmm = pd.DataFrame(
        scaler.inverse_transform(gmm.means_),
        columns=features,
        index=nomes_perfis
    )

    print("\n" + "=" * 70)
    print("MÉDIAS DOS COMPONENTES DO GMM")
    print("=" * 70)

    print(medias_gmm.round(2))

    # --------------------------------------------------------
    # PERFIL ORIGINAL x PERFIL PREVISTO (GMM)
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PERFIL ORIGINAL x PERFIL PREVISTO (GMM)")
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
    # caíram no perfil certo. Mostra se perfis pequenos estão
    # sendo "engolidos" pelos grandes.
    #

    recall = (
        (df['perfil_original'] == df['perfil_previsto'])
        .groupby(df['perfil_original'])
        .mean()
        .reindex(nomes_perfis)
    )

    acuracia = (df['perfil_original'] == df['perfil_previsto']).mean()
    acuracia_kmeans = (df['perfil_original'] == df['perfil_kmeans']).mean()
    ari = adjusted_rand_score(df['perfil_original'], df['perfil_previsto'])
    ari_kmeans = adjusted_rand_score(df['perfil_original'], df['perfil_kmeans'])
    concordancia = (df['perfil_previsto'] == df['perfil_kmeans']).mean()
    silhueta = silhouette_score(X_scaled, df['cluster_id'])

    # --------------------------------------------------------
    # OS PERFIS APARECEM SOZINHOS?
    # --------------------------------------------------------
    #
    # GMM SEM começar das médias dos perfis. Se o ARI contra os
    # perfis originais continuar alto, os 6 perfis existem de fato
    # na estrutura dos dados e não são só efeito da inicialização.
    #

    gmm_livre = GaussianMixture(
        n_components=len(PERFIS),
        covariance_type=tipo_escolhido,
        n_init=5,
        random_state=42
    ).fit(X_scaled)

    ari_livre = adjusted_rand_score(df['perfil_original'], gmm_livre.predict(X_scaled))

    print("\n" + "=" * 70)
    print("MÉTRICAS")
    print("=" * 70)

    print("Recall por perfil (GMM):")
    print((recall * 100).round(1).astype(str) + '%')
    print(f"\n{'':<24}{'GMM':>8}{'K-Means':>10}")
    print(f"{'Acurácia':<24}{acuracia:>8.3f}{acuracia_kmeans:>10.3f}")
    print(f"{'Adjusted Rand Index':<24}{ari:>8.3f}{ari_kmeans:>10.3f}")
    print(f"\nConcordância GMM x K-Means: {concordancia:.3f}")
    print(f"Probabilidade média do perfil escolhido: {df['probabilidade'].mean():.3f}")
    print(f"Silhouette (GMM):           {silhueta:.3f}")
    print(f"ARI GMM sem init fixo:      {ari_livre:.3f}")

    metricas = {
        'Acurácia GMM': acuracia,
        'Acurácia K-Means': acuracia_kmeans,
        'ARI GMM': ari,
        'ARI K-Means': ari_kmeans,
        'Concordância GMM x K-Means': concordancia,
        'Probabilidade média': df['probabilidade'].mean(),
        'Silhouette': silhueta,
        'ARI sem init fixo': ari_livre,
    }
    metricas.update({f'Recall {nome}': valor for nome, valor in recall.items()})

    return {
        'df': df,
        'scaler': scaler,
        'kmeans': kmeans,
        'gmm': gmm,
        'metricas': metricas,
    }


# ============================================================
# EXECUÇÃO
# ============================================================
#
# Tudo abaixo só roda com "python treinar.py". PERFIS, features
# e gerar_dados ficam em perfis.py, que os outros scripts importam.
#

if __name__ == '__main__':

    argumentos = argparse.ArgumentParser(description='Treina o modelo de perfis.')
    argumentos.add_argument(
        '--saida', type=Path, default=CAMINHO_MODELO,
        help=f'onde salvar o modelo (padrão: {CAMINHO_MODELO})'
    )
    saida = argumentos.parse_args().saida

    np.random.seed(SEMENTE)

    # ============================================================
    # 3. TREINAR OS CENÁRIOS
    # ============================================================

    resultados = {
        nome: treinar_e_avaliar(nome)
        for nome in CENARIOS
    }


    # ============================================================
    # 4. COMPARAÇÃO ENTRE CENÁRIOS
    # ============================================================

    print("\n" + "#" * 70)
    print("COMPARAÇÃO ENTRE CENÁRIOS")
    print("#" * 70)

    comparacao = pd.DataFrame({
        nome: resultado['metricas']
        for nome, resultado in resultados.items()
    })

    print(comparacao.round(3))


    # ============================================================
    # 5. ANÁLISES DO CENÁRIO FINAL
    # ============================================================

    final = resultados[CENARIO_FINAL]

    df, scaler, kmeans, gmm = final['df'], final['scaler'], final['kmeans'], final['gmm']

    print("\n" + "#" * 70)
    print(f"ANÁLISES DO CENÁRIO FINAL: {CENARIO_FINAL.upper()}")
    print("#" * 70)


    # ============================================================
    # 6. MÉDIAS POR PERFIL PREVISTO
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
    # 7. Q9 — MUDANÇA DE OPINIÃO POR PERFIL
    # ============================================================

    print("\n" + "=" * 70)
    print("Q9 — MUDANÇA DE OPINIÃO POR PERFIL")
    print("=" * 70)

    q9_por_cluster = (
        df.groupby('perfil_previsto')['q9_mudanca_opiniao']
        .mean()
        .reindex(nomes_perfis)
        .round(2)
    )

    print(q9_por_cluster)


    # ============================================================
    # 8. Q9 x RESULTADO DA VERIFICAÇÃO
    # ============================================================

    print("\n" + "=" * 70)
    print("Q9 x RESULTADO DA VERIFICAÇÃO")
    print("=" * 70)

    q9_resultado = (
        df.groupby('resultado_verificacao')
        ['q9_mudanca_opiniao']
        .mean()
        .round(2)
    )

    print(q9_resultado)


    # ============================================================
    # 9. PERFIL x RESULTADO x Q9
    # ============================================================

    print("\n" + "=" * 70)
    print("PERFIL x RESULTADO DA VERIFICAÇÃO x Q9")
    print("=" * 70)

    analise_completa = (
        df.groupby(
            ['perfil_previsto', 'resultado_verificacao']
        )['q9_mudanca_opiniao']
        .agg(['count', 'mean'])
        .round(2)
    )

    print(analise_completa)


    # ============================================================
    # 10. SALVAR MODELO
    # ============================================================
    #
    # Scaler + modelo ficam juntos num Pipeline, então quem usar o
    # modelo não precisa lembrar de normalizar antes do predict.
    # O arquivo vai para backend/app/ml/, de onde a API carrega.
    #

    acuracia_final = final['metricas']['Acurácia GMM']

    if acuracia_final < ACURACIA_MINIMA:
        raise SystemExit(
            f"\nMODELO NÃO SALVO: acurácia do GMM {acuracia_final:.3f} < "
            f"{ACURACIA_MINIMA:.2f}. Revise PERFIS em perfis.py."
        )

    pipeline = Pipeline([
        ('scaler', scaler),
        ('gmm', gmm)
    ])

    pipeline_kmeans = Pipeline([
        ('scaler', scaler),
        ('kmeans', kmeans)
    ])

    # --------------------------------------------------------
    # LIMIAR "FORA DO PADRÃO"
    # --------------------------------------------------------
    #
    # Log-verossimilhança de cada resposta no GMM. Abaixo do
    # percentil 1 do treino, a resposta não se parece com nenhum
    # perfil (ex.: respondente aleatório). Usado em
    # backend/app/ml/perfil.py para gerar alertas.
    #

    verossimilhanca_treino = pipeline.score_samples(
        corrigir_aquiescencia(df[entradas])[0]
    )

    limiar_verossimilhanca = float(np.percentile(verossimilhanca_treino, 1))

    joblib.dump(
        {
            'pipeline': pipeline,
            'pipeline_kmeans': pipeline_kmeans,
            'features': features,
            'entradas': entradas,
            'mapa_clusters': mapa_clusters,
            'limiar_verossimilhanca': limiar_verossimilhanca,
            'covariance_type': gmm.covariance_type,
            # Rastreabilidade: o backend avisa se o scikit-learn
            # instalado for diferente do usado no treino.
            'versao_sklearn': sklearn.__version__,
            'treinado_em': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'cenario': CENARIO_FINAL,
            'semente': SEMENTE,
            'metricas': {nome: round(float(valor), 4) for nome, valor in final['metricas'].items()},
        },
        saida
    )


    # ============================================================
    # 11. SALVAR DADOS SINTÉTICOS
    # ============================================================

    df.to_csv(CAMINHO_DADOS, index=False)


    # ============================================================
    # 12. EXEMPLO DE USO (COMO O BACKEND VAI USAR)
    # ============================================================

    modelo = joblib.load(saida)

    nova_resposta = [5, 5, 1, 4, 2, 5, 5, 2]

    resultado = classificar(modelo, nova_resposta)

    print("\n" + "=" * 70)
    print("EXEMPLO DE PREVISÃO")
    print("=" * 70)

    print(f"Respostas: {nova_resposta}")
    print(f"Perfil (GMM):     {resultado['cluster_label']}")
    print(f"Perfil (K-Means): {resultado['details']['kmeans_label']}")
    print(f"Probabilidades:   {resultado['probabilities']}")
    print(f"Alertas:          {resultado['details']['alerts'] or 'nenhum'}")


    # ============================================================
    # 13. FINAL
    # ============================================================

    print("\n" + "=" * 70)
    print("MODELO SALVO COM SUCESSO!")
    print("=" * 70)

    print("\nArquivos gerados:")
    print(f"- {saida}")
    print(f"- {CAMINHO_DADOS}")
