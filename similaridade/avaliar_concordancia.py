#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Une as anotações dos dois alunos, mede a concordância e gera o CSV final (itens d e e).

Entradas : similaridade/pares_gabriela.csv (anotador 1) e pares_renato.csv (anotador 2)
Saídas   : similaridade/similaridade_final.csv  (palavra_1, palavra_2, similaridade_a1,
                                                 similaridade_a2, similaridade_media)
           similaridade/CONCORDANCIA.md         (métricas de concordância)

Os arquivos de entrada têm linhas de cabeçalho (nome do anotador e escala) antes dos pares; por isso
só são lidas as linhas cuja terceira coluna é uma nota de 1 a 5 e cuja primeira coluna não é a própria
linha da escala.

Uso (a partir da raiz do repositório):
    python3 similaridade/avaliar_concordancia.py
"""
import csv
import math
from collections import Counter
from pathlib import Path

DIR = Path(__file__).resolve().parent
NOTAS = [1, 2, 3, 4, 5]


def ler_anotacoes(caminho):
    """Retorna {(palavra_1, palavra_2): nota} e a ordem dos pares no arquivo."""
    notas, ordem = {}, []
    with open(caminho, encoding="utf-8", newline="") as f:
        for linha in csv.reader(f):
            if len(linha) < 3 or linha[2].strip() not in map(str, NOTAS):
                continue
            if linha[0].strip() in map(str, NOTAS):   # linha da escala ("5,Totalmente,similar")
                continue
            par = (linha[0].strip(), linha[1].strip())
            if par in notas:
                raise SystemExit(f"{caminho.name}: par duplicado {par}")
            notas[par] = int(linha[2])
            ordem.append(par)
    return notas, ordem


# ---------------------------------------------------------------- métricas
def kappa(a, b, peso):
    """Kappa de Cohen com pesos: 'nenhum', 'linear' ou 'quadratico'."""
    n, k = len(a), len(NOTAS)
    obs = [[0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[x - 1][y - 1] += 1
    marg_a = [sum(obs[i]) for i in range(k)]
    marg_b = [sum(obs[i][j] for i in range(k)) for j in range(k)]

    def w(i, j):  # discordância ponderada entre as categorias i e j
        d = abs(i - j) / (k - 1)
        return {"nenhum": float(i != j), "linear": d, "quadratico": d * d}[peso]

    num = sum(w(i, j) * obs[i][j] for i in range(k) for j in range(k))
    den = sum(w(i, j) * marg_a[i] * marg_b[j] / n for i in range(k) for j in range(k))
    return 1 - num / den if den else float("nan")


def pearson(x, y):
    mx, my = sum(x) / len(x), sum(y) / len(y)
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    vx, vy = sum((a - mx) ** 2 for a in x), sum((b - my) ** 2 for b in y)
    return cov / math.sqrt(vx * vy) if vx and vy else float("nan")


def postos(v):
    """Postos com empates resolvidos pela média."""
    ordem = sorted(range(len(v)), key=lambda i: v[i])
    r, i = [0.0] * len(v), 0
    while i < len(ordem):
        j = i
        while j + 1 < len(ordem) and v[ordem[j + 1]] == v[ordem[i]]:
            j += 1
        for k in range(i, j + 1):
            r[ordem[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def interpretar_kappa(k):
    """Escala de Landis & Koch (1977)."""
    if k != k:
        return "indefinido"
    for limite, rotulo in [(0, "pior que o acaso"), (0.20, "leve"), (0.40, "razoável"),
                           (0.60, "moderada"), (0.80, "substancial"), (1.01, "quase perfeita")]:
        if k <= limite:
            return rotulo
    return "quase perfeita"


def main():
    n1, ordem = ler_anotacoes(DIR / "pares_gabriela.csv")
    n2, _ = ler_anotacoes(DIR / "pares_renato.csv")
    if set(n1) != set(n2):
        raise SystemExit(f"os arquivos não têm os mesmos pares: só no 1 = {set(n1) - set(n2)}, "
                         f"só no 2 = {set(n2) - set(n1)}")
    a = [n1[p] for p in ordem]
    b = [n2[p] for p in ordem]
    n = len(ordem)

    # ---- CSV final: nota de cada anotador e a média
    with open(DIR / "similaridade_final.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["palavra_1", "palavra_2", "similaridade_a1", "similaridade_a2", "similaridade_media"])
        for (p1, p2), x, y in zip(ordem, a, b):
            w.writerow([p1, p2, x, y, f"{(x + y) / 2:.1f}"])

    # ---- métricas
    difs = [abs(x - y) for x, y in zip(a, b)]
    exata = sum(d == 0 for d in difs) / n
    ate1 = sum(d <= 1 for d in difs) / n
    k_n, k_l, k_q = (kappa(a, b, p) for p in ("nenhum", "linear", "quadratico"))
    r_p, r_s = pearson(a, b), pearson(postos(a), postos(b))
    media = [(x + y) / 2 for x, y in zip(a, b)]

    linhas = ["# Concordância entre anotadores", "",
              "Gerado por `similaridade/avaliar_concordancia.py`.", "",
              f"{n} pares anotados por 2 alunos na escala Likert de 1 a 5. "
              "A nota final de cada par (`similaridade_media`) é a média das duas.", "",
              "## Distribuição das notas", "",
              "| nota | Gabriela (a1) | Renato (a2) |", "|:-:|--:|--:|"]
    c1, c2 = Counter(a), Counter(b)
    linhas += [f"| {v} | {c1[v]} | {c2[v]} |" for v in NOTAS]
    linhas += ["", f"Média das notas: Gabriela (a1) = {sum(a) / n:.2f}, Renato (a2) = {sum(b) / n:.2f}.", "",
               "## Métricas", "",
               "| métrica | valor |", "|---|--:|",
               f"| concordância exata | {100 * exata:.0f}% |",
               f"| diferença de até 1 ponto | {100 * ate1:.0f}% |",
               f"| diferença absoluta média | {sum(difs) / n:.2f} |",
               f"| kappa de Cohen | {k_n:.3f} ({interpretar_kappa(k_n)}) |",
               f"| kappa ponderado linear | {k_l:.3f} ({interpretar_kappa(k_l)}) |",
               f"| kappa ponderado quadrático | {k_q:.3f} ({interpretar_kappa(k_q)}) |",
               f"| correlação de Pearson | {r_p:.3f} |",
               f"| correlação de Spearman | {r_s:.3f} |", "",
               "O kappa simples trata toda divergência como igual; os ponderados penalizam mais as "
               "divergências grandes (dar 1 e 5 pesa mais que 1 e 2), o que combina melhor com uma "
               "escala ordinal. Spearman mede se os dois ordenam os pares de forma parecida, mesmo que "
               "um use a escala de forma mais compressa que o outro. Interpretação do kappa: escala de "
               "Landis & Koch (1977).", "",
               "## Maiores divergências", "",
               "| par | Gabriela (a1) | Renato (a2) |", "|---|:-:|:-:|"]
    for i in sorted(range(n), key=lambda i: -difs[i])[:10]:
        if difs[i] >= 2:
            linhas.append(f"| {ordem[i][0]} – {ordem[i][1]} | {a[i]} | {b[i]} |")
    linhas += ["", "## Pares mais e menos similares (nota média)", "",
               "Mais similares: " + ", ".join(f"{ordem[i][0]}–{ordem[i][1]} ({media[i]:.1f})"
                                              for i in sorted(range(n), key=lambda i: -media[i])[:8]), "",
               "Menos similares: " + ", ".join(f"{ordem[i][0]}–{ordem[i][1]} ({media[i]:.1f})"
                                               for i in sorted(range(n), key=lambda i: media[i])[:5]), ""]
    texto = "\n".join(linhas)
    (DIR / "CONCORDANCIA.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
