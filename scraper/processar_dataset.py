#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transforma os .txt de dataset/raw.zip (saída de `pdftotext -layout`) em questões estruturadas.

Etapas:
  1. separa as colunas de cada página (o -layout intercala provas em duas colunas)
  2. remove cabeçalhos/rodapés, recorta a seção de conhecimentos específicos
  3. segmenta questões, separa enunciado de alternativas, junta o gabarito
  4. descarta questões com problema de conversão (ver dataset/descartes.csv)
  5. organiza por subárea (redes, seguranca, sistemas) e por ano

Uso (a partir da raiz do repositório):
    python scraper/processar_dataset.py
"""
import csv
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import scraper_pci as sp  # reaproveita segmentação de questões, alternativas e gabarito

RAIZ = Path(__file__).resolve().parent.parent
ZIP_RAW = RAIZ / "dataset" / "raw.zip"
DIR_SAIDA = RAIZ / "dataset"

RE_LIXO = re.compile(r"pcimark|pciconcursos|^\s*p[áa]gina\s+\d+(\s+de\s+\d+)?\s*$", re.I)
# cabeçalho corrido que pode dividir a linha com texto de outra coluna: apaga só o trecho
RE_CABECALHO = re.compile(r"(?i:conhecimentos\s+espec[íi]ficos_.*?_(?:superior|m[ée]dio)\b)|"
                          r"[A-ZÀ-Ú][\wÀ-ú]+(?: [\wÀ-ú–-]+){0,8}_(?:Superior|M[ée]dio)\b")
# conteúdo de orçamento público que vem junto com a parte específica de alguns concursos (ex.: MPO/Cebraspe)
RE_FORA_DOMINIO = re.compile(r"\b(or[çc]ament[aáoí]\w*|lei de responsabilidade fiscal|\bLDO\b|\bLOA\b|\bLRF\b|"
                             r"cr[ée]ditos? (adicional|suplementar|especial|extraordin[áa]rio)|receita p[úu]blica|"
                             r"despesa p[úu]blica|dívida p[úu]blica|pol[íi]tica fiscal)", re.I)
RE_JULGUE = re.compile(r"\bjulgue\b", re.I)
RE_FIGURA = re.compile(r"\b(figura|imagem|gr[áa]fico|diagrama|ilustra[çc][ãa]o|print|captura de tela)\b", re.I)


# ---------------------------------------------------------------- entrada
class ArquivoZip:
    """Arquivo de texto dentro de raw.zip, com a mesma interface mínima de Path (name, read_text)."""

    def __init__(self, zf, name):
        self.zf, self.name = zf, name

    def read_text(self, encoding="utf-8", errors="strict"):
        return self.zf.read(self.name).decode(encoding, errors)


def listar_raw():
    zf = zipfile.ZipFile(ZIP_RAW)
    return [ArquivoZip(zf, n) for n in sorted(zf.namelist()) if n.endswith(".txt")]


# ---------------------------------------------------------------- metadados
def ano_do_slug(slug):
    anos = re.findall(r"(?<!\d)(20[12]\d)(?!\d)", slug)
    return int(anos[0]) if anos else None


def subarea_do_slug(slug):
    """Mesma prioridade das listagens do scraper: seguranca > redes > sistemas."""
    s = slug
    if "producao-animal" in s or "producao-vegetal" in s:
        return None  # Embrapa/ciências agrárias: "sistemas" aqui não é TI
    if "seguranca" in s or "ciberneti" in s:
        return "seguranca"
    if "redes" in s or "infraestrutura" in s:
        return "redes"
    if "sistemas" in s or "desenvolvimento" in s or "tecnologia-da-informacao" in s:
        return "sistemas"
    return None


# ---------------------------------------------------------------- colunas
def separar_colunas(pagina):
    """Divide uma página do -layout em coluna esquerda + direita, se houver um vão vertical."""
    linhas = [l.expandtabs(8).rstrip() for l in pagina.split("\n")]
    cheias = [l for l in linhas if l.strip()]
    if len(cheias) < 15:
        return pagina
    largura = max(len(l) for l in cheias)
    lo, hi = int(largura * 0.30), int(largura * 0.70)
    ocup = [sum(1 for l in cheias if len(l) > x and l[x] != " ") for x in range(largura)]
    limite = max(3, int(0.10 * len(cheias)))
    # maior corrida de colunas quase vazias na faixa central
    melhor, ini = (0, 0), None
    for x in range(lo, hi + 1):
        if ocup[x] <= limite:
            ini = x if ini is None else ini
            if x - ini + 1 > melhor[0]:
                melhor = (x - ini + 1, ini)
        else:
            ini = None
    largura_vao, ini = melhor
    if largura_vao < 2:
        return pagina
    corte = ini + largura_vao // 2
    esq = sum(1 for l in cheias if l[:corte].strip())
    dir_ = sum(1 for l in cheias if l[corte:].strip())
    if esq < 0.25 * len(cheias) or dir_ < 0.25 * len(cheias):
        return pagina
    return "\n".join(l[:corte].rstrip() for l in linhas) + "\n" + "\n".join(l[corte:].strip() for l in linhas)


def texto_prova(caminho):
    """Texto da prova com colunas separadas e sem cabeçalho/rodapé; páginas separadas por \\f."""
    # remove marca d'água/cabeçalhos ANTES de separar colunas (o corte os fragmentaria)
    em_branco = lambda m: " " * len(m.group(0))
    brutas = ["\n".join(RE_CABECALHO.sub(em_branco, l) for l in p.split("\n") if not RE_LIXO.search(l))
              for p in caminho.read_text(encoding="utf-8", errors="replace").split("\f")]
    paginas = [separar_colunas(p) for p in brutas]
    chave = lambda l: re.sub(r"\d+", "#", l.strip().lower())
    # marcadores de questão/alternativa e linhas curtas repetem por natureza: nunca são cabeçalho
    protegida = lambda l: len(l.strip()) < 16 or bool(re.match(r"\s*(quest[ãa]o\b|\(?[a-e]\s*[).])", l, re.I))
    cont = Counter()
    for p in paginas:
        cont.update({chave(l) for l in p.splitlines() if l.strip() and not l.strip().isdigit() and not protegida(l)})
    limite = max(3, 0.4 * len(paginas))
    repetidas = {k for k, v in cont.items() if v >= limite}
    limpas = []
    for p in paginas:
        ls = [l for l in p.splitlines()
              if not RE_LIXO.search(l) and (l.strip().isdigit() or chave(l) not in repetidas)]
        limpas.append("\n".join(ls))
    return "\f".join(limpas)


# ---------------------------------------------------------------- seção
RE_FAIXA = re.compile(r"conhecimentos?\s+espec[íi]ficos?[^\n\d]{0,80}?\b(\d{1,3})\s*(?:a|à|ao|–|-)\s*(\d{1,3})\b", re.I)


def faixa_especificos(texto):
    """Faixa de números das questões específicas, lida do sumário da capa ('... 31 a 60')."""
    for m in RE_FAIXA.finditer(texto[:6000]):
        a, b = int(m.group(1)), int(m.group(2))
        if 5 <= b - a + 1 <= 100:
            return a, b
    return None


RE_QUESTAO = re.compile(r"^[ \t]*quest[ãa]o\s*(?:n[º°o.]?\s*)?(\d{1,3})\b[ \t]*[.\-–—:)]?[ \t]*", re.I | re.M)


def segmentar(texto, inicio=0, fim=None):
    """Prefere marcadores explícitos ('QUESTÃO 26'); números soltos (páginas, itens) enganam a cadeia genérica."""
    fim = len(texto) if fim is None else fim
    cands = [(m.start(), int(m.group(1)), m.end()) for m in RE_QUESTAO.finditer(texto, inicio, fim)]
    cadeia = sp.maior_sequencia(cands)
    if len(cadeia) < 5:
        return sp.segmentar_questoes(texto, inicio, fim)
    questoes = []
    for k, idx in enumerate(cadeia):
        pos, num, fim_marca = cands[idx]
        prox = cands[cadeia[k + 1]][0] if k + 1 < len(cadeia) else fim
        corpo = texto[fim_marca:prox]
        if k + 1 == len(cadeia):           # última questão: corta lixo após mudança de página
            corpo = corpo[:4000]
        questoes.append((num, corpo))
    return questoes


def segmentar_especificas(texto):
    faixa = faixa_especificos(texto)
    if faixa:
        qs = [(n, c) for n, c in segmentar(texto) if faixa[0] <= n <= faixa[1]]
        if len(qs) >= 5:
            return qs
    secao = sp.recortar_especificos(texto)
    return segmentar(texto, *secao) if secao else None


# ---------------------------------------------------------------- gabarito
RE_NUM_CARGO = re.compile(r"cargo\s*(\d+)\s*[:\-–]", re.I)


def gabarito_por_blocos(texto, titulo):
    """Gabaritos com vários cargos: separa em blocos por cabeçalho e escolhe o do cargo da prova.

    Diferente de sp.parse_gabarito: o cabeçalho de um bloco sem pares (ex.: 'CARGO 7: ...') é carregado
    para o bloco seguinte (a tabela costuma vir sob outro título, como 'GABARITOS OFICIAIS'), e blocos do
    mesmo cargo espalhados em várias páginas são unidos. Só aceita se houver um único melhor cargo.
    """
    alvo = sp.palavras_titulo(titulo)
    blocos, cab, corpo, carga = [], [], [], []
    for l in texto.splitlines():
        tem_par = bool(sp.RE_PAR.search(l)) or len(re.findall(r"\b[A-E]\b", l)) >= 3
        if not tem_par and len(re.findall(r"[A-Za-zÀ-ú]{3,}", l)) >= 2:
            if corpo:
                if sp.resolver_pares(sp.pares_gabarito("\n".join(corpo)))[2] >= 3:
                    blocos.append((" ".join(carga + cab), "\n".join(corpo)))
                    carga = []
                else:                       # corpo sem tabela: o cabeçalho vale para o próximo bloco
                    carga = carga + cab
                cab, corpo = [], []
            cab.append(l)
        else:
            corpo.append(l)
    if corpo and sp.resolver_pares(sp.pares_gabarito("\n".join(corpo)))[2] >= 3:
        blocos.append((" ".join(carga + cab), "\n".join(corpo)))

    grupos = {}
    for cabecalho, corpo_b in blocos:
        m = RE_NUM_CARGO.search(cabecalho)
        chave = m.group(1) if m else cabecalho
        g = grupos.setdefault(chave, {"cab": "", "pares": []})
        g["cab"] += " " + cabecalho
        g["pares"] += sp.pares_gabarito(corpo_b)
    pontuados = []
    for chave, g in grupos.items():
        resp, conflitos, total = sp.resolver_pares(g["pares"])
        score = len(alvo & sp.palavras_titulo(g["cab"]))
        if score >= 2 and len(resp) >= 10 and conflitos / max(total, 1) <= 0.15:
            pontuados.append((score, resp))
    if not pontuados:
        return {}
    topo = max(s for s, _ in pontuados)
    melhores = [r for s, r in pontuados if s == topo]
    return melhores[0] if len(melhores) == 1 else {}


# ---------------------------------------------------------------- principal
def escolher_arquivos(arquivos):
    gabs = [a for a in arquivos if "gabarito" in a.name.lower()]
    provas = [a for a in arquivos if a not in gabs]
    if not provas or not gabs:
        return None, None
    gab = next((g for g in gabs if re.search(r"defin|final|pos_recurso", g.name.lower())), gabs[-1])
    return provas[0], gab


def main():
    por_prova = defaultdict(list)
    for t in listar_raw():
        por_prova[t.name.split("__")[0]].append(t)

    saida, descartes = [], []
    provas_usadas = {}
    vistos = set()

    def descartar(slug, num, motivo):
        descartes.append({"prova": slug, "numero": num, "motivo": motivo})

    for slug, arquivos in por_prova.items():
        sub, ano = subarea_do_slug(slug), ano_do_slug(slug)
        if sub is None or ano is None:
            descartar(slug, "", "fora do escopo (subárea/ano não identificados)")
            continue
        arq_prova, arq_gab = escolher_arquivos(arquivos)
        if arq_prova is None:
            descartar(slug, "", "sem prova ou sem gabarito")
            continue
        titulo = slug.rsplit("-", 2)[0].replace("-", " ")
        texto_gab = arq_gab.read_text(encoding="utf-8", errors="replace")
        respostas, motivo = sp.parse_gabarito(texto_gab, titulo)
        if motivo:   # vários cargos: tenta o separador por blocos
            respostas = gabarito_por_blocos(texto_gab, titulo)
            motivo = None if respostas else motivo
        if motivo:
            descartar(slug, "", motivo)
            continue
        texto = texto_prova(arq_prova)
        if len(texto.replace("\f", "").strip()) < 500:
            descartar(slug, "", "PDF sem texto (provavelmente escaneado)")
            continue
        questoes = segmentar_especificas(texto)
        if questoes is None:
            descartar(slug, "", "seção de conhecimentos específicos não encontrada")
            continue
        if len(questoes) < 5:
            descartar(slug, "", "não foi possível separar as questões")
            continue

        # o gabarito precisa corresponder à prova: arquivo errado (ex.: outro caderno) rende "respostas"
        # espúrias, que coincidem com alguns números de questão e produziriam gabaritos falsos
        numeros = [n for n, _ in questoes]
        cobertura = sum(n in respostas for n in numeros) / len(numeros)
        validas = [respostas[n] for n in numeros if n in respostas and respostas[n] != "ANULADA"]
        dominante = max(Counter(validas).values()) / len(validas) if validas else 1
        if cobertura < 0.6 or (dominante > 0.7 and len(validas) >= 10):
            descartar(slug, "", "gabarito não corresponde à prova (cobertura baixa ou letras implausíveis)")
            continue

        certo_errado = set(respostas.values()) <= {"C", "E", "ANULADA"}
        n_ok = 0
        for num, corpo in questoes:
            prob = sp.problema_de_conversao(corpo)
            if prob:
                descartar(slug, num, prob)
                continue
            resp = respostas.get(num)
            if resp is None:
                descartar(slug, num, "questão sem resposta no gabarito")
                continue
            if resp == "ANULADA":
                descartar(slug, num, "questão anulada")
                continue
            if certo_errado:
                enunciado, opcoes = sp.limpar(corpo), [("C", "Certo"), ("E", "Errado")]
                # Cebraspe: o item pode vir seguido da introdução do próximo bloco ("Acerca de X, julgue ...")
                m = RE_JULGUE.search(enunciado)
                if m:
                    ini = max(enunciado.rfind(". ", 0, m.start()), enunciado.rfind("? ", 0, m.start()))
                    enunciado = enunciado[:ini + 1].strip() if ini >= 0 else ""
            else:
                enunciado, opcoes = sp.separar_opcoes(corpo)
                if len(opcoes) not in (4, 5):
                    descartar(slug, num, "alternativas não encontradas")
                    continue
                if resp not in {l for l, _ in opcoes}:
                    descartar(slug, num, "resposta fora das alternativas")
                    continue
                if any(not t for _, t in opcoes):
                    descartar(slug, num, "alternativa vazia")
                    continue
            if len(enunciado) < 20:
                descartar(slug, num, "enunciado muito curto")
                continue
            if RE_FORA_DOMINIO.search(enunciado):
                descartar(slug, num, "fora do domínio (orçamento público)")
                continue
            if RE_FIGURA.search(enunciado):
                descartar(slug, num, "depende de figura/imagem")
                continue
            chave = sp.sem_acento(enunciado.lower())[:300] + "|" + "|".join(t.lower()[:60] for _, t in opcoes)
            if chave in vistos:
                descartar(slug, num, "duplicada")
                continue
            vistos.add(chave)
            saida.append({
                "id": f"{slug}#{num}", "subarea": sub, "ano": ano, "prova": slug, "numero": num,
                "tipo": "certo_errado" if certo_errado else "multipla_escolha",
                "enunciado": enunciado,
                "alternativas": {l: t for l, t in opcoes},
                "gabarito": resp,
            })
            n_ok += 1
        provas_usadas[slug] = (sub, ano, n_ok)
        print(f"{slug[:90]:90s} {sub:9s} {ano} {n_ok:3d}")

    # ---- gravação: um arquivo geral + um por subárea/ano
    DIR_SAIDA.mkdir(exist_ok=True)
    escrever_jsonl(DIR_SAIDA / "questoes.jsonl", saida)
    grupos = defaultdict(list)
    for q in saida:
        grupos[(q["subarea"], q["ano"])].append(q)
    for (sub, ano), qs in grupos.items():
        (DIR_SAIDA / sub).mkdir(exist_ok=True)
        escrever_jsonl(DIR_SAIDA / sub / f"{ano}.jsonl", qs)
    with open(DIR_SAIDA / "descartes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["prova", "numero", "motivo"])
        w.writeheader()
        w.writerows(descartes)

    print(f"\n{len(saida)} questões em {DIR_SAIDA}")
    print("Por subárea:", dict(Counter(q["subarea"] for q in saida)))
    print("Por ano:", dict(sorted(Counter(q["ano"] for q in saida).items())))
    print("Descartes:")
    for m, n in Counter(d["motivo"] for d in descartes).most_common():
        print(f"  {n:5d}  {m}")


def escrever_jsonl(caminho, registros):
    with open(caminho, "w", encoding="utf-8") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
