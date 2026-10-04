#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corpus de similaridade de palavras (Trabalho 1, item 2).

1. lê enunciados + alternativas de dataset/questoes.jsonl
2. spaCy (pt_core_news_lg): tokeniza, lematiza e remove stopwords
3. escolhe os 200 lemas mais representativos
4. sorteia 100 pares disjuntos (cada palavra aparece em exatamente um par)
5. grava os arquivos de anotação (um por anotador, mesma ordem de pares)

Uso (a partir da raiz do repositório):
    python3 similaridade/construir_pares.py
"""
import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import spacy

RAIZ = Path(__file__).resolve().parent.parent
DATASET = RAIZ / "dataset" / "questoes.jsonl"
DIR = Path(__file__).resolve().parent

N_PALAVRAS, N_PARES, SEMENTE = 200, 100, 42
CLASSES = {"NOUN", "VERB", "ADJ"}          # palavras de conteúdo; PROPN/X (siglas, código) ficam fora
MIN_LEN = 3
# vocabulário de enunciado de prova, que não diz nada sobre a área
BOILERPLATE = {"assinalar", "afirmativa", "afirmação", "alternativa", "correto", "incorreto", "seguinte",
               "considerar", "analisar", "opção", "questão", "acordo", "respeito", "item", "julgar",
               "apenas", "referir", "relação", "texto", "trecho", "ser", "ter", "haver", "estar", "fazer",
               "poder", "dever", "utilizar", "usar", "chamar", "denominar", "ocorrer", "possuir",
               # lemas errados do spaCy para formas verbais do enunciado ("assinale", "considere", ...)
               "assinaler", "considere", "analise", "afirmativo", "afirmar", "indicar", "seguir"}
ROMANO = re.compile(r"^[ivxlcdm]+$")

ESCALA = {
    1: "Totalmente dissimilar (ou Muito diferente)",
    2: "Parcialmente dissimilar (ou Um pouco diferente)",
    3: "Neutro / Indiferente (Nem similar, nem dissimilar)",
    4: "Parcialmente similar (ou Um pouco parecido)",
    5: "Totalmente similar (ou Muito parecido)",
}


def textos():
    with open(DATASET, encoding="utf-8") as f:
        for linha in f:
            q = json.loads(linha)
            yield q["enunciado"]
            yield from q["alternativas"].values()


def main():
    nlp = spacy.load("pt_core_news_lg", disable=["ner", "parser"])
    freq, docs = Counter(), defaultdict(set)   # frequência total e nº de questões onde aparece
    n_tokens = n_conteudo = 0
    for i, doc in enumerate(nlp.pipe(textos(), batch_size=64)):
        for t in doc:
            if t.is_space or t.is_punct:
                continue
            n_tokens += 1
            lema = t.lemma_.lower()
            if (t.is_stop or t.pos_ not in CLASSES or not lema.isalpha() or len(lema) < MIN_LEN
                    or ROMANO.match(lema) or lema in BOILERPLATE or nlp.vocab[lema].is_stop):
                continue
            n_conteudo += 1
            freq[lema] += 1
            docs[lema].add(i)

    # representatividade: frequência, com a dispersão (nº de textos) como desempate
    ranking = sorted(freq, key=lambda w: (-freq[w], -len(docs[w]), w))
    top = ranking[:N_PALAVRAS]
    if len(top) < N_PALAVRAS:
        raise SystemExit(f"só {len(top)} lemas disponíveis")

    with open(DIR / "palavras_top200.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "lema", "frequencia", "textos"])
        for r, lema in enumerate(top, 1):
            w.writerow([r, lema, freq[lema], len(docs[lema])])

    # pares disjuntos: embaralha e emparelha consecutivos
    rng = random.Random(SEMENTE)
    sorteadas = top[:]
    rng.shuffle(sorteadas)
    pares = [(sorteadas[2 * k], sorteadas[2 * k + 1]) for k in range(N_PARES)]

    for nome in ("anotador1", "anotador2"):
        with open(DIR / f"pares_{nome}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["palavra_1", "palavra_2", "similaridade"])
            for a, b in pares:
                w.writerow([a, b, ""])

    print(f"{n_tokens} tokens, {n_conteudo} de conteúdo, {len(freq)} lemas distintos")
    print(f"top {N_PALAVRAS}: {', '.join(top[:20])} ...")
    print(f"{N_PARES} pares gravados em {DIR}")


if __name__ == "__main__":
    main()
