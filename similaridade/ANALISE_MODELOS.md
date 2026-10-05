# Similaridade de palavras: modelos de linguagem vs. anotação humana

Gerado por `similaridade/avaliar_modelos.py`. A nota humana é `similaridade_media` (média dos dois anotadores). Métrica principal: **correlação de Spearman** (a escala dos modelos não é a Likert: cosseno vai de -1 a 1, e só a ordenação dos pares importa). IC 95% por bootstrap (1000 reamostragens dos pares).

## Fonte: corpus próprio (100 pares)

| modelo | n | Spearman | IC 95% | Pearson | Spearman vs. a1 | Spearman vs. a2 |
|---|--:|--:|---|--:|--:|--:|
| bert-base-uncased-contexto | 100 | -0.051 | [-0.26, 0.15] | -0.060 | 0.025 | -0.090 |
| bert-base-uncased-isolada | 100 | -0.036 | [-0.23, 0.15] | -0.054 | -0.052 | -0.062 |
| llm-claude-sonnet-5-5 | 100 | 0.545 | [0.38, 0.70] | 0.604 | 0.471 | 0.483 |
| spacy | 100 | 0.173 | [0.01, 0.35] | 0.181 | 0.336 | 0.122 |

Referência humana: Spearman entre os dois anotadores = **0.265** (IC 95% [0.02, 0.47]). A nota de comparação é a **média** dos dois, que é menos ruidosa que um anotador sozinho: pela fórmula de Spearman-Brown a confiabilidade da média é 0.42, então mesmo um modelo perfeito teria correlação de cerca de **0.65** com ela (teto realista). Compare os modelos com esse valor, não com 1.

## Concordância entre os modelos (Spearman, corpus próprio)

| | bert-base-uncased-contexto | bert-base-uncased-isolada | llm-claude-sonnet-5-5 | spacy |
|---|--:|--:|--:|--:|
| bert-base-uncased-contexto | 1.00 | 0.56 | 0.11 | 0.25 |
| bert-base-uncased-isolada | 0.56 | 1.00 | 0.04 | 0.10 |
| llm-claude-sonnet-5-5 | 0.11 | 0.04 | 1.00 | 0.37 |
| spacy | 0.25 | 0.10 | 0.37 | 1.00 |

## Maiores divergências do melhor modelo (`llm-claude-sonnet-5-5`) em relação aos humanos

| par | nota humana | score do modelo | modelo acha |
|---|--:|--:|---|
| base – gerar | 2.5 | 1.000 | menos similar |
| componente – acessar | 2.5 | 1.000 | menos similar |
| modelo – autenticação | 2.5 | 1.000 | menos similar |
| integridade – incidente | 1.0 | 2.000 | mais similar |
| teste – ação | 1.0 | 2.000 | mais similar |
| virtual – seguro | 2.5 | 1.000 | menos similar |
| objeto – desenvolvimento | 1.0 | 2.000 | mais similar |
| informação – verificar | 1.0 | 2.000 | mais similar |
