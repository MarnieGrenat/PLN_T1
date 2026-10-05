# PLN T1

Trabalho 1 de Processamento de Linguagem Natural (PUCRS): construção de um corpus de questões de
concursos de TI (subáreas **redes**, **segurança** e **sistemas**) e de um corpus de similaridade de
palavras derivado dele.

## Estrutura

| pasta | conteúdo |
|---|---|
| `scraper/` | coleta (web scraping) das provas e gabaritos e processamento em questões estruturadas |
| `dataset/` | corpus de questões: texto bruto, questões por subárea/ano, estatísticas e *dataset card* |
| `similaridade/` | corpus de similaridade de palavras: 200 palavras, 100 pares e arquivos de anotação |
| `src/` | treino e inferência dos modelos |

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
similaridade/palavras_top200.csv, similaridade/pares_anotador{1,2}.csv
```

### 1. Corpus de questões (item 1)

1. `scraper/scraper_pci.py` baixa provas e gabaritos (PDF) das listagens de cada subárea. Os PDFs
   ficam versionados em `scraper/dados/pdfs_parte01.zip`, `pdfs_parte02.zip`, … (até ~45 MB cada,
   abaixo do limite do GitHub). Cada zip é independente e contém pastas `<slug-da-prova>/` inteiras;
   extraia todos no mesmo diretório para reconstruir `scraper/dados/pdfs/`.
2. O texto foi extraído com `pdftotext -layout` e compactado em `dataset/raw.zip`.
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

Estado: os arquivos `pares_anotador1.csv` e `pares_anotador2.csv` estão **sem anotação** (coluna
`similaridade` vazia). Faltam anotar os pares, medir a concordância entre os anotadores e gerar o CSV
final.

## Como executar

Pré-requisitos: Python 3, `poppler-utils` (`pdftotext`) e, para o item 2, spaCy com o modelo
português grande.

```bash
pip install spacy
python3 -m spacy download pt_core_news_lg
```

Os comandos abaixo rodam a partir da raiz do repositório:

```bash
# reconstrói as questões a partir de dataset/raw.zip
python3 scraper/processar_dataset.py

# estatísticas do corpus
python3 scraper/estatisticas_dataset.py

# palavras e pares para anotação de similaridade
python3 similaridade/construir_pares.py
```

Os três scripts são determinísticos: rodar de novo reproduz os mesmos arquivos. Atenção: rodar
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

Um dos PDFs tem nome longo demais para o sistema de arquivos e foi gravado com nome abreviado
(`pebtt-redes-de-computadores-ifrj-selecon-2022__pebtt_redes_de_computadores__1_.txt`).
