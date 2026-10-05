# Classificação de questões por subárea (item 3)

Classifica as questões do corpus em **redes**, **seguranca** ou **sistemas**, comparando três representações de texto: BoW + TF-IDF, embeddings do spaCy (`pt_core_news_lg`) e embeddings de BERT (BERTimbau e `bert-base-uncased`). Todas usam o mesmo split treino/teste (80/20, semente 42) e o mesmo classificador (regressão logística).

## Como rodar

```
uv add scikit-learn matplotlib spacy transformers torch pandas
uv pip install https://github.com/explosion/spacy-models/releases/download/pt_core_news_lg-3.8.0/pt_core_news_lg-3.8.0-py3-none-any.whl
uv run python classificacao/classificar.py
```

Os embeddings do BERT ficam salvos em `classificacao/cache/` (fora do git) para as próximas execuções serem rápidas.

## Resultados

Ficam em `classificacao/resultados/`: tabela e gráfico de comparação (`comparacao.csv`, `comparacao.png`), matrizes de confusão, questões erradas por modelo, curva do F1 pelo tamanho da BoW e as palavras mais importantes de cada subárea no TF-IDF.

## Uso de IA

O código foi desenvolvido com auxílio do Claude (Anthropic); o grupo revisou, executou e analisou os resultados.
