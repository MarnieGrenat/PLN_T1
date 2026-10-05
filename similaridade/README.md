# Corpus de similaridade de palavras

Itens 2 e 4 do Trabalho 1. Palavras vêm de `dataset/questoes.jsonl` (enunciados + alternativas).

> **Versão 2.** Refeito sobre o corpus ampliado (1500 questões), anotado pelos dois alunos. Resultado em
> `similaridade_final.csv`, concordância em [`CONCORDANCIA.md`](CONCORDANCIA.md) e *dataset card* em
> [`DATASET_CARD.md`](DATASET_CARD.md). A versão anterior (274 questões) está em [`v1/`](v1/).

## Arquivos

| arquivo | conteúdo |
|---|---|
| `palavras_top200.csv` | os 200 lemas mais representativos: `rank, lema, frequencia, textos` |
| `pares_gabriela.csv` | 100 pares para a anotadora 1 (Gabriela): `palavra_1, palavra_2, similaridade`, com nome e escala no topo |
| `pares_renato.csv` | os mesmos 100 pares, mesma ordem, para o anotador 2 (Renato) |
| `construir_pares.py` | gera as palavras e os pares (semente fixa, resultado reprodutível) |
| `avaliar_concordancia.py` | une as anotações, calcula a concordância e gera o CSV final |
| `similaridade_final.csv` | **resultado**: `palavra_1, palavra_2, similaridade_a1, similaridade_a2, similaridade_media` |
| `topico_4/` | **item 4**: notebook `similaridade_modelos.ipynb` (spaCy, BERTimbau, `bert-base-uncased` e Claude nos dois datasets), dataset da aula, notas do Claude (`claude/`) e tabela/gráficos de comparação |
| `COMPARACAO.md` | **análise e comparação dos modelos (item 4b)** |
| `avaliar_modelos.py`, `colab_modelos.ipynb` | rodada preliminar do item 4 (só o corpus próprio; BERT em contexto, Claude Sonnet 5.5) |
| `resultados/` | previsões da rodada preliminar (`pred_*.csv`) e contextos do corpus (`contextos.json`) |
| `ANALISE_MODELOS.md` | tabela de correlações da rodada preliminar (gerada por `avaliar_modelos.py`) |
| `DATASET_CARD.md` | *dataset card* do CSV final (esquema, construção, estatísticas, limitações) |
| `CONCORDANCIA.md` | métricas de concordância entre os anotadores |

## Como foi gerado

1. spaCy `pt_core_news_lg`: tokenização, lematização e remoção de stopwords.
2. Ficam só substantivos, verbos e adjetivos (sem nomes próprios/siglas), com lema alfabético de ≥ 3
   letras, sem numerais romanos e sem vocabulário de enunciado ("assinalar", "alternativa", "julgue",
   "asserção", ...). Nos itens certo/errado só o enunciado entra (as "alternativas" são só Certo/Errado).
3. Representatividade = frequência do lema no corpus (desempate: nº de questões em que aparece).
4. As 200 lemas são embaralhadas (semente 42) e emparelhadas em sequência: 100 pares disjuntos,
   cada palavra aparece em exatamente um par.

## Escala Likert de similaridade

Preencha a coluna `similaridade` com um número de 1 a 5:

| valor | significado |
|:-:|---|
| 1 | Totalmente dissimilar (ou Muito diferente) |
| 2 | Parcialmente dissimilar (ou Um pouco diferente) |
| 3 | Neutro / Indiferente (Nem similar, nem dissimilar) |
| 4 | Parcialmente similar (ou Um pouco parecido) |
| 5 | Totalmente similar (ou Muito parecido) |

Cada anotador deve preencher o seu arquivo **sem ver as respostas do outro**.

## Teste com modelos de linguagem (item 4)

O experimento final está em [`topico_4/similaridade_modelos.ipynb`](topico_4/similaridade_modelos.ipynb). Ele testa os
100 pares do nosso dataset e os 80 pares do dataset feito em aula (`topico_4/dataset_aula.csv`) com:

| modelo | como mede a similaridade |
|---|---|
| estático: spaCy `pt_core_news_lg` | cosseno entre os vetores das duas palavras |
| transformer: BERTimbau e `bert-base-uncased` | cosseno entre os vetores da palavra isolada (média dos sub-tokens) |
| LLM: Claude Opus 5.5 | recebe só os pares e a mesma escala dos anotadores e dá a nota, em sessão separada e às cegas (prompt e respostas em `topico_4/claude/`) |

Métrica: correlação de Spearman com a média dos anotadores. Resultado (nosso / aula): Claude 0,53 / 0,48,
BERTimbau 0,22 / −0,01, spaCy 0,17 / −0,03, `bert-base-uncased` −0,04 / −0,01. Análise completa em
[`COMPARACAO.md`](COMPARACAO.md).

Para rodar o notebook (o Claude não é chamado por ele: as notas são lidas de `topico_4/claude/`):

```bash
uv add spacy transformers torch google-genai pandas scipy matplotlib
```

Depois, abra o notebook no Jupyter ou no VS Code e rode as células em ordem (BERT fica mais rápido com GPU).

### Rodada preliminar

`avaliar_modelos.py` foi a primeira versão do item 4, só com o nosso dataset. Ela testa também o BERT com a palavra em
até 20 contextos do corpus (média das 4 últimas camadas) e um LLM pela API da Anthropic ou um LLM aberto via Hugging
Face. Os resultados estão em `ANALISE_MODELOS.md` e batem com os da rodada final.

```bash
python3 similaridade/avaliar_modelos.py --modelos contextos spacy        # local
python3 similaridade/avaliar_modelos.py --modelos bert                   # melhor com GPU (veja colab_modelos.ipynb)
ANTHROPIC_API_KEY=... python3 similaridade/avaliar_modelos.py --modelos llm --llm-backend anthropic
python3 similaridade/avaliar_modelos.py --so-analise                     # só a tabela final
```
