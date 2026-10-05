# Carrega e prepara as questões para a classificação (usado pelo classificar.py e pelo Colab).
#
# Mantém uma única definição de "qual texto representa a questão" e de quais questões entram, para
# que o treino local e os embeddings gerados no Colab usem exatamente os mesmos textos, na mesma ordem.

import re
import unicodedata

import pandas as pd

ARQUIVO_QUESTOES = "dataset/questoes.jsonl"


def montar_texto(questao):
    # texto = enunciado + alternativas (as alternativas têm muitos termos técnicos).
    # Nos itens certo/errado as "alternativas" são só "Certo"/"Errado": não dizem nada sobre o assunto
    # e, como esses itens não se distribuem igualmente entre as subáreas, vazariam o rótulo. Ficam de fora.
    alternativas = questao["alternativas"]
    if questao.get("tipo") == "multipla_escolha" and isinstance(alternativas, dict):
        return questao["enunciado"] + " " + " ".join(alternativas.values())
    return questao["enunciado"]


def normalizar(texto):
    # minúsculas, sem acento e sem pontuação, só para comparar se duas questões são iguais
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return texto.strip()


def carregar_questoes(arquivo=ARQUIVO_QUESTOES, verboso=True):
    df = pd.read_json(arquivo, lines=True)
    if verboso:
        print("Questões lidas:", len(df))

    df["texto"] = df.apply(montar_texto, axis=1)
    df["texto_normalizado"] = df["texto"].apply(normalizar)

    # As bancas repetem questões entre concursos. Se uma cópia cair no treino e outra no
    # teste, o modelo "decora" e o resultado fica melhor do que deveria. Então tiramos as repetidas.
    # Se a mesma questão aparece em subáreas diferentes, não dá para saber o rótulo certo: tiramos todas.
    qtd_subareas = df.groupby("texto_normalizado")["subarea"].nunique()
    textos_ambiguos = qtd_subareas[qtd_subareas > 1].index
    df = df[~df["texto_normalizado"].isin(textos_ambiguos)]
    if verboso:
        print("Removidas por rótulo ambíguo:", len(textos_ambiguos))

    antes = len(df)
    df = df.drop_duplicates(subset="texto_normalizado").reset_index(drop=True)
    if verboso:
        print("Removidas por duplicata:", antes - len(df))
        print("Questões usadas:", len(df))
        print(df["subarea"].value_counts(), "\n")
    return df
