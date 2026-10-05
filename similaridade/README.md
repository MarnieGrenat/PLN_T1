# Corpus de similaridade de palavras

Item 2 do Trabalho 1. Palavras vêm de `dataset/questoes.jsonl` (enunciados + alternativas).

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
| `avaliar_modelos.py` | testa spaCy, BERT e um LLM contra a nota humana (Spearman, IC por bootstrap) |
| `colab_modelos.ipynb` | roda BERT e LLM aberto no Google Colab (sem GPU local) |
| `resultados/` | previsões de cada modelo (`pred_*.csv`) e contextos do corpus (`contextos.json`) |
| `ANALISE_MODELOS.md` | tabela de correlações dos modelos com os humanos (gerada) |
| `COMPARACAO.md` | análise e comparação dos resultados (item b) |
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

## Teste com modelos de linguagem

`avaliar_modelos.py` compara a nota humana (`similaridade_media`) com a de três tipos de modelo:

| modelo | como mede a similaridade |
|---|---|
| estático: spaCy `pt_core_news_lg` | cosseno entre os vetores das duas palavras |
| transformer: BERTimbau e `bert-base-uncased` | cosseno entre vetores (média das 4 últimas camadas) da palavra isolada e da palavra em até 20 contextos reais do corpus de questões |
| LLM: Claude Sonnet 5.5 | recebe só o par e a mesma escala Likert e dá a nota (feita em conversa, às cegas em relação às notas humanas; ver `resultados/LLM_CLAUDE.md`). `avaliar_modelos.py` também sabe chamar a API da Anthropic ou um LLM aberto via Hugging Face (nota esperada pelas probabilidades dos dígitos 1–5) |

A métrica é a correlação de Spearman com a nota humana (com IC 95% por bootstrap), comparada com o Spearman entre os
dois anotadores como referência. Se tiver o dataset de palavras feito em aula, passe `--dataset-aula arquivo.csv`
(colunas `palavra_1,palavra_2,similaridade`) e as métricas saem separadas por fonte.

```bash
python3 similaridade/avaliar_modelos.py --modelos contextos spacy        # local
python3 similaridade/avaliar_modelos.py --modelos bert                   # melhor com GPU (veja colab_modelos.ipynb)
ANTHROPIC_API_KEY=... python3 similaridade/avaliar_modelos.py --modelos llm --llm-backend anthropic
python3 similaridade/avaliar_modelos.py --so-analise                     # só a tabela final
```
