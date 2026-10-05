# Classificação de questões por subárea (item 3)

Classifica as questões do corpus em **redes**, **seguranca** ou **sistemas**, comparando três representações de texto: BoW + TF-IDF, embeddings do spaCy (`pt_core_news_lg`) e embeddings de BERT (BERTimbau e `bert-base-uncased`). Todas usam o mesmo split treino/teste (80/20, semente 42) e o mesmo classificador (regressão logística).

## Como rodar

```
uv add scikit-learn matplotlib spacy transformers torch pandas
uv pip install https://github.com/explosion/spacy-models/releases/download/pt_core_news_lg-3.8.0/pt_core_news_lg-3.8.0-py3-none-any.whl
uv run python classificacao/classificar.py
```

Os embeddings do BERT ficam salvos em `classificacao/cache/` (fora do git) para as próximas execuções serem rápidas.
O nome do arquivo inclui um hash dos textos: se o dataset mudar, o cache antigo não é reaproveitado.

## Sem GPU: gerar os embeddings no Google Colab

Gerar os embeddings de BERT é a parte pesada. Em computador sem GPU, use [`colab_embeddings.ipynb`](colab_embeddings.ipynb):

1. Abra o notebook no Colab (*Arquivo → Fazer upload de notebook*) e escolha uma GPU (T4).
2. Envie `dataset/questoes.jsonl`, `classificacao/preparar_dados.py` e `classificacao/embeddings_bert.py` (o repositório é privado).
3. Rode as células e baixe `cache_embeddings.zip`.
4. No seu computador: `unzip cache_embeddings.zip -d classificacao/` e rode o `classificar.py` normalmente.

## Arquivos

| arquivo | função |
|---|---|
| `classificar.py` | TF-IDF, spaCy e BERT: treina, avalia e compara |
| `preparar_dados.py` | carrega o dataset e monta o texto de cada questão (mesmo código local e no Colab) |
| `embeddings_bert.py` | gera/carrega os embeddings de BERT (pode ser rodado sozinho) |
| `colab_embeddings.ipynb` | roda `embeddings_bert.py` no Colab |

Nos itens certo/errado, o texto usa só o enunciado: as "alternativas" (Certo/Errado) vazariam a subárea, já que
esses itens não se distribuem igualmente entre elas.

## Resultados

Ficam em `classificacao/resultados/`: tabela e gráfico de comparação (`comparacao.csv`, `comparacao.png`), matrizes de confusão, questões erradas por modelo, curva do F1 pelo tamanho da BoW e as palavras mais importantes de cada subárea no TF-IDF.


