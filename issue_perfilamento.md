# [Feature] Algoritmo de Agrupamento/Perfilamento de Usuários (GMM / K-Means)

## Objetivo

Implementar o serviço de perfilamento de usuários baseado em **Gaussian Mixture Model (GMM)**, com **K-Means como baseline**, usando como entrada as respostas do questionário de verificação de notícias.

O objetivo é categorizar o comportamento do usuário diante de uma notícia em **6 perfis**:

| Cluster | Perfil | Traço dominante |
|---|---|---|
| 0 | Verificador crítico | Verifica sempre (Q3) e é aberto a mudar de opinião (Q5) |
| 1 | Crente resistente | Crença máxima na notícia e fechado a mudar (Q5) |
| 2 | Crente flexível | Crença alta, mas verifica e muda de opinião |
| 3 | Compartilhador impulsivo | Confia nas redes (Q4), compartilha tudo (Q6), não verifica (Q3) |
| 4 | Cético de baixa circulação | Não acredita, não verifica, não compartilha (desengajado) |
| 5 | Reativo emocional | Emoção máxima (Q7), resto intermediário |

## Dados de entrada

O questionário tem **9 perguntas** (escala Likert de 1 a 5), salvas no campo `answers` do feedback (`POST /api/verifications/{verification_id}/feedback`):

```json
{
  "answers": {
    "q1": 4, "q2": 4, "q3": 2, "q4": 4, "q5": 3,
    "q6": 4, "q7": 4, "q8": 2, "q9": 3
  }
}
```

| Chave | Pergunta | Uso no modelo |
|---|---|---|
| q1 | Crença inicial na notícia | feature |
| q2 | Credibilidade | feature |
| q3 | Hábito de verificar | feature |
| q4 | "Eu confio nas notícias que recebo pelas redes sociais." | feature |
| q5 | Abertura para mudar de opinião | feature |
| q6 | Probabilidade de compartilhar | feature |
| q7 | Emoção provocada pela notícia | feature |
| q8 | "Quando uma notícia chega pelo WhatsApp ou Instagram, eu desconfio dela." | **invertida da q4**: corrige o viés de resposta, não é feature |
| q9 | Mudança de opinião depois da verificação | **não entra no modelo** (respondida depois) |

- **Entrada do modelo:** X = [q1, …, q8] ∈ ℝ⁸, em ordem fixa.
- **Features do GMM/K-Means:** [q1, …, q7] ∈ ℝ⁷, depois da correção de aquiescência.

A ordem na tela é diferente (Q3, Q4, Q1, Q2, Q5, Q6, Q7, Q8) para deixar 5 perguntas entre as duas afirmações opostas (Q4 e Q8). O modelo sempre recebe Q1..Q8.

## Especificação técnica

### Pré-processamento

- **Validação:** registros com resposta faltando, nula ou fora do intervalo 1–5 (inclusive decimais, texto e booleanos) são **ignorados**. O questionário é salvo, mas não gera perfil.
- **Correção de aquiescência:** quem responde com coerência tem Q4 + Q8 ≈ 6. O desvio `(Q4 + Q8 − 6) / 2` mede a tendência de concordar (ou discordar) de tudo e é descontado de Q1..Q7.
- **Padronização:** `StandardScaler` (média 0, desvio 1), dentro de um `Pipeline` junto com o modelo.

### Modelagem

- **Principal:** GMM (soft clustering, probabilidade de cada perfil).
- **Baseline:** K-Means, salvo junto e retornado para comparação.
- **K = 6**, escolhido pela validação (melhor K pela silhouette no K-Means e pelo BIC no GMM, em dados balanceados).
- **Covariância:** `'full'` e `'diag'` são comparadas pelo BIC no treino; a escolhida foi **`'diag'`**.
- **Inicialização:** GMM e K-Means começam das médias esperadas de cada perfil, então o cluster *i* é sempre o perfil *i* (rótulos estáveis entre treinos).

### Dados de treino

Ainda não há respostas reais suficientes. O modelo é treinado com **dados sintéticos** gerados a partir das médias esperadas de cada perfil (720 respostas, cenário desbalanceado, semente 42).

Resultados (treino / dados novos balanceados):

| | GMM | K-Means |
|---|---|---|
| Acurácia | 97,1% / 98,0% | 98,2% / 98,3% |

⚠️ Essas métricas medem **coerência**, não validade com pessoas reais: os dados saem das mesmas médias usadas para definir os perfis. Validar com respostas reais é trabalho futuro.

### Saída do modelo

O perfil é salvo na tabela `profiles` (um por verificação):

```json
{
  "verification_id": "123",
  "profile_result": {
    "assigned_cluster": 5,
    "cluster_label": "Reativo emocional",
    "probabilities": {
      "cluster_0": 0.0, "cluster_1": 0.0004, "cluster_2": 0.0001,
      "cluster_3": 0.4676, "cluster_4": 0.0, "cluster_5": 0.532
    },
    "details": {
      "confidence": 0.532,
      "second_label": "Compartilhador impulsivo",
      "kmeans_label": "Compartilhador impulsivo",
      "acquiescence": 0.0,
      "alerts": ["resposta entre 'Reativo emocional' e 'Compartilhador impulsivo'"]
    },
    "processed_at": "2026-09-30T10:00:00"
  }
}
```

`details` traz os alertas de qualidade da resposta:

- todas as respostas iguais;
- Q4 e Q8 contraditórias (viés de resposta);
- resposta fora do padrão de qualquer perfil;
- resposta entre dois perfis (maior probabilidade < 0,6).

`processed_at` é gravado em UTC, sem o sufixo `Z`.

## Endpoints

| Método | Rota | O que faz |
|---|---|---|
| `POST` | `/api/verifications/{verification_id}/feedback` | Salva o questionário e **calcula o perfil na hora** (hook síncrono) |
| `GET` | `/api/verifications/{verification_id}/profile` | Retorna o perfil salvo (404 se não houver) |
| `POST` | `/api/verifications/{verification_id}/profile` | Recalcula a partir do último questionário (422 se incompleto) |

Falha no cálculo do perfil nunca derruba o salvamento do questionário: o erro vai para o log.

## Onde está

- `backend/app/ml/perfil.py`: validação, correção, inferência e alertas (usado em produção).
- `backend/app/ml/modelo_perfis.joblib`: modelo treinado, com versão do scikit-learn, data, semente e métricas.
- `backend/app/services/profile.py` e `backend/app/routes/profile.py`: serviço, hook e rotas.
- `treinamento/`: treino (`treinar.py`), perfis e dados sintéticos (`perfis.py`), validação (`validar_modelo.py`), matriz de confusão (`matriz_confusao.py`). O passo a passo está em `treinamento/README.md`.

## Critérios de aceitação (Definition of Done)

- [x] Módulo Python com padronização, treino e inferência (scikit-learn; `StandardScaler` + GMM, K-Means como baseline).
- [x] Endpoint/função para calcular e atribuir o perfil a partir do `verification_id`.
- [x] Testes unitários validando o vetor de entrada **X ∈ ℝ⁸** (7 features + q8 invertida) e a geração das probabilidades (`backend/tests/test_profile.py`).
- [x] Mapeamento dos clusters para rótulos interpretáveis (6 perfis, testados com respostas típicas de cada um).
- [x] Hook síncrono executado após o salvamento do questionário.
- [x] Escolha de K e da covariância justificada por silhouette e BIC/AIC (`treinamento/validar_modelo.py`).
- [ ] Validar os perfis com respostas reais (piloto e/ou especialistas) e retreinar.
