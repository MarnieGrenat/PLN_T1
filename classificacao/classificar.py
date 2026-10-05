# Trabalho 1 de PLN - Item 3: classificação das questões por subárea
#
# Objetivo: dado o texto de uma questão, dizer se ela é de redes, seguranca ou sistemas.
# Comparamos 3 formas de representar o texto:
#   1) Bag of Words + TF-IDF
#   2) Word embeddings estáticos do spaCy (pt_core_news_lg)
#   3) Embeddings de BERT (BERTimbau e bert-base-uncased)
#
# Para a comparação ser justa, todas usam o mesmo split treino/teste e o mesmo
# classificador (regressão logística). Assim a diferença vem só da representação.
#
# Como rodar (na raiz do repositório):
#   uv run python classificacao/classificar.py

import os
import re
import unicodedata

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # salva os gráficos em arquivo sem abrir janela
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix, ConfusionMatrixDisplay

ARQUIVO_QUESTOES = "dataset/questoes.jsonl"
PASTA_RESULTADOS = "classificacao/resultados"
PASTA_CACHE = "classificacao/cache"  # embeddings do BERT ficam salvos aqui (demora para gerar)
CLASSES = ["redes", "seguranca", "sistemas"]
SEMENTE = 42
MODELOS_BERT = ["neuralmind/bert-base-portuguese-cased", "bert-base-uncased"]

os.makedirs(PASTA_RESULTADOS, exist_ok=True)
os.makedirs(PASTA_CACHE, exist_ok=True)

# validação cruzada com 5 partes, mantendo a proporção das classes em cada parte
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMENTE)


# ============================================================
# 1. Carregar as questões
# ============================================================

def montar_texto(questao):
    # texto = enunciado + alternativas (as alternativas têm muitos termos técnicos)
    alternativas = questao["alternativas"]
    if isinstance(alternativas, dict):
        return questao["enunciado"] + " " + " ".join(alternativas.values())
    return questao["enunciado"]


def normalizar(texto):
    # minúsculas, sem acento e sem pontuação, só para comparar se duas questões são iguais
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return texto.strip()


df = pd.read_json(ARQUIVO_QUESTOES, lines=True)
print("Questões lidas:", len(df))

df["texto"] = df.apply(montar_texto, axis=1)
df["texto_normalizado"] = df["texto"].apply(normalizar)

# As bancas repetem questões entre concursos. Se uma cópia cair no treino e outra no
# teste, o modelo "decora" e o resultado fica melhor do que deveria. Então tiramos as repetidas.
# Se a mesma questão aparece em subáreas diferentes, não dá para saber o rótulo certo: tiramos todas.
qtd_subareas = df.groupby("texto_normalizado")["subarea"].nunique()
textos_ambiguos = qtd_subareas[qtd_subareas > 1].index
df = df[~df["texto_normalizado"].isin(textos_ambiguos)]
print("Removidas por rótulo ambíguo:", len(textos_ambiguos))

antes = len(df)
df = df.drop_duplicates(subset="texto_normalizado").reset_index(drop=True)
print("Removidas por duplicata:", antes - len(df))
print("Questões usadas:", len(df))
print(df["subarea"].value_counts(), "\n")


# ============================================================
# 2. Separar treino e teste (80% / 20%)
# ============================================================

# stratify garante a mesma proporção de cada subárea no treino e no teste
treino, teste = train_test_split(df, test_size=0.2, random_state=SEMENTE, stratify=df["subarea"])
y_treino = treino["subarea"].values
y_teste = teste["subarea"].values
print(f"Treino: {len(treino)} | Teste: {len(teste)}\n")

resultados = []  # uma linha por representação, para a tabela final


def avaliar(nome, modelo, X_teste, busca):
    # o conjunto de teste só é usado aqui, no final, uma única vez
    previsto = modelo.predict(X_teste)
    acuracia = accuracy_score(y_teste, previsto)
    f1 = f1_score(y_teste, previsto, average="macro")

    print(f"Acurácia: {acuracia:.3f} | F1 macro: {f1:.3f}")
    print(classification_report(y_teste, previsto, digits=3, zero_division=0))

    # matriz de confusão: linha = classe verdadeira, coluna = classe prevista
    arquivo = nome.replace("/", "_").replace(" ", "_")
    matriz = confusion_matrix(y_teste, previsto, labels=CLASSES)
    ConfusionMatrixDisplay(matriz, display_labels=CLASSES).plot(cmap="Blues", colorbar=False)
    plt.title(nome)
    plt.tight_layout()
    plt.savefig(f"{PASTA_RESULTADOS}/matriz_{arquivo}.png", dpi=150)
    plt.close()

    # salva as questões que o modelo errou, para olhar na análise
    erros = teste[previsto != y_teste][["id", "prova", "subarea", "enunciado"]].copy()
    erros.insert(3, "previsto", previsto[previsto != y_teste])
    erros.to_csv(f"{PASTA_RESULTADOS}/erros_{arquivo}.csv", index=False)

    # média e desvio do F1 na validação cruzada (no treino), para ver se a diferença é confiável
    i = busca.best_index_
    f1_cv = busca.cv_results_["mean_test_score"][i]
    desvio_cv = busca.cv_results_["std_test_score"][i]

    linha = {"representacao": nome, "acuracia": acuracia, "f1_macro": f1,
             "f1_cv_treino": f1_cv, "desvio_cv": desvio_cv, "melhores_parametros": str(busca.best_params_)}
    for c in CLASSES:
        linha["f1_" + c] = f1_score(y_teste, previsto, labels=[c], average="macro")
    resultados.append(linha)


def classificador_com_busca(X, y):
    # mesmo classificador para spaCy e BERT.
    # StandardScaler deixa todas as dimensões na mesma escala, o que ajuda a regressão logística.
    # C controla a regularização: C pequeno = modelo mais simples (evita overfitting)
    pipe = Pipeline([
        ("escala", StandardScaler()),
        ("clf", LogisticRegression(max_iter=5000, class_weight="balanced")),
    ])
    busca = GridSearchCV(pipe, {"clf__C": [0.001, 0.01, 0.1, 1, 10]}, cv=cv, scoring="f1_macro")
    busca.fit(X, y)
    print("Melhor C:", busca.best_params_["clf__C"])
    return busca


# ============================================================
# 3. Representação 1: Bag of Words + TF-IDF
# ============================================================
print("========== BoW + TF-IDF ==========")
from spacy.lang.pt.stop_words import STOP_WORDS

stopwords = list(STOP_WORDS)


def criar_pipeline_tfidf():
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            stop_words=stopwords,
            token_pattern=r"(?u)\b[^\W\d_]{2,}\b",  # só palavras com 2 ou mais letras (ignora números)
            sublinear_tf=True,  # usa 1 + log(tf), para uma palavra repetida não pesar demais
        )),
        ("clf", LogisticRegression(max_iter=5000, class_weight="balanced")),
    ])


# testamos várias combinações de parâmetros com validação cruzada no treino
parametros = {
    "tfidf__max_features": [1000, 5000, 20000, None],  # comprimento da BoW (None = todas as palavras)
    "tfidf__ngram_range": [(1, 1), (1, 2)],            # só palavras, ou palavras + pares de palavras
    "tfidf__min_df": [1, 2, 5],                        # ignora palavras que aparecem em poucas questões
    "clf__C": [0.1, 1, 10],
}
busca_tfidf = GridSearchCV(criar_pipeline_tfidf(), parametros, cv=cv, scoring="f1_macro")
busca_tfidf.fit(treino["texto"], y_treino)
print("Melhores parâmetros:", busca_tfidf.best_params_)

melhor_tfidf = busca_tfidf.best_estimator_
tamanho_bow = len(melhor_tfidf.named_steps["tfidf"].vocabulary_)
print("Tamanho final da BoW:", tamanho_bow, "palavras")

# Curva F1 x tamanho da BoW: fixa os melhores parâmetros e muda só o max_features.
# Serve para justificar o tamanho da BoW escolhido.
curva = []
for tamanho in [100, 250, 500, 1000, 2000, 5000, 10000, 20000]:
    pipe = criar_pipeline_tfidf()
    pipe.set_params(**busca_tfidf.best_params_)
    pipe.set_params(tfidf__max_features=tamanho)
    notas = cross_val_score(pipe, treino["texto"], y_treino, cv=cv, scoring="f1_macro")
    curva.append({"max_features": tamanho, "f1_media": notas.mean(), "f1_desvio": notas.std()})
    print(f"  BoW com {tamanho} palavras: F1 = {notas.mean():.3f} ± {notas.std():.3f}")
    if tamanho >= tamanho_bow * 2:  # já passou do vocabulário inteiro, não muda mais
        break
curva = pd.DataFrame(curva)
curva.to_csv(f"{PASTA_RESULTADOS}/curva_tamanho_bow.csv", index=False)

plt.figure(figsize=(6, 3.5))
plt.errorbar(curva["max_features"], curva["f1_media"], yerr=curva["f1_desvio"], marker="o", capsize=3)
plt.xscale("log")
plt.xlabel("tamanho da BoW (max_features)")
plt.ylabel("F1 macro (validação cruzada)")
plt.title("TF-IDF: F1 x tamanho da BoW")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{PASTA_RESULTADOS}/curva_tamanho_bow.png", dpi=150)
plt.close()

# palavras com maior peso para cada classe (ajuda a entender o que o modelo aprendeu)
vocabulario = melhor_tfidf.named_steps["tfidf"].get_feature_names_out()
regressao = melhor_tfidf.named_steps["clf"]
with open(f"{PASTA_RESULTADOS}/palavras_mais_importantes.txt", "w", encoding="utf-8") as f:
    for i, classe in enumerate(regressao.classes_):
        top = np.argsort(regressao.coef_[i])[::-1][:15]
        linha = f"{classe}: {', '.join(vocabulario[top])}"
        print(linha)
        f.write(linha + "\n")

avaliar("TF-IDF", melhor_tfidf, teste["texto"], busca_tfidf)


# ============================================================
# 4. Representação 2: embeddings estáticos do spaCy
# ============================================================
print("========== spaCy pt_core_news_lg ==========")
import spacy

nlp = spacy.load("pt_core_news_lg")

# o vetor da questão é a média dos vetores das palavras (sem stopwords, pontuação e números)
vetores_spacy = []
palavras_total = 0
palavras_com_vetor = 0
with nlp.select_pipes(disable=nlp.pipe_names):  # só precisamos dos vetores, desliga o resto (fica rápido)
    for doc in nlp.pipe(df["texto"], batch_size=64):
        palavras = [t for t in doc if t.is_alpha and not t.is_stop]
        vetores = [t.vector for t in palavras if t.has_vector]
        palavras_total += len(palavras)
        palavras_com_vetor += len(vetores)
        if vetores:
            vetores_spacy.append(np.mean(vetores, axis=0))
        else:
            vetores_spacy.append(np.zeros(300))
X_spacy = np.array(vetores_spacy)
print(f"Palavras com vetor no modelo: {palavras_com_vetor / palavras_total:.1%}")

# df foi resetado, então o índice de treino/teste é a posição da linha em X
busca_spacy = classificador_com_busca(X_spacy[treino.index], y_treino)
avaliar("spaCy", busca_spacy.best_estimator_, X_spacy[teste.index], busca_spacy)


# ============================================================
# 5. Representação 3: embeddings do BERT
# ============================================================
import torch
from transformers import AutoTokenizer, AutoModel


def gerar_embeddings_bert(nome_modelo, textos):
    arquivo_cache = f"{PASTA_CACHE}/{nome_modelo.replace('/', '_')}.npy"
    if os.path.exists(arquivo_cache):
        X = np.load(arquivo_cache)
        if len(X) == len(textos):  # se o dataset mudou, gera de novo
            print("Usando embeddings salvos em", arquivo_cache)
            return X

    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizador = AutoTokenizer.from_pretrained(nome_modelo)
    modelo = AutoModel.from_pretrained(nome_modelo).to(dispositivo)
    modelo.eval()

    embeddings = []
    with torch.no_grad():  # não estamos treinando o BERT, só usando
        for i in range(0, len(textos), 16):  # de 16 em 16 textos
            lote = textos[i:i + 16]
            entrada = tokenizador(lote, padding=True, truncation=True, max_length=512, return_tensors="pt").to(dispositivo)
            saida = modelo(**entrada).last_hidden_state  # um vetor de 768 posições por token

            # média dos vetores dos tokens, ignorando o padding (attention_mask = 0)
            mascara = entrada["attention_mask"].unsqueeze(-1)
            media = (saida * mascara).sum(dim=1) / mascara.sum(dim=1)
            embeddings.append(media.cpu().numpy())
            print(f"  {min(i + 16, len(textos))}/{len(textos)} questões", end="\r")
    print()

    X = np.vstack(embeddings)
    np.save(arquivo_cache, X)
    return X


for nome_modelo in MODELOS_BERT:
    print(f"========== BERT {nome_modelo} ==========")
    X_bert = gerar_embeddings_bert(nome_modelo, list(df["texto"]))
    busca_bert = classificador_com_busca(X_bert[treino.index], y_treino)
    avaliar("BERT " + nome_modelo, busca_bert.best_estimator_, X_bert[teste.index], busca_bert)


# ============================================================
# 6. Comparação final
# ============================================================
tabela = pd.DataFrame(resultados)
tabela.to_csv(f"{PASTA_RESULTADOS}/comparacao.csv", index=False)
print("\n========== COMPARAÇÃO ==========")
print(tabela[["representacao", "acuracia", "f1_macro", "f1_cv_treino", "desvio_cv"]].round(3).to_string(index=False))

x = np.arange(len(tabela))
plt.figure(figsize=(8, 4))
plt.bar(x - 0.2, tabela["acuracia"], 0.4, label="acurácia")
plt.bar(x + 0.2, tabela["f1_macro"], 0.4, label="F1 macro")
plt.xticks(x, tabela["representacao"], rotation=15, ha="right", fontsize=8)
plt.ylim(0, 1)
plt.title("Comparação das representações (conjunto de teste)")
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{PASTA_RESULTADOS}/comparacao.png", dpi=150)
plt.close()
print(f"\nResultados salvos em {PASTA_RESULTADOS}/")
