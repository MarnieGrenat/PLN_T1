#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estatísticas do corpus: lê dataset/questoes.jsonl e grava dataset/ESTATISTICAS.md.

Uso (a partir da raiz do repositório):
    python3 scraper/estatisticas_dataset.py
"""
import json
import re
import statistics as st
import unicodedata
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "dataset"
SUBAREAS = ["redes", "seguranca", "sistemas"]

STOP = set("""a o as os um uma uns umas de do da dos das em no na nos nas por para com sem sob sobre entre ate
e ou mas que se como quando onde qual quais quem cujo cuja ao aos à às pelo pela pelos pelas seu sua seus suas
ser sao foi eh e ha ter tem sendo pode podem deve devem mais menos muito muita ja nao sim so tambem apenas
isso isto esse essa esses essas este esta estes estas aquele aquela seguinte seguir afirmativa afirmativas
assinale correta correto alternativa item itens acordo considerando""".split())


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def tokens(texto):
    return re.findall(r"\w+", texto.lower())


def texto_q(q):
    return q["enunciado"] + " " + " ".join(q["alternativas"].values())


def resumo(valores):
    if not valores:
        return "–"
    v = sorted(valores)
    return f"{st.mean(v):.1f} / {st.median(v):.0f} / {v[0]} / {v[-1]}"


def tabela(cabecalho, linhas):
    out = ["| " + " | ".join(map(str, cabecalho)) + " |","|" + "|".join("---" for _ in cabecalho) + "|"]
    out += ["| " + " | ".join(str(c) for c in l) + " |" for l in linhas]
    return "\n".join(out)


def main():
    qs = [json.loads(l) for l in open(DIR / "questoes.jsonl", encoding="utf-8")]
    por_sub = {s: [q for q in qs if q["subarea"] == s] for s in SUBAREAS}
    L = ["# Estatísticas do corpus", "",
         "Gerado por `scraper/estatisticas_dataset.py` a partir de `dataset/questoes.jsonl`.", ""]

    # ---- visão geral
    todos = [tokens(texto_q(q)) for q in qs]
    vocab = Counter(t for ts in todos for t in ts)
    L += ["## Visão geral", "",
          tabela(["métrica", "valor"], [
              ["questões", len(qs)],
              ["provas de origem", len({q["prova"] for q in qs})],
              ["tokens (enunciado + alternativas)", sum(map(len, todos))],
              ["vocabulário (tipos distintos)", len(vocab)],
              ["palavras que aparecem 1 vez", sum(1 for c in vocab.values() if c == 1)],
          ]), ""]

    # ---- subárea x ano
    anos = sorted({q["ano"] for q in qs})
    c = Counter((q["subarea"], q["ano"]) for q in qs)
    linhas = [[s] + [c[(s, a)] or "–" for a in anos] + [len(por_sub[s]),
              len({q["prova"] for q in por_sub[s]})] for s in SUBAREAS]
    linhas.append(["**total**"] + [sum(c[(s, a)] for s in SUBAREAS) for a in anos] + [len(qs),
                  len({q["prova"] for q in qs})])
    L += ["## Questões por subárea e ano", "", tabela(["subárea"] + anos + ["total", "provas"], linhas), ""]

    # ---- tamanhos
    L += ["## Tamanho dos textos (em tokens)", "",
          "Células: média / mediana / mín / máx.", ""]
    linhas = []
    for s in SUBAREAS + ["todas"]:
        grupo = qs if s == "todas" else por_sub[s]
        linhas.append([s,
                       resumo([len(tokens(q["enunciado"])) for q in grupo]),
                       resumo([len(tokens(v)) for q in grupo for v in q["alternativas"].values()]),
                       resumo([len(tokens(texto_q(q))) for q in grupo])])
    L += [tabela(["subárea", "enunciado", "alternativa (cada)", "questão inteira"], linhas), ""]

    # ---- alternativas e gabarito
    L += ["## Alternativas e gabarito", ""]
    n_alt = Counter(len(q["alternativas"]) for q in qs)
    L += ["Número de alternativas: " + ", ".join(f"{k} → {v}" for k, v in sorted(n_alt.items())), ""]
    letras = "ABCDE"
    linhas = []
    for s in SUBAREAS + ["todas"]:
        grupo = qs if s == "todas" else por_sub[s]
        cont = Counter(q["gabarito"] for q in grupo)
        n = len(grupo) or 1
        linhas.append([s] + [f"{cont[l]} ({100 * cont[l] / n:.0f}%)" for l in letras])
    L += ["Distribuição da letra correta:", "", tabela(["subárea"] + list(letras), linhas), ""]

    # ---- palavras mais frequentes
    L += ["## Palavras mais frequentes por subárea", "",
          "Sem stopwords; acentos preservados na exibição. Top 15.", ""]
    for s in SUBAREAS:
        cont = Counter()
        for q in por_sub[s]:
            for t in tokens(texto_q(q)):
                if len(t) > 2 and not t.isdigit() and sem_acento(t) not in STOP:
                    cont[t] += 1
        L.append(f"- **{s}**: " + ", ".join(f"{w} ({n})" for w, n in cont.most_common(15)))
    L.append("")

    # ---- palavras características (razão de frequência relativa)
    L += ["## Palavras características de cada subárea", "",
          "Maior razão entre a frequência relativa na subárea e no resto do corpus "
          "(mínimo de 5 ocorrências na subárea).", ""]
    cont_sub = {}
    for s in SUBAREAS:
        cont_sub[s] = Counter(t for q in por_sub[s] for t in tokens(texto_q(q))
                              if len(t) > 3 and not t.isdigit() and sem_acento(t) not in STOP)
    for s in SUBAREAS:
        resto = Counter()
        for o in SUBAREAS:
            if o != s:
                resto.update(cont_sub[o])
        n_s, n_r = sum(cont_sub[s].values()) or 1, sum(resto.values()) or 1
        pont = {w: (n / n_s) / ((resto[w] + 1) / n_r) for w, n in cont_sub[s].items() if n >= 5}
        top = sorted(pont, key=pont.get, reverse=True)[:12]
        L.append(f"- **{s}**: " + ", ".join(f"{w} ({cont_sub[s][w]})" for w in top))
    L.append("")

    (DIR / "ESTATISTICAS.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
