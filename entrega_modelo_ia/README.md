# Entrega do modelo de IA: BKT

Entrega do primeiro desafio (Residência em IA, ELD/UnB): o modelo de *Bayesian Knowledge Tracing* que estima o domínio do jogador em cada habilidade de checagem de notícias (`SOURCE`, `EVIDENCE`, `CONTEXT`, `VISUAL`).

| Caminho | Conteúdo |
|---|---|
| `RELATORIO_TECNICO.md` / `.pdf` | Relatório técnico: funcionamento do BKT, dados, treino, critérios, métricas, desafios e aprendizados |
| `notebooks/bkt_modelo.ipynb` | Notebook executado: carrega, treina, avalia, salva e usa o modelo |
| `modelos/bkt_modelo.pkl` | Modelo treinado (dicionário com parâmetros por habilidade, métricas e metadados) |
| `src/bkt_engine.py` | Motor BKT (cópia de `backend/app/bkt/engine.py`) |
| `dados/respostas_teste_local.csv` | 10 respostas reais de teste, sem identificação de usuário |
| `figuras/` | Gráficos gerados pelo notebook |

## Como executar

```bash
cd entrega_modelo_ia
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook notebooks/bkt_modelo.ipynb   # Kernel > Restart & Run All
```

A execução leva menos de 15 segundos e é determinística (seed `20261009`). O notebook regrava `modelos/bkt_modelo.pkl` e `figuras/`.

## Usar o modelo salvo

```python
import pickle, sys
sys.path.insert(0, 'src')
from bkt_engine import BKTEngine

modelo = pickle.load(open('modelos/bkt_modelo.pkl', 'rb'))   # carregue só arquivos confiáveis
motor = BKTEngine(**modelo['parameters']['VISUAL'])
dominio = modelo['parameters']['VISUAL']['p_init']
dominio = motor.update(dominio, correct=True)
```

**Atenção:** os parâmetros foram calibrados com dados **simulados** (`modelo['data']['is_synthetic'] == True`). Eles validam o método; antes de usá-los em produção, recalibre com respostas reais.
