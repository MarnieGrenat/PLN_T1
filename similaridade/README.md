# Corpus de similaridade de palavras

Item 2 do Trabalho 1. Palavras vêm de `dataset/questoes.jsonl` (enunciados + alternativas).

## Arquivos

| arquivo | conteúdo |
|---|---|
| `palavras_top200.csv` | as 200 lemas mais representativas: `rank, lema, frequencia, textos` |
| `pares_anotador1.csv` | 100 pares para o anotador 1: `palavra_1, palavra_2, similaridade` |
| `pares_anotador2.csv` | os mesmos 100 pares, mesma ordem, para o anotador 2 |
| `construir_pares.py` | gera as palavras e os pares (semente fixa, resultado reprodutível) |
| `avaliar_concordancia.py` | une as anotações, calcula a concordância e gera o CSV final |
| `similaridade_final.csv` | **resultado**: `palavra_1, palavra_2, similaridade_a1, similaridade_a2, similaridade_media` |
| `CONCORDANCIA.md` | métricas de concordância entre os anotadores |

## Como foi gerado

1. spaCy `pt_core_news_lg`: tokenização, lematização e remoção de stopwords.
2. Ficam só substantivos, verbos e adjetivos (sem nomes próprios/siglas), com lema alfabético de ≥ 3
   letras, sem numerais romanos e sem vocabulário de enunciado ("assinalar", "alternativa", ...).
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
