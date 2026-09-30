# Treinamento do modelo de perfis

Scripts que geram e validam o modelo usado pela API para classificar o
leitor em um dos 6 perfis, a partir do questionário aplicado (Q1..Q8, escala 1–5).

O código de **classificação** (usado em produção) fica no backend, em
`backend/app/ml/perfil.py`. Esta pasta só **treina** e **avalia**. Os scripts
importam o mesmo código do backend via `classificador.py`, então treino e API
nunca divergem.

## Estrutura

| Arquivo | O que faz |
| ------- | --------- |
| `perfis.py` | Os 6 perfis (médias esperadas), cenários e o gerador de respostas sintéticas. Edite aqui para mudar os perfis. |
| `treinar.py` | Treina GMM (principal) + K-Means (baseline) e salva `backend/app/ml/modelo_perfis.joblib`. |
| `validar_modelo.py` | Testes de coerência e robustez: casos-gabarito, ruído, vícios de resposta, escolha de k, alertas. |
| `matriz_confusao.py` | Matriz de confusão (treino e dados novos) em `relatorios/matriz_confusao.png`. |
| `testar_perfil.py` | Classifica respostas digitadas no terminal. |
| `classificador.py` | Atalho que importa `backend/app/ml/perfil.py`. |
| `dados/respostas_sinteticas.csv` | Dados do cenário usado no treino (gerado por `treinar.py`). |

## Ambiente

Use as mesmas versões do backend. O `scikit-learn` precisa ser **igual** ao
fixado em `backend/requirements.txt`, senão o modelo salvo pode não carregar na API.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r treinamento/requirements.txt
```

## Fluxo para atualizar o modelo

```bash
cd treinamento

python treinar.py            # 1. treina e atualiza o modelo da API
python validar_modelo.py     # 2. valida (resumo no final: tudo OK?)
python matriz_confusao.py    # 3. matriz de confusão
cd ../backend && pytest      # 4. a API continua funcionando
```

Se algo piorou, volte o modelo anterior com
`git checkout backend/app/ml/modelo_perfis.joblib treinamento/dados/`.

Para experimentar sem tocar no modelo da API, use
`python treinar.py --saida /tmp/teste.joblib`. Esse comando também regrava
`dados/respostas_sinteticas.csv`. `validar_modelo.py` e `matriz_confusao.py`
sempre avaliam o modelo da API.

O treino é determinístico (semente 42): rodar `treinar.py` sem mudar
`perfis.py` gera o mesmo modelo.

## Salvaguardas

- **Acurácia mínima:** `treinar.py` não salva o modelo se a acurácia do GMM no
  cenário final ficar abaixo de `ACURACIA_MINIMA` (0,90).
- **Metadados no artefato:** o `.joblib` guarda a versão do scikit-learn, a data
  do treino, o cenário, a semente e as métricas.
- **Checagem na API:** `carregar_modelo()` recusa um modelo cujas entradas não
  batem com as do questionário. Se a versão do scikit-learn instalada for
  diferente da usada no treino, registra um aviso no log.

## Limitação

Os dados são **sintéticos**, gerados a partir das próprias médias de `PERFIS`.
As métricas (acurácia ~97%) medem a coerência do modelo, não se os perfis
existem em pessoas reais. O próximo passo é validar com respostas reais
coletadas pela API.
