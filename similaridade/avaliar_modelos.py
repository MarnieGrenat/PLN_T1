#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Similaridade de palavras com modelos de linguagem (Trabalho 1, item 2 - segunda parte).

Compara a nota de similaridade dada pelos modelos com a nota humana (`similaridade_media` de
similaridade_final.csv), com três tipos de modelo:

  spacy  : modelo estático (vetores de palavra do pt_core_news_lg), similaridade de cosseno
  bert   : transformer (BERTimbau e bert-base-uncased), similaridade de cosseno entre
           (a) a palavra isolada e (b) a média dos vetores da palavra em contextos reais do corpus
  llm    : LLM que recebe o par e responde uma nota de 1 a 5 (a mesma escala Likert dos anotadores)

Cada modelo grava seu resultado em similaridade/resultados/pred_<nome>.csv, então os modelos pesados
(bert, llm) podem rodar no Colab e a análise (sempre no final) roda no seu computador.

Etapas (use --modelos com uma ou mais):
  contextos : sorteia ocorrências de cada palavra no corpus de questões (precisa de spaCy; rode local)
  spacy | bert | llm : calcula as previsões
  (a análise de correlação roda sempre no final; --so-analise pula o cálculo)

Exemplos (a partir da raiz do repositório):
  python3 similaridade/avaliar_modelos.py --modelos contextos spacy
  python3 similaridade/avaliar_modelos.py --modelos bert                              # melhor com GPU
  python3 similaridade/avaliar_modelos.py --modelos llm --llm-backend anthropic       # precisa de ANTHROPIC_API_KEY
  python3 similaridade/avaliar_modelos.py --modelos llm --llm-backend hf --llm-modelo Qwen/Qwen2.5-3B-Instruct
  python3 similaridade/avaliar_modelos.py --so-analise

Para incluir também o dataset de palavras feito em aula, passe --dataset-aula arquivo.csv, com as colunas
palavra_1, palavra_2, similaridade (nota humana). As métricas saem separadas por fonte.
"""
import argparse
import csv
import json
import math
import os
import re
from pathlib import Path

import numpy as np

DIR = Path(__file__).resolve().parent
RAIZ = DIR.parent
ARQ_FINAL = DIR / "similaridade_final.csv"
ARQ_QUESTOES = RAIZ / "dataset" / "questoes.jsonl"
PASTA = DIR / "resultados"
ARQ_CONTEXTOS = PASTA / "contextos.json"
ARQ_ANALISE = DIR / "ANALISE_MODELOS.md"

MODELOS_BERT = ["neuralmind/bert-base-portuguese-cased", "bert-base-uncased"]
MAX_CONTEXTOS, JANELA, SEMENTE = 20, 150, 42

PROMPT = """Você avalia a similaridade semântica entre duas palavras do vocabulário de TI (redes, segurança da \
informação e sistemas) em português.

Dê uma nota de 1 a 5:
1 = Totalmente dissimilar (ou Muito diferente)
2 = Parcialmente dissimilar (ou Um pouco diferente)
3 = Neutro / Indiferente (Nem similar, nem dissimilar)
4 = Parcialmente similar (ou Um pouco parecido)
5 = Totalmente similar (ou Muito parecido)

Palavra 1: {a}
Palavra 2: {b}

Responda apenas com o número da nota (1 a 5)."""


# ---------------------------------------------------------------- dados
def ler_pares(arquivo_aula=None):
    """Retorna lista de dicts: palavra_1, palavra_2, fonte, ouro (+ a1/a2 nos pares próprios)."""
    pares = []
    with open(ARQ_FINAL, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            pares.append({"palavra_1": r["palavra_1"], "palavra_2": r["palavra_2"], "fonte": "nossa",
                          "ouro": float(r["similaridade_media"]),
                          "a1": float(r["similaridade_a1"]), "a2": float(r["similaridade_a2"])})
    if arquivo_aula:
        with open(arquivo_aula, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                pares.append({"palavra_1": r["palavra_1"].strip(), "palavra_2": r["palavra_2"].strip(),
                              "fonte": "aula", "ouro": float(r["similaridade"])})
    return pares


def palavras_dos_pares(pares):
    return sorted({p[k] for p in pares for k in ("palavra_1", "palavra_2")})


def cosseno(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float("nan") if nu == 0 or nv == 0 else float(np.dot(u, v) / (nu * nv))


def salvar_previsoes(nome, pares, scores):
    PASTA.mkdir(exist_ok=True)
    with open(PASTA / f"pred_{nome}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fonte", "palavra_1", "palavra_2", "score"])
        for p, s in zip(pares, scores):
            w.writerow([p["fonte"], p["palavra_1"], p["palavra_2"], "" if s != s else f"{s:.6f}"])
    print(f"  -> resultados/pred_{nome}.csv ({sum(s == s for s in scores)}/{len(scores)} pares com nota)")


def slug(nome):
    return re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-")


# ---------------------------------------------------------------- contextos (corpus)
def montar_contextos(palavras):
    """Para cada palavra (lema), sorteia até MAX_CONTEXTOS ocorrências no corpus de questões."""
    import random
    import spacy

    nlp = spacy.load("pt_core_news_lg", disable=["ner", "parser"])
    alvo = set(palavras)
    ocorrencias = {w: [] for w in palavras}
    textos = []
    with open(ARQ_QUESTOES, encoding="utf-8") as f:
        for linha in f:
            q = json.loads(linha)
            t = q["enunciado"]
            if q["tipo"] == "multipla_escolha":
                t += " " + " ".join(q["alternativas"].values())
            textos.append(t)
    for texto, doc in zip(textos, nlp.pipe(textos, batch_size=64)):
        for tok in doc:
            lema = tok.lemma_.lower()
            if lema in alvo:
                ini, fim = tok.idx, tok.idx + len(tok.text)
                a, b = max(0, ini - JANELA), min(len(texto), fim + JANELA)
                ocorrencias[lema].append({"texto": texto[a:b], "ini": ini - a, "fim": fim - a})
    rng = random.Random(SEMENTE)
    saida = {}
    for w, lista in ocorrencias.items():
        rng.shuffle(lista)
        saida[w] = lista[:MAX_CONTEXTOS]
    PASTA.mkdir(exist_ok=True)
    ARQ_CONTEXTOS.write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
    sem = [w for w, l in saida.items() if not l]
    print(f"  -> {ARQ_CONTEXTOS.relative_to(RAIZ)}: {sum(len(l) for l in saida.values())} contextos; palavras sem contexto: {sem}")


# ---------------------------------------------------------------- modelo estático (spaCy)
def prever_spacy(pares):
    import spacy

    nlp = spacy.load("pt_core_news_lg")
    vec = lambda w: nlp.vocab[w].vector if nlp.vocab[w].has_vector else np.zeros(nlp.vocab.vectors_length)
    return [cosseno(vec(p["palavra_1"]), vec(p["palavra_2"])) for p in pares]


# ---------------------------------------------------------------- transformer (BERT)
def prever_bert(pares, nome_modelo):
    import torch
    from transformers import AutoModel, AutoTokenizer

    palavras = palavras_dos_pares(pares)
    disp = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  {nome_modelo} em {disp}")
    tok = AutoTokenizer.from_pretrained(nome_modelo)
    mod = AutoModel.from_pretrained(nome_modelo, output_hidden_states=True).to(disp).eval()

    def camadas(ent):
        # média das 4 últimas camadas: costuma representar melhor o significado que só a última
        return torch.stack(mod(**ent).hidden_states[-4:]).mean(0)

    # (a) palavra isolada: média dos subtokens da palavra (sem [CLS]/[SEP]/padding)
    isolada = {}
    with torch.no_grad():
        for i in range(0, len(palavras), 32):
            lote = palavras[i:i + 32]
            ent = tok(lote, padding=True, return_tensors="pt", return_special_tokens_mask=True)
            especial = ent.pop("special_tokens_mask")
            ent = ent.to(disp)
            mascara = (ent["attention_mask"] * (1 - especial.to(disp))).unsqueeze(-1)
            h = camadas(ent)
            v = ((h * mascara).sum(1) / mascara.sum(1)).cpu().numpy()
            isolada.update(zip(lote, v))
    saidas = {"isolada": [cosseno(isolada[p["palavra_1"]], isolada[p["palavra_2"]]) for p in pares]}

    # (b) em contexto: média dos vetores da palavra em até MAX_CONTEXTOS ocorrências reais do corpus
    if ARQ_CONTEXTOS.exists():
        contextos = json.loads(ARQ_CONTEXTOS.read_text(encoding="utf-8"))
        contexto = {}
        with torch.no_grad():
            for w in palavras:
                vs = []
                for oc in contextos.get(w, []):
                    ent = tok(oc["texto"], return_offsets_mapping=True, return_tensors="pt",
                              truncation=True, max_length=256)
                    off = ent.pop("offset_mapping")[0]
                    ent = ent.to(disp)
                    h = camadas(ent)[0]
                    sel = [k for k, (a, b) in enumerate(off.tolist()) if b > a and a < oc["fim"] and b > oc["ini"]]
                    if sel:
                        vs.append(h[sel].mean(0).cpu().numpy())
                contexto[w] = np.mean(vs, axis=0) if vs else None
        saidas["contexto"] = [
            float("nan") if contexto[p["palavra_1"]] is None or contexto[p["palavra_2"]] is None
            else cosseno(contexto[p["palavra_1"]], contexto[p["palavra_2"]]) for p in pares]
    else:
        print("  (sem resultados/contextos.json: pulando a variante em contexto; rode --modelos contextos)")
    return saidas


# ---------------------------------------------------------------- LLM
def extrair_nota(texto):
    m = re.search(r"[1-5]", texto or "")
    return float(m.group(0)) if m else float("nan")


def prever_llm_anthropic(pares, modelo):
    import anthropic

    cliente = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente
    notas = []
    for i, p in enumerate(pares, 1):
        r = cliente.messages.create(model=modelo, max_tokens=8, temperature=0,
                                    messages=[{"role": "user", "content": PROMPT.format(a=p["palavra_1"], b=p["palavra_2"])}])
        notas.append(extrair_nota("".join(b.text for b in r.content if b.type == "text")))
        print(f"  {i}/{len(pares)}", end="\r")
    print()
    return notas


def prever_llm_hf(pares, modelo):
    """LLM aberto local: nota esperada = soma(k * P(k)), com P tirada da distribuição do próximo token."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    disp = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(modelo)
    mod = AutoModelForCausalLM.from_pretrained(modelo, torch_dtype=torch.float16 if disp == "cuda" else torch.float32,
                                               device_map="auto" if disp == "cuda" else None).eval()
    ids = [tok.encode(str(k), add_special_tokens=False)[-1] for k in range(1, 6)]
    notas = []
    with torch.no_grad():
        for i, p in enumerate(pares, 1):
            msg = [{"role": "user", "content": PROMPT.format(a=p["palavra_1"], b=p["palavra_2"])}]
            texto = tok.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
            ent = tok(texto, return_tensors="pt").to(mod.device)
            logits = mod(**ent).logits[0, -1, ids].float()
            prob = torch.softmax(logits, dim=0).cpu().numpy()
            notas.append(float((prob * np.arange(1, 6)).sum()))
            print(f"  {i}/{len(pares)}", end="\r")
    print()
    return notas


# ---------------------------------------------------------------- análise
def correlacoes(x, y):
    from scipy.stats import pearsonr, spearmanr

    x, y = np.array(x, float), np.array(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    if len(x) < 5 or np.std(x) == 0 or np.std(y) == 0:
        return {"n": int(len(x)), "spearman": float("nan"), "pearson": float("nan"), "ic": (float("nan"),) * 2}
    rng = np.random.default_rng(SEMENTE)
    boot = []
    for _ in range(1000):                     # IC 95% do Spearman por bootstrap dos pares
        i = rng.integers(0, len(x), len(x))
        if np.std(x[i]) and np.std(y[i]):
            boot.append(spearmanr(x[i], y[i])[0])
    ic = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))) if boot else (float("nan"),) * 2
    return {"n": int(len(x)), "spearman": float(spearmanr(x, y)[0]), "pearson": float(pearsonr(x, y)[0]), "ic": ic}


def f(v, casas=3):
    return "–" if v != v else f"{v:.{casas}f}"


def analisar(pares):
    arquivos = sorted(PASTA.glob("pred_*.csv")) if PASTA.exists() else []
    if not arquivos:
        print("Nenhuma previsão em similaridade/resultados/. Rode --modelos spacy (e bert/llm).")
        return
    chave = lambda p: (p["fonte"], p["palavra_1"], p["palavra_2"])
    ouro = {chave(p): p for p in pares}
    modelos = {}
    for a in arquivos:
        with open(a, encoding="utf-8", newline="") as fh:
            modelos[a.stem[len("pred_"):]] = {(r["fonte"], r["palavra_1"], r["palavra_2"]): float(r["score"]) if r["score"] else float("nan")
                                              for r in csv.DictReader(fh)}

    linhas = ["# Similaridade de palavras: modelos de linguagem vs. anotação humana", "",
              "> **Rodada preliminar** (só o corpus próprio). O resultado final do item 4, com o dataset da aula e o "
              "BERTimbau, está em [`topico_4/similaridade_modelos.ipynb`](topico_4/similaridade_modelos.ipynb) e a "
              "análise em [`COMPARACAO.md`](COMPARACAO.md).", "",
              "Gerado por `similaridade/avaliar_modelos.py`. A nota humana é `similaridade_media` "
              "(média dos dois anotadores). Métrica principal: **correlação de Spearman** (a escala dos modelos "
              "não é a Likert: cosseno vai de -1 a 1, e só a ordenação dos pares importa). IC 95% por bootstrap "
              "(1000 reamostragens dos pares).", ""]
    fontes = sorted({p["fonte"] for p in pares})
    for fonte in fontes:
        ps = [p for p in pares if p["fonte"] == fonte]
        linhas += [f"## Fonte: {'corpus próprio' if fonte == 'nossa' else 'dataset da aula'} ({len(ps)} pares)", "",
                   "| modelo | n | Spearman | IC 95% | Pearson |" + (" Spearman vs. a1 | Spearman vs. a2 |" if fonte == "nossa" else ""),
                   "|---|--:|--:|---|--:|" + ("--:|--:|" if fonte == "nossa" else "")]
        ouro_f = [p["ouro"] for p in ps]
        for nome, pred in modelos.items():
            sc = [pred.get(chave(p), float("nan")) for p in ps]
            c = correlacoes(sc, ouro_f)
            linha = f"| {nome} | {c['n']} | {f(c['spearman'])} | [{f(c['ic'][0], 2)}, {f(c['ic'][1], 2)}] | {f(c['pearson'])} |"
            if fonte == "nossa":
                linha += f" {f(correlacoes(sc, [p['a1'] for p in ps])['spearman'])} | {f(correlacoes(sc, [p['a2'] for p in ps])['spearman'])} |"
            linhas.append(linha)
        if fonte == "nossa":
            h = correlacoes([p["a1"] for p in ps], [p["a2"] for p in ps])
            rho = h["spearman"]
            conf = 2 * rho / (1 + rho)                     # Spearman-Brown: confiabilidade da média dos 2 anotadores
            teto = math.sqrt(conf) if conf == conf and conf > 0 else float("nan")
            linhas += ["", f"Referência humana: Spearman entre os dois anotadores = **{f(rho)}** "
                           f"(IC 95% [{f(h['ic'][0], 2)}, {f(h['ic'][1], 2)}]). A nota de comparação é a **média** dos "
                           f"dois, que é menos ruidosa que um anotador sozinho: pela fórmula de Spearman-Brown a "
                           f"confiabilidade da média é {f(conf, 2)}, então mesmo um modelo perfeito teria correlação de "
                           f"cerca de **{f(teto, 2)}** com ela (teto realista). Compare os modelos com esse valor, não com 1."]
        linhas.append("")

    # correlação entre os modelos (os modelos concordam entre si?)
    nomes = list(modelos)
    if len(nomes) > 1:
        ps = [p for p in pares if p["fonte"] == "nossa"]
        linhas += ["## Concordância entre os modelos (Spearman, corpus próprio)", "",
                   "| | " + " | ".join(nomes) + " |", "|---|" + "--:|" * len(nomes)]
        for a in nomes:
            linhas.append(f"| {a} | " + " | ".join(
                f(correlacoes([modelos[a].get(chave(p), float('nan')) for p in ps],
                              [modelos[b].get(chave(p), float('nan')) for p in ps])["spearman"], 2) for b in nomes) + " |")
        linhas.append("")

    # maiores discordâncias entre o melhor modelo e a nota humana
    melhor = max(modelos, key=lambda n: np.nan_to_num(correlacoes(
        [modelos[n].get(chave(p), float("nan")) for p in pares if p["fonte"] == "nossa"],
        [p["ouro"] for p in pares if p["fonte"] == "nossa"])["spearman"], nan=-9))
    ps = [p for p in pares if p["fonte"] == "nossa"]
    sc = np.array([modelos[melhor].get(chave(p), float("nan")) for p in ps])
    humano = np.array([p["ouro"] for p in ps])
    ok = ~np.isnan(sc)
    if ok.sum() > 10:
        rk = lambda v: np.argsort(np.argsort(v)) / (len(v) - 1)   # posto normalizado em [0, 1]
        dif = rk(sc[ok]) - rk(humano[ok])
        idx = np.where(ok)[0][np.argsort(-np.abs(dif))[:8]]
        linhas += [f"## Maiores divergências do melhor modelo (`{melhor}`) em relação aos humanos", "",
                   "| par | nota humana | score do modelo | modelo acha |", "|---|--:|--:|---|"]
        for i in idx:
            d = rk(sc[ok])[list(np.where(ok)[0]).index(i)] - rk(humano[ok])[list(np.where(ok)[0]).index(i)]
            linhas.append(f"| {ps[i]['palavra_1']} – {ps[i]['palavra_2']} | {humano[i]:.1f} | {sc[i]:.3f} | {'mais similar' if d > 0 else 'menos similar'} |")
        linhas.append("")
    ARQ_ANALISE.write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))
    print(f"\n-> {ARQ_ANALISE.relative_to(RAIZ)}")


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modelos", nargs="*", default=[], choices=["contextos", "spacy", "bert", "llm"])
    ap.add_argument("--bert-modelos", nargs="*", default=MODELOS_BERT)
    ap.add_argument("--llm-backend", choices=["anthropic", "hf"], default="anthropic")
    ap.add_argument("--llm-modelo", default=None, help="padrão: claude-haiku-4-5-20251001 (anthropic) ou Qwen/Qwen2.5-3B-Instruct (hf)")
    ap.add_argument("--dataset-aula", default=None, help="CSV do dataset da aula (palavra_1, palavra_2, similaridade)")
    ap.add_argument("--so-analise", action="store_true")
    args = ap.parse_args()

    pares = ler_pares(args.dataset_aula)
    if not args.so_analise:
        if "contextos" in args.modelos:
            print("Contextos no corpus:"); montar_contextos(palavras_dos_pares(pares))
        if "spacy" in args.modelos:
            print("spaCy pt_core_news_lg:"); salvar_previsoes("spacy", pares, prever_spacy(pares))
        if "bert" in args.modelos:
            for nome in args.bert_modelos:
                print(f"BERT {nome}:")
                for variante, scores in prever_bert(pares, nome).items():
                    salvar_previsoes(f"{slug(nome)}-{variante}", pares, scores)
        if "llm" in args.modelos:
            modelo = args.llm_modelo or ("claude-haiku-4-5-20251001" if args.llm_backend == "anthropic" else "Qwen/Qwen2.5-3B-Instruct")
            print(f"LLM {modelo} ({args.llm_backend}):")
            fn = prever_llm_anthropic if args.llm_backend == "anthropic" else prever_llm_hf
            salvar_previsoes(f"llm-{slug(modelo)}", pares, fn(pares, modelo))
    analisar(pares)


if __name__ == "__main__":
    main()
