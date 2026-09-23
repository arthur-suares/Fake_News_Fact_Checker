# Análise Exploratória (EDA) — Fake News vs Notícias Verdadeiras

Esta pasta traz a análise exploratória dos dois datasets de checagens de fatos usados no projeto. Os scripts usam **pandas** e **matplotlib**. Primeiro os dados são limpos. Depois são analisados separadamente (só fakes, só verdadeiras) e em conjunto (comparações e temas).

---

## 1. Como rodar

Na raiz do projeto (`Fake_News_Fact_Checker`):

```bash
# só na primeira vez
source .venv/bin/activate
pip install -r EDA/requirements.txt

# roda a limpeza e todas as análises, em ordem
for s in EDA/0*.py; do python "$s"; done
```

Também dá para rodar um script de cada vez, por exemplo `python EDA/05_temas.py`. Os gráficos vão para `EDA/outputs/`, e cada script imprime no terminal as tabelas por trás deles.

> Se você alterar alguma regra em `00_limpeza.py`, rode esse script de novo para atualizar os dados limpos. Se a pasta `datasets/limpos/` não existir, os outros scripts rodam a limpeza sozinhos.

---

## 2. Estrutura da pasta

```
EDA/
├── analise_exploratoria.md          ← este arquivo
├── analise_exploratoria.ipynb       ← notebook com toda a análise explicada passo a passo
├── requirements.txt                 ← pandas, matplotlib, numpy
├── utils.py                         ← funções compartilhadas (carregamento, tokenização, gráficos)
├── 00_limpeza.py                    ← limpa os dados e gera datasets/limpos/
├── 01_visao_geral.py                ← os dois datasets: tamanho, nulos, duplicados, período
├── 02_analise_fakes.py              ← só fakes: palavras, origem, agências, evolução mensal
├── 03_analise_verdadeiras.py        ← só verdadeiras: palavras, autores, agências, por ano
├── 04_comparativo_fake_vs_true.py   ← comparação: tamanho, estilo, vocabulário característico
├── 05_temas.py                      ← assuntos por palavras-chave e evolução no tempo
├── datasets/
│   ├── fakes.csv                    ← ORIGINAL (nunca é alterado)
│   ├── true.csv                     ← ORIGINAL (nunca é alterado)
│   └── limpos/                      ← gerado pelo 00_limpeza.py (ignorado pelo git)
│       ├── fakes.csv
│       ├── true.csv
│       └── nao_tratados.csv         ← registros com problemas que a limpeza não resolve
└── outputs/                         ← gráficos PNG gerados pelos scripts
```

---

## 3. Os dados

| Arquivo | Linhas | `label` | Conteúdo |
|---|---|---|---|
| `fakes.csv` | 20.478 | 1 | Alegações classificadas como falsas pelas agências |
| `true.csv` | 2.720 | 0 | Alegações classificadas como verdadeiras |

Colunas: `title` (título da checagem), `text` (a alegação checada), `origin`, `url`, `label`, `publisher_name`, `publisher_site`, `date`.

Pontos importantes para interpretar os resultados:

- **As classes estão desbalanceadas**, com cerca de 7,5 fakes para cada verdadeira. Por isso as comparações usam **porcentagens**, não contagens.
- **A coluna `origin` tem significado diferente em cada dataset.** Nas fakes, indica onde o boato circulou (Facebook, WhatsApp…). Nas verdadeiras, indica quase sempre **quem fez a declaração** (políticos).
- **Há dados de Portugal.** O Polígrafo e o Observador são portugueses e respondem por boa parte das verdadeiras. Por isso aparecem palavras como "euros" e "António Costa".
- **Uma mesma URL pode ter várias alegações.** Artigos do tipo "erros e acertos do candidato X" checam várias frases, e 425 URLs aparecem nos dois datasets. Isso **não** é erro: nenhuma alegação aparece com rótulos opostos.

---

## 4. Limpeza (`00_limpeza.py`)

O script lê os originais, aplica as regras abaixo e grava o resultado em `datasets/limpos/`. **Os CSVs originais nunca são modificados.**

| Problema encontrado | Tratamento | Impacto |
|---|---|---|
| Espaços invisíveis (` `, `​`…), quebras de linha e espaços duplos | Normalizados para um espaço simples | Todos os textos |
| Aspas envolvendo o texto (`“...”`) | Removidas das bordas | ~2.870 textos |
| `text` contendo só um link | Substituído pelo `title` | 1 |
| Registros duplicados (mesmo title + text + url) | Removidos | 9 |
| `text` idêntico ao `title` | Marcado na coluna `text_igual_title`, e as análises contam as palavras só uma vez | 4.088 |
| Mesma agência com nomes diferentes ("UOL Noticias" / "UOL Notícias"; 3 nomes do Estadão + nulos; Piauí como "UOL") | Nome padronizado a partir do `publisher_site` (dicionário `PUBLISHERS`) | 14 → 12 nomes |
| Variações de `origin` (maiúsculas/minúsculas, "Utilizador de/do Facebook", "Post no/do Facebook", "Lula" / "Luiz Inácio Lula da Silva"…) | Unificadas (dicionário `ORIGENS_SINONIMOS` + grafia mais frequente) | ~1.470 → ~1.430 valores |
| `origin` com rótulos genéricos ("desinformação", "checamos") | Tornados vazios, pois não indicam a origem | ~2.100 |
| Data impossível (2005, antes de a agência existir) | Anulada (datas anteriores a 2010) | 1 |
| Data vazia, mas a URL contém a data (`/2022/09/08/`) | Recuperada da URL; a coluna `date_fonte` indica `original` ou `url` | 502 |
| `label` fora de {0, 1} | O script para com erro | Nenhum caso |


---

## 5. Módulo compartilhado (`utils.py`)

- **`carregar_fakes()`, `carregar_true()`, `carregar_combinado()`**: leem os dados limpos. A versão combinada adiciona a coluna `classe` ("Fake" / "Verdadeira"). Todas criam `texto_completo` (title + text, sem repetir quando são iguais) e `palavras_text`.
- **`tokenizar()`, `contar_palavras()`, `contar_bigramas()`**: passam o texto para minúsculas, removem links e descartam palavras muito comuns (as stopwords, que ficam na lista `STOPWORDS`). A lista inclui, além das stopwords do português, termos próprios das agências ("fact check", "boato", "erros e acertos"). Sem isso, esses termos dominariam os rankings sem dizer nada sobre o assunto.
- **`plataforma_da_origem()`**: classifica o `origin` em WhatsApp, Facebook, Twitter/X, Instagram, YouTube, TikTok, Telegram ou Kwai, com os padrões do dicionário `PLATAFORMAS`.
- **`barh()` e `salvar()`**: padronizam os gráficos (vermelho = fake, verde = verdadeira) e os salvam em `outputs/`.

---

## 6. Análises e gráficos

### 01 — Visão geral (dois datasets)
Quantidade por classe, % de nulos por coluna, duplicados e período coberto.
→ `01_visao_geral.png`

### 02 — Só fake news
- Palavras e bigramas (pares de palavras) mais frequentes → `02_fakes_palavras.png`
- Plataforma de origem e valores mais comuns de `origin` → `02_fakes_origem.png`
- Agências que mais checaram fakes → `02_fakes_publishers.png`
- Checagens por mês → `02_fakes_por_mes.png`

### 03 — Só verdadeiras
- Palavras e bigramas → `03_true_palavras.png`
- Quem mais fez declarações verdadeiras checadas, e agências → `03_true_autores_publishers.png`
- Checagens por ano → `03_true_por_ano.png`

### 04 — Comparativo fake × verdadeira
- Distribuição do nº de palavras (histograma normalizado + boxplot) → `04_tamanho_textos.png`
- Estilo de escrita: % de letras maiúsculas e nº de exclamações (só no terminal)
- Checagens por ano e classe → `04_por_ano.png`
- **Vocabulário característico** → `04_vocabulario_caracteristico.png`. Usa **log-odds com suavização**, que compara a frequência relativa de cada palavra nas duas classes. Valores altos indicam palavras muito mais típicas de uma classe do que da outra. Só entram palavras com pelo menos 20 ocorrências no total.
- Top 10 agências, em barras empilhadas por classe → `04_publishers.png`

### 05 — Temas (assuntos mais comentados)
Cada registro é classificado por **palavras-chave** (dicionário `TEMAS`), e um registro pode ter mais de um tema.
- % de registros de cada classe em cada tema → `05_temas_por_classe.png`
- Ranking de temas nas fakes → `05_temas_fakes.png`
- Evolução trimestral dos 5 principais temas de fake news → `05_temas_no_tempo.png`. O último trimestre é descartado por estar incompleto.

**Como os temas foram escolhidos:** manualmente, a partir das palavras e bigramas mais frequentes (scripts 02 e 03) e do contexto do período (eleições de 2018 e 2022, pandemia, guerra na Ucrânia). As expressões buscam pedaços de palavras em texto sem acento: por exemplo, `vacin` captura "vacina", "vacinação" e "vacinado".

---

## 7. Principais achados

- **Assuntos dominantes nas fakes:** Covid-19 (17,6% dos registros), Bolsonaro (13,9%), Lula/PT (9,5%), vacinas (9,0%) e eleições/urnas (8,9%).
- **Os temas acompanham o noticiário:** Covid explode no 2º trimestre de 2020. Vacinas crescem no fim de 2020 e em 2021. Lula e eleições sobem em 2022. Os meses com mais checagens foram outubro e novembro de 2020 (eleições municipais) e agosto de 2022 (início da campanha presidencial).
- **Nas verdadeiras, os temas mais comuns são economia, eleições e Portugal.** Isso reflete checagens de discursos de políticos, mais do que boatos.
- **Estilo de escrita:** as fakes usam mais exclamações (0,16 contra 0,01 por texto, em média) e mais letras maiúsculas (8,1% contra 6,1%).
- **Palavras mais típicas das fakes:** "eletrônicas" (urnas), "ladrão", "Adélio", "hidroxicloroquina", "MST", "mídia", "fraude".
- **Onde circulam:** entre os registros com origem identificável, o Facebook predomina, seguido do WhatsApp.

---

## 8. Limitações

- **Os temas foram definidos à mão:** 41% dos registros não caem em nenhum tema, e alguns padrões são amplos (ex.: `justica` no tema STF também captura "Ministério da Justiça").
- **Viés das fontes:** as verdadeiras vêm quase só do Polígrafo (Portugal) e da Lupa. Parte das diferenças entre as classes reflete **quais agências publicaram**, não só a natureza da notícia. Isso também deve ser considerado ao treinar um modelo com esses dados.
- **Datas:** cerca de 12% das fakes não têm data. Os gráficos temporais consideram só os registros com data.
- **Plataforma de origem:** é inferida por palavras-chave no campo `origin`, e a maioria dos registros cai em "Outros" ou "Não informado".

---
