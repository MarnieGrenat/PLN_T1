# PLN T1

Trabalho 1 de Processamento de Linguagem Natural (PUCRS): construção de um corpus de questões de
concursos de TI (subáreas **redes**, **segurança** e **sistemas**) e de um corpus de similaridade de
palavras derivado dele.

> **Uso de IA:** ver [`USO_DE_IA.md`](USO_DE_IA.md).

## Estrutura

| pasta | conteúdo |
|---|---|
| `scraper/` | coleta (web scraping) das provas e gabaritos e processamento em questões estruturadas |
| `dataset/` | corpus de questões: texto bruto, questões por subárea/ano, estatísticas e *dataset card* |
| `similaridade/` | corpus de similaridade de palavras (200 palavras, 100 pares, anotações, CSV final; item 2) e teste com spaCy, BERT e LLM (item 4, em `similaridade/topico_4/`) |
| `classificacao/` | classificação das questões por subárea (item 3), comparando BoW/TF-IDF, spaCy e BERT |

## Pipeline

```
PDFs (PCI Concursos) ──pdftotext -layout──▶ dataset/raw.zip (*.txt)
        │
        ▼  scraper/processar_dataset.py
dataset/questoes.jsonl, dataset/<subarea>/<ano>.jsonl, dataset/descartes.csv
        │
        ├──▶ scraper/estatisticas_dataset.py ──▶ dataset/ESTATISTICAS.md
        │
        ▼  similaridade/construir_pares.py  (spaCy pt_core_news_lg)
similaridade/palavras_top200.csv, similaridade/pares_{gabriela,renato}.csv
        │
        ▼  (anotação manual, escala Likert 1–5) + similaridade/avaliar_concordancia.py
similaridade/similaridade_final.csv, similaridade/CONCORDANCIA.md
```

### 1. Corpus de questões (item 1)

1. `scraper/scraper_pci.py` baixa provas e gabaritos (PDF) das listagens de cada subárea. Os PDFs
   ficam versionados em partes: `scraper/dados/pdfs_parte01.zip` a `pdfs_parte13.zip` (352 PDFs).
2. O texto foi extraído com `pdftotext -layout` e compactado em `dataset/raw.zip` (352 arquivos).
3. `scraper/processar_dataset.py` transforma o texto bruto em questões estruturadas:
   separa as colunas de cada página, remove cabeçalhos e marcas d'água, recorta a seção de
   conhecimentos específicos, separa enunciado e alternativas e junta o gabarito. Questões com
   problemas de conversão são descartadas (motivos em `dataset/descartes.csv`).
4. `scraper/estatisticas_dataset.py` gera `dataset/ESTATISTICAS.md`.

Detalhes do formato, filtros e limitações: [`dataset/README.md`](dataset/README.md).
Estatísticas: [`dataset/ESTATISTICAS.md`](dataset/ESTATISTICAS.md).

### 2. Corpus de similaridade de palavras (item 2)

`similaridade/construir_pares.py` tokeniza, lematiza e remove stopwords com spaCy, escolhe as 200
lemas mais frequentes (substantivos, verbos e adjetivos), sorteia 100 pares disjuntos (semente 42) e
grava um arquivo de anotação por anotador. A escala Likert (1 a 5) e as instruções estão em
[`similaridade/README.md`](similaridade/README.md).

Os pares foram refeitos sobre o corpus ampliado (versão 2) e anotados pelos dois alunos
(`pares_gabriela.csv` e `pares_renato.csv`). A versão 1, feita sobre as 274 primeiras questões, está
arquivada em `similaridade/v1/`.

`similaridade/avaliar_concordancia.py` une as duas anotações, mede a concordância
([`similaridade/CONCORDANCIA.md`](similaridade/CONCORDANCIA.md)) e gera o CSV final
[`similaridade/similaridade_final.csv`](similaridade/similaridade_final.csv), com a nota de cada anotador
e a média das duas. *Dataset card*: [`similaridade/DATASET_CARD.md`](similaridade/DATASET_CARD.md).

### 4. Similaridade de palavras com modelos de linguagem (item 4)

[`similaridade/topico_4/similaridade_modelos.ipynb`](similaridade/topico_4/similaridade_modelos.ipynb) compara a
nota humana com spaCy `pt_core_news_lg`, BERT (BERTimbau e `bert-base-uncased`) e um LLM (Claude Opus 5.5, às cegas).
Usa dois datasets: o nosso (100 pares) e o feito em aula (80 pares). Só o LLM teve correlação clara com os humanos nos
dois (Spearman 0,53 e 0,48). Análise e comparação: [`similaridade/COMPARACAO.md`](similaridade/COMPARACAO.md).

## Como executar

Pré-requisitos: [`uv`](https://docs.astral.sh/uv/) (Python 3.14) e `poppler-utils` (`pdftotext`, só para refazer a
extração do texto). Instale as dependências (inclui spaCy e o modelo `pt_core_news_lg`):

```bash
uv sync
```

Os comandos abaixo rodam a partir da raiz do repositório:

```bash
# reconstrói as questões a partir de dataset/raw.zip
uv run python scraper/processar_dataset.py

# estatísticas do corpus
uv run python scraper/estatisticas_dataset.py

# palavras e pares para anotação de similaridade
uv run python similaridade/construir_pares.py

# une as anotações, calcula a concordância e gera o CSV final
uv run python similaridade/avaliar_concordancia.py

# classificação das questões por subárea (item 3; veja classificacao/README.md)
uv run python classificacao/classificar.py
```

Os scripts são determinísticos: rodar de novo reproduz os mesmos arquivos. Atenção: rodar
`construir_pares.py` **sobrescreve** os arquivos de anotação; não rode depois que começarem a
anotar.

Para refazer a extração do texto a partir dos PDFs (a coleta usa as dependências de
`scraper/requirements.txt`). O nome de cada `.txt` leva o prefixo da pasta da prova, pois muitos PDFs
têm o mesmo nome (`gabarito.pdf`):

```bash
for z in scraper/dados/pdfs_parte*.zip; do unzip -q -o "$z" -d /tmp/pdfs; done
mkdir -p /tmp/raw
find /tmp/pdfs -iname '*.pdf' | while read -r f; do
  pdftotext -layout "$f" "/tmp/raw/$(basename "$(dirname "$f")")__$(basename "${f%.*}").txt"
done
(cd /tmp/raw && zip -q "$OLDPWD/dataset/raw.zip" *.txt)
```

Nomes com mais de 200 caracteres são abreviados (prefixo da pasta truncado em 150 caracteres e nome do
PDF em 40), por causa do limite do sistema de arquivos.
