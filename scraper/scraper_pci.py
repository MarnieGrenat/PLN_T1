#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coleta de questões de concurso do PCI Concursos (Trabalho 1 - PLN).

Saída principal: dados/questoes.csv com as colunas
    subarea, questao, opcoes, resposta

Etapas (rode em ordem):
    python scraper_pci.py listar    # lê as listagens das 3 subáreas + buscas extras -> dados/provas.csv
    python scraper_pci.py baixar    # baixa prova + gabarito (abre um navegador)
    python scraper_pci.py manual    # alternativa ao "baixar": você baixa no seu navegador
    python scraper_pci.py extrair   # lê os PDFs e gera dados/questoes.csv

Dependências:
    pip install requests beautifulsoup4 pdfplumber playwright
    playwright install chromium

Observações:
  - Cada prova tem uma verificação de segurança (Cloudflare Turnstile). A etapa
    "baixar" abre um navegador visível; clique na verificação quando ela
    aparecer e o script continua sozinho. O script NÃO tenta burlar a verificação.
  - Também dá para baixar PDFs manualmente: coloque-os em
    dados/pdfs/<slug-da-prova>/ (o slug é a última parte da URL da prova,
    veja dados/provas.csv) e rode só "extrair".
"""
import argparse
import bisect
import csv
import json
import random
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urljoin

# ---------------------------------------------------------------- configuração
BASE = "https://www.pciconcursos.com.br"
SUBAREAS = {  # a ordem define a prioridade quando --manter-sobrepostas é usado
    "seguranca": f"{BASE}/provas/seguranca-da-informacao",
    "redes": f"{BASE}/provas/redes-de-computadores",
    "sistemas": f"{BASE}/provas/analista-de-sistemas",
}
# No PCI, /provas/<termos> é uma busca por palavras no nome do cargo. As listagens
# acima são aceitas inteiras; as buscas abaixo ampliam a coleta, mas cada prova
# delas só entra numa subárea se o título casar com o padrão em TITULO_SUBAREA
# (evita "Segurança do Trabalho", "Redes Sociais" etc.).
BUSCAS_EXTRAS = [
    "seguranca-cibernetica", "ciberseguranca", "seguranca-de-ti", "seguranca-de-redes",
    "seguranca-da-tecnologia-da-informacao", "analista-de-seguranca",
    "redes", "analista-de-redes", "tecnico-em-redes", "administrador-de-redes",
    "infraestrutura", "analista-de-suporte", "telematica",
    "analise-de-sistemas", "analista-de-sistema", "desenvolvimento-de-sistemas",
    "desenvolvedor", "engenharia-de-software", "analista-de-ti",
    "tecnologia-da-informacao",   # busca ampla (~50 páginas): pega "Analista de TI - Redes" etc.
]
TITULO_SUBAREA = {  # aplicados ao título sem acento e em minúsculas
    "seguranca": re.compile(
        r"ciber|seguranca\s+(da\s+|de\s+|em\s+)?(informacao|ti\b|tecnologia|redes|sistemas|dados|"
        r"computacional|digital)|\b(redes|infraestrutura|ti|sistemas)\s*(e|,|/)\s*seguranca\b"
        r"(?!\s+(do|no)\s+trabalho|\s+publica|\s+patrimonial)"),
    "redes": re.compile(
        r"^(?!.*eletricista)(.*\bredes?\b(?!\s+sociais|\s+d[ea]\s+(saude|atencao|ensino|esgoto|agua|distribuicao|frio|lojas)))|"
        r"infraestrutura\s+(de\s+|em\s+)?(ti\b|tecnologia|redes|computacional)|"
        r"comunicacao\s+de\s+dados|conectividade|telematica"),
    "sistemas": re.compile(
        r"anali(se|sta)\s+(de\s+)?sistemas?\b|desenvolvimento\s+(de\s+)?(sistemas|software)|"
        r"desenvolvedor|engenh(aria|eiro)\s+de\s+software"),
}
ANO_MIN_PADRAO = 2020          # "últimos 6 anos"
PAUSA = 1.5                    # segundos entre requisições (seja gentil com o site)
HEADERS = {"User-Agent": "Mozilla/5.0 (coleta academica - trabalho de PLN PUCRS)"}

DIR_DADOS = Path("dados")
DIR_PDFS = DIR_DADOS / "pdfs"
ARQ_PROVAS = DIR_DADOS / "provas.csv"
ARQ_QUESTOES = DIR_DADOS / "questoes.csv"
ARQ_COMPLETO = DIR_DADOS / "questoes_completo.csv"
ARQ_DESCARTES = DIR_DADOS / "descartes.csv"


# ---------------------------------------------------------------- utilidades
def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def nome_seguro(nome: str) -> str:
    return re.sub(r"[^\w.\-]", "_", nome).strip("_") or "arquivo.pdf"


def limpar(texto: str) -> str:
    texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)    # junta palavras hifenizadas na quebra
    texto = texto.replace("\f", " ")
    return re.sub(r"\s+", " ", texto).strip()


def carregar_provas():
    if not ARQ_PROVAS.exists():
        sys.exit(f"{ARQ_PROVAS} não existe. Rode primeiro: python scraper_pci.py listar")
    with open(ARQ_PROVAS, encoding="utf-8") as f:
        provas = list(csv.DictReader(f))
    for p in provas:
        p["subareas"] = [s for s in p["subareas"].split(";") if s]
        p["ano"] = int(p["ano"]) if p["ano"] else None
    return provas


def faltando(prova):
    """O que ainda falta baixar da prova: lista com "prova" e/ou "gabarito"."""
    pasta = DIR_PDFS / prova["slug"]
    pdfs = list(pasta.glob("*.pdf")) if pasta.exists() else []
    gabs = [p for p in pdfs if "gabarito" in sem_acento(p.name.lower())]
    falta = []
    if len(gabs) == len(pdfs):
        falta.append("prova")
    if not gabs:
        falta.append("gabarito")
    return falta


def selecionar_provas(args):
    """Filtra por ano e resolve provas que aparecem em mais de uma subárea."""
    escolhidas, puladas = [], 0
    for p in carregar_provas():
        if p["ano"] is None or p["ano"] < args.ano_min:
            continue
        if len(p["subareas"]) > 1 and not args.manter_sobrepostas:
            puladas += 1
            continue
        p["subarea"] = next(s for s in SUBAREAS if s in p["subareas"])
        escolhidas.append(p)
    if puladas:
        print(f"[info] {puladas} provas aparecem em mais de uma subárea e foram ignoradas "
              f"(use --manter-sobrepostas para incluí-las)")
    if args.max_por_subarea:
        # mais recentes primeiro; as já baixadas sempre entram (não desperdiça o que existe)
        escolhidas.sort(key=lambda p: (bool(faltando(p)), -p["ano"]))
        cont = Counter()
        filtradas = []
        for p in escolhidas:
            if not faltando(p) or cont[p["subarea"]] < args.max_por_subarea:
                cont[p["subarea"]] += 1
                filtradas.append(p)
        escolhidas = filtradas
    if args.limite:
        escolhidas = escolhidas[: args.limite]
    return escolhidas


# ================================================================ 1. LISTAR
def listar(args):
    import requests
    from bs4 import BeautifulSoup

    sess = requests.Session()
    sess.headers.update(HEADERS)
    provas = {}

    def baixar_pagina(url):
        for tentativa in range(4):
            try:
                r = sess.get(url, timeout=30)
                if r.status_code == 404:
                    return None
                r.raise_for_status()
                return BeautifulSoup(r.content, "html.parser")
            except requests.RequestException as e:
                print(f"   erro ({e}), tentando de novo...")
                time.sleep(PAUSA * 2 ** (tentativa + 1))
        print(f"   desisti de {url}")
        return None

    def percorrer(url_base, rotulo, sub_fixa=None):
        """Lê todas as páginas de uma listagem. sub_fixa: subárea dada a todas as provas
        (listagem oficial); sem ela, a subárea vem só do título."""
        pagina, total, aceitas = 1, 0, 0
        while pagina <= args.max_paginas:
            url = url_base if pagina == 1 else f"{url_base}/{pagina}"
            soup = baixar_pagina(url)
            if soup is None:
                break
            linhas = [tr for tr in soup.select("tr") if tr.select_one('a[href*="/provas/download/"]')]
            if not linhas:
                break
            for tr in linhas:
                a = tr.select_one('a[href*="/provas/download/"]')
                href = urljoin(BASE, a["href"])
                slug = href.rstrip("/").split("/")[-1]
                titulo = a.get_text(" ", strip=True)
                tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                ano = next((int(t) for t in tds if re.fullmatch(r"(19|20)\d\d", t)), None)
                subs = [sub_fixa] if sub_fixa else []
                t = sem_acento(titulo.lower())
                subs += [s for s, rx in TITULO_SUBAREA.items() if rx.search(t)]
                total += 1
                if not subs:
                    continue
                aceitas += 1
                p = provas.setdefault(slug, {
                    "slug": slug, "url": href, "titulo": titulo, "ano": ano,
                    "orgao": tds[2] if len(tds) > 2 else "", "banca": tds[3] if len(tds) > 3 else "",
                    "subareas": [],
                })
                p["subareas"] += [s for s in subs if s not in p["subareas"]]

            # próxima página: link "Próxima" ou, na falta dele, um link numérico maior que a atual
            prox = soup.find("a", string=re.compile(r"Pr[óo]xima", re.I))
            tem_prox = prox is not None and prox.get("href", "#") not in ("#", "")
            if not tem_prox:
                caminho = url_base.split(BASE, 1)[-1]
                nums = [int(x.get_text(strip=True)) for x in soup.find_all("a", href=True)
                        if x.get_text(strip=True).isdigit() and caminho in x["href"]]
                tem_prox = any(n > pagina for n in nums)
            print(f"[{rotulo}] página {pagina}: {len(linhas)} provas")
            if not tem_prox:
                break
            pagina += 1
            time.sleep(PAUSA)
        print(f"[{rotulo}] {total} provas lidas, {aceitas} aceitas")
        time.sleep(PAUSA)

    for sub, url_base in SUBAREAS.items():
        percorrer(url_base, sub, sub_fixa=sub)
    buscas = BUSCAS_EXTRAS + [b.strip().strip("/") for b in args.buscas.split(",") if b.strip()]
    if not args.sem_buscas_extras:
        for termo in dict.fromkeys(buscas):
            percorrer(f"{BASE}/provas/{termo}", f"busca:{termo}")

    # mantém a ordem de prioridade de SUBAREAS dentro de cada prova
    for p in provas.values():
        p["subareas"] = [s for s in SUBAREAS if s in p["subareas"]]

    DIR_DADOS.mkdir(exist_ok=True)
    campos = ["slug", "url", "titulo", "ano", "orgao", "banca", "subareas"]
    with open(ARQ_PROVAS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for p in provas.values():
            w.writerow({**p, "subareas": ";".join(p["subareas"]), "ano": p["ano"] or ""})

    print(f"\n{len(provas)} provas únicas salvas em {ARQ_PROVAS}")
    for sub in SUBAREAS:
        tot = sum(sub in p["subareas"] for p in provas.values())
        rec = sum(sub in p["subareas"] and (p["ano"] or 0) >= args.ano_min for p in provas.values())
        so = sum(p["subareas"] == [sub] and (p["ano"] or 0) >= args.ano_min for p in provas.values())
        print(f"  {sub:10s} total={tot:4d}  desde {args.ano_min}={rec:4d}  (exclusivas={so})")


# ================================================================ 2. BAIXAR
# Como o site funciona (verificado em out/2026):
#   - cada página de prova tem uma verificação Cloudflare Turnstile;
#   - ao concluir, a página faz POST em /provas/link e recebe as URLs reais;
#   - os links "Baixar" (a.prova-pdf-link[data-acao=baixar]) passam a ter href.
# Uma verificação libera todos os arquivos daquela prova. O script só ESPERA
# os links serem liberados (por você ou automaticamente pelo navegador) — ele
# não tenta resolver nem contornar a verificação.
JS_LINKS = """() => [...document.querySelectorAll('a.prova-pdf-link[data-acao="baixar"]')]
    .map(a => ({arquivo: a.dataset.arquivo, href: a.href}))"""


def baixar(args):
    from playwright.sync_api import sync_playwright

    provas = selecionar_provas(args)
    pendentes = [p for p in provas if faltando(p)]
    so_gab = sum(faltando(p) == ["gabarito"] for p in pendentes)
    print(f"{len(provas)} provas selecionadas, {len(provas) - len(pendentes)} já baixadas, "
          f"{len(pendentes)} a baixar ({so_gab} só sem gabarito).\n")
    print("Uma janela do navegador vai abrir. Em cada prova, clique na verificação "
          "'Confirme que é humano' se ela aparecer; o script segue sozinho.\n"
          "Ctrl+C interrompe (o que já foi baixado fica salvo).\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        ctx = browser.new_context(locale="pt-BR")
        page = ctx.new_page()

        for i, prova in enumerate(pendentes, 1):
            print(f"[{i}/{len(pendentes)}] {prova['titulo']} ({prova['ano']}, {prova['banca']})")
            try:
                page.goto(prova["url"], wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                print(f"   erro ao abrir a página: {e}")
                continue

            links = page.evaluate(JS_LINKS)
            if not links:
                print("   nenhum arquivo listado")
                continue
            try:
                page.locator("#captcha-provas").scroll_into_view_if_needed(timeout=3000)
            except Exception:
                pass

            avisou, fim = False, time.time() + args.espera
            while time.time() < fim and any(l["href"].startswith("javascript") for l in links):
                if not avisou and time.time() > fim - args.espera + 3:
                    print("   aguardando a verificação na janela do navegador...")
                    avisou = True
                page.wait_for_timeout(1000)
                try:
                    links = page.evaluate(JS_LINKS)
                except Exception:
                    break
            if any(l["href"].startswith("javascript") for l in links):
                print(f"   links não liberados em {args.espera}s, pulando")
                continue

            destino = DIR_PDFS / prova["slug"]
            destino.mkdir(parents=True, exist_ok=True)
            for l in links:
                alvo = destino / nome_seguro(l["arquivo"])
                try:
                    r = ctx.request.get(l["href"], headers={"Referer": prova["url"]}, timeout=120000)
                    corpo = r.body() if r.ok else b""
                except Exception as e:
                    corpo = b""
                    print(f"   erro: {e}")
                if corpo[:4] == b"%PDF":
                    alvo.write_bytes(corpo)
                    print(f"   ok  {alvo.name} ({len(corpo) // 1024} KB)")
                else:
                    print(f"   FALHOU {alvo.name} (resposta não é PDF)")
                time.sleep(PAUSA)

        browser.close()
    print(f"\nPDFs em {DIR_PDFS}/. Próximo passo: python scraper_pci.py extrair")


# ================================================================ 2b. MANUAL
# Alternativa ao "baixar" quando a verificação falha no navegador controlado
# pelo Playwright: abre cada prova no seu navegador padrão, você faz a
# verificação e baixa os arquivos normalmente, e o script move os PDFs novos
# da pasta de downloads para dados/pdfs/<slug>/.
def manual(args):
    import shutil
    import webbrowser

    downloads = Path(args.downloads).expanduser()
    if not downloads.is_dir():
        sys.exit(f"Pasta de downloads não encontrada: {downloads} (use --downloads)")

    provas = selecionar_provas(args)
    pendentes = [p for p in provas if faltando(p)]
    so_gab = sum(faltando(p) == ["gabarito"] for p in pendentes)
    print(f"{len(provas)} provas selecionadas, {len(provas) - len(pendentes)} já baixadas, "
          f"{len(pendentes)} a baixar ({so_gab} só sem gabarito).")
    print(f"Os PDFs serão buscados em {downloads}\n"
          "Para cada prova: faça a verificação, clique em 'Baixar' na prova e no gabarito,\n"
          "espere os downloads terminarem e aperte Enter aqui.\n")

    for i, prova in enumerate(pendentes, 1):
        print(f"[{i}/{len(pendentes)}] {prova['titulo']} ({prova['ano']}, {prova['banca']})")
        print(f"   falta baixar: {' e '.join(faltando(prova))}")
        antes = {p: p.stat().st_mtime for p in downloads.glob("*.pdf")}
        webbrowser.open(prova["url"])
        try:
            r = input("   Enter = terminei | p = pular | q = sair: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if r == "q":
            break
        if r == "p":
            continue

        if any(downloads.glob("*.crdownload")) or any(downloads.glob("*.part")):
            print("   aviso: há downloads em andamento; eles serão ignorados")
        novos = [p for p in downloads.glob("*.pdf") if antes.get(p) != p.stat().st_mtime]
        if not novos:
            print("   nenhum PDF novo encontrado")
            continue
        destino = DIR_PDFS / prova["slug"]
        destino.mkdir(parents=True, exist_ok=True)
        for p in novos:
            alvo = destino / nome_seguro(p.name)
            shutil.move(str(p), alvo)
            print(f"   ok  {alvo.name}")
        if faltando(prova):
            print(f"   aviso: ainda falta {' e '.join(faltando(prova))} (o gabarito precisa ter "
                  "'gabarito' no nome); rode de novo para completar")

    print(f"\nPDFs em {DIR_PDFS}/. Próximo passo: python scraper_pci.py extrair")


# ================================================================ 3. EXTRAIR
# ---- PDF -> texto ----------------------------------------------------------
def texto_pagina(pg):
    """Extrai o texto de uma página, tratando layouts de duas colunas."""
    palavras = pg.extract_words()
    if not palavras:
        return ""
    x0, top, x1, bottom = pg.bbox
    largura = x1 - x0

    # procura, na faixa central da página, a posição x cortada pelo menor número de palavras
    # (o "vão" entre as colunas), preferindo a mais próxima do centro
    def cortes(x):
        return sum(1 for w in palavras if w["x0"] < x - 1 and w["x1"] > x + 1)

    centro = x0 + largura / 2
    xs = [x0 + largura * f / 100 for f in range(35, 66)]
    meio = min(xs, key=lambda x: (cortes(x), abs(x - centro)))
    cruzam = cortes(meio)
    esq = sum(1 for w in palavras if w["x1"] <= meio)
    dir_ = sum(1 for w in palavras if w["x0"] >= meio)
    if cruzam <= max(3, 0.03 * len(palavras)) and esq > 30 and dir_ > 30:
        e = pg.crop((x0, top, meio, bottom)).extract_text() or ""
        d = pg.crop((meio, top, x1, bottom)).extract_text() or ""
        return e + "\n" + d
    return pg.extract_text() or ""


def texto_pdf(caminho):
    """Texto do PDF inteiro, sem cabeçalhos/rodapés repetidos; páginas separadas por \\f."""
    import pdfplumber
    with pdfplumber.open(caminho) as pdf:
        paginas = [texto_pagina(pg) for pg in pdf.pages]

    # linhas que se repetem em muitas páginas = cabeçalho/rodapé
    chave = lambda l: re.sub(r"\d+", "#", l.strip().lower())
    cont = Counter()
    for t in paginas:
        cont.update({chave(l) for l in t.splitlines() if l.strip() and not l.strip().isdigit()})
    limite = max(3, 0.4 * len(paginas))
    repetidas = {k for k, v in cont.items() if v >= limite}
    num_pagina = re.compile(r"^\s*(p[áa]g(ina)?\.?\s*\d+(\s*(de|/)\s*\d+)?|\d+\s*(de|/)\s*\d+)\s*$", re.I)
    limpas = ["\n".join(l for l in t.splitlines()
                        if not num_pagina.match(l) and (l.strip().isdigit() or chave(l) not in repetidas))
              for t in paginas]
    return "\f".join(limpas)


# ---- seções -----------------------------------------------------------------
RE_INICIO_Q = re.compile(
    r"^[ \t]*(?:quest[ãa]o\s*(?:n[º°o.]?\s*)?)?(\d{1,3})(?=[ \t]*[.\-–—:)][ \t]|[ \t]*$|[ \t]+\S)[ \t]*[.\-–—:)]?[ \t]*",
    re.I | re.M)
RE_ESPECIFICOS = re.compile(
    r"conhecimentos?\s+(espec[íi]fic[oa]s?|t[ée]cnic[oa]s?)|parte\s+espec[íi]fica|"
    r"m[óo]dulo\s+espec[íi]fico|prova\s+espec[íi]fica|conte[úu]do\s+espec[íi]fico", re.I)
RE_OUTRAS_SECOES = re.compile(
    r"l[íi]ngua\s+portuguesa|portugu[êe]s|racioc[íi]nio\s+l[óo]gico|matem[áa]tica|legisla[çc][ãa]o|"
    r"conhecimentos\s+gerais|atualidades|l[íi]ngua\s+inglesa|ingl[êe]s|[ée]tica|no[çc][õo]es\s+de\s+direito|"
    r"direito\s+\w+|administra[çc][ãa]o\s+p[úu]blica|conhecimentos\s+b[áa]sicos|realidade\s+\w+", re.I)


def eh_cabecalho(texto, m):
    """O match está numa linha curta (título de seção) e há uma questão logo depois?"""
    ini = texto.rfind("\n", 0, m.start()) + 1
    fim = texto.find("\n", m.end())
    fim = len(texto) if fim == -1 else fim
    linha = texto[ini:fim].strip()
    if len(linha) > len(m.group(0)) + 35:
        return False
    return bool(RE_INICIO_Q.search(texto[m.end(): m.end() + 1200]))


def recortar_especificos(texto):
    """Devolve (inicio, fim) da seção de conhecimentos específicos, ou None."""
    candidatos = [m for m in RE_ESPECIFICOS.finditer(texto) if eh_cabecalho(texto, m)]
    if not candidatos:
        return None
    fora_capa = [m for m in candidatos if texto.count("\f", 0, m.start()) > 0]
    m = (fora_capa or candidatos)[0]
    inicio, fim = m.end(), len(texto)
    for o in RE_OUTRAS_SECOES.finditer(texto, inicio):
        if eh_cabecalho(texto, o):
            fim = o.start()
            break
    return inicio, fim


# ---- questões e alternativas -----------------------------------------------
def maior_sequencia(cands):
    """cands: lista (pos, valor, fim) com valores ordenáveis por 'proximo'.
    Retorna a maior cadeia de valores consecutivos em ordem de posição."""
    por_valor = defaultdict(list)
    for i, (pos, val, _) in enumerate(cands):
        por_valor[val].append((pos, i))
    melhor = []
    for i, (pos, val, _) in enumerate(cands):
        cadeia, atual_pos, atual_val = [i], pos, val
        while True:
            prox = atual_val + 1
            lista = por_valor.get(prox, [])
            k = bisect.bisect_right(lista, (atual_pos, len(cands)))
            if k >= len(lista):
                break
            atual_pos, idx = lista[k]
            atual_val = prox
            cadeia.append(idx)
        if len(cadeia) > len(melhor):
            melhor = cadeia
    return melhor


def segmentar_questoes(texto, inicio=0, fim=None):
    fim = len(texto) if fim is None else fim
    cands = [(m.start(), int(m.group(1)), m.end()) for m in RE_INICIO_Q.finditer(texto, inicio, fim)]
    cadeia = maior_sequencia(cands)
    questoes = []
    for k, idx in enumerate(cadeia):
        pos, num, fim_marca = cands[idx]
        prox = cands[cadeia[k + 1]][0] if k + 1 < len(cadeia) else fim
        corpo = texto[fim_marca:prox]
        if k + 1 == len(cadeia):           # última questão: corta lixo após mudança de página
            corpo = corpo[:4000]
        questoes.append((num, corpo))
    return questoes


RE_OPCAO = re.compile(r"(?:^|(?<=\s))\(?([A-Ea-e])\s*[)\.\-–]\s+", re.M)


def separar_opcoes(corpo):
    """Retorna (enunciado, [(letra, texto), ...]). Alternativas devem vir em ordem A, B, C, D[, E]."""
    cands = []
    for m in RE_OPCAO.finditer(corpo):
        ini_linha = corpo.rfind("\n", 0, m.start()) + 1
        if corpo[ini_linha:m.start()].strip():   # a letra precisa iniciar a linha
            continue
        cands.append((m.start(), ord(m.group(1).upper()) - ord("A"), m.end()))
    # só cadeias que começam em A
    melhor = []
    por_valor = defaultdict(list)
    for i, (pos, val, _) in enumerate(cands):
        por_valor[val].append((pos, i))
    for i, (pos, val, _) in enumerate(cands):
        if val != 0:
            continue
        cadeia, ap, av = [i], pos, 0
        while av < 4:
            lista = por_valor.get(av + 1, [])
            k = bisect.bisect_right(lista, (ap, len(cands)))
            if k >= len(lista):
                break
            ap, idx = lista[k]
            av += 1
            cadeia.append(idx)
        if len(cadeia) >= len(melhor):           # empate -> a última (alternativas vêm no fim)
            melhor = cadeia
    if len(melhor) < 4:
        return limpar(corpo), []
    enunciado = corpo[: cands[melhor[0]][0]]
    opcoes = []
    for k, idx in enumerate(melhor):
        _, val, fim_marca = cands[idx]
        prox = cands[melhor[k + 1]][0] if k + 1 < len(melhor) else len(corpo)
        txt = corpo[fim_marca:prox]
        if k + 1 == len(melhor):
            txt = txt.split("\f")[0][:800]       # última alternativa: não invade a próxima página
        opcoes.append((chr(ord("A") + val), limpar(txt)))
    return limpar(enunciado), opcoes


# ---- gabarito ---------------------------------------------------------------
TOK_RESP = r"(?:[A-E]|X|\*|ANULADA|Anulada|NULA|Nula|ANUL)"
RE_PAR = re.compile(r"(?<![\d.,/:])\b(\d{1,3})\s*[-–.:)=]?\s*(" + TOK_RESP + r")(?![A-Za-zÀ-ú\d])")


def pares_da_linha_tabela(l1, l2):
    t1, t2 = l1.split(), l2.split()
    nums = [t for t in t1 if t.isdigit()]
    resp = [t for t in t2 if re.fullmatch(TOK_RESP, t)]
    if len(nums) >= 3 and len(nums) == len(resp) and len(t1) - len(nums) <= 2 and len(t2) - len(resp) <= 2:
        return list(zip(map(int, nums), resp))
    return []


def pares_gabarito(texto):
    linhas = [l for l in texto.splitlines() if l.strip()]
    pares = []
    usadas = set()
    for i in range(len(linhas) - 1):
        p = pares_da_linha_tabela(linhas[i], linhas[i + 1])
        if p:
            pares += p
            usadas.update({i, i + 1})
    for i, l in enumerate(linhas):
        if i not in usadas:
            pares += [(int(n), r) for n, r in RE_PAR.findall(l)]
    return pares


def normalizar_resp(r):
    r = r.upper()
    return "ANULADA" if r in ("X", "*", "ANULADA", "NULA", "ANUL") else r


def resolver_pares(pares):
    por_num = defaultdict(set)
    for n, r in pares:
        por_num[n].add(normalizar_resp(r))
    conflitos = sum(len(v) > 1 for v in por_num.values())
    return {n: next(iter(v)) for n, v in por_num.items() if len(v) == 1}, conflitos, len(por_num)


def palavras_titulo(titulo):
    return {w for w in re.findall(r"\w+", sem_acento(titulo.lower())) if len(w) > 3}


def parse_gabarito(texto, titulo):
    """Retorna (dict num->resposta, motivo_de_falha_ou_None)."""
    resp, conflitos, total = resolver_pares(pares_gabarito(texto))
    if total and conflitos / total <= 0.15 and len(resp) >= 5:
        return resp, None

    # gabarito com vários cargos/tipos: separa em blocos por linhas de cabeçalho
    alvo = palavras_titulo(titulo)
    blocos, cab, corpo = [], [], []
    for l in texto.splitlines():
        tem_par = bool(RE_PAR.search(l)) or len(re.findall(r"\b[A-E]\b", l)) >= 3
        if not tem_par and len(re.findall(r"[A-Za-zÀ-ú]{3,}", l)) >= 2:
            if corpo:
                blocos.append((" ".join(cab), "\n".join(corpo)))
                cab, corpo = [], []
            cab.append(l)
        else:
            corpo.append(l)
    if corpo:
        blocos.append((" ".join(cab), "\n".join(corpo)))

    melhor, melhor_score = None, 0
    for cabecalho, corpo_b in blocos:
        score = len(alvo & palavras_titulo(cabecalho))
        r, c, t = resolver_pares(pares_gabarito(corpo_b))
        if score > melhor_score and len(r) >= 10 and c / max(t, 1) <= 0.15:
            melhor, melhor_score = r, score
    if melhor and melhor_score >= 2:
        return melhor, None
    return {}, "gabarito ambíguo (vários cargos/tipos) ou ilegível"


# ---- qualidade --------------------------------------------------------------
def problema_de_conversao(txt):
    if "(cid:" in txt or "\ufffd" in txt:
        return "caracteres corrompidos"
    estranhos = sum(1 for c in txt if not (c.isalnum() or c.isspace() or c in ".,;:!?()[]{}\"'-–—/\\%$#@&*+=<>_|ºª°§“”‘’…^~`"))
    if txt and estranhos / len(txt) > 0.05:
        return "muitos caracteres estranhos"
    return None


# ---- loop principal ---------------------------------------------------------
def extrair(args):
    provas = selecionar_provas(args)
    saida, descartes, vistos = [], [], set()

    def descartar(prova, num, motivo):
        descartes.append({"prova": prova["slug"], "subarea": prova["subarea"], "numero": num, "motivo": motivo})

    for i, prova in enumerate(provas, 1):
        pasta = DIR_PDFS / prova["slug"]
        pdfs = sorted(pasta.glob("*.pdf")) if pasta.exists() else []
        gabs = [p for p in pdfs if "gabarito" in sem_acento(p.name.lower())]
        provs = [p for p in pdfs if p not in gabs]
        if not provs:
            descartar(prova, "", "PDF da prova não baixado")
            continue
        if not gabs:
            descartar(prova, "", "sem gabarito")
            continue
        gab = next((g for g in gabs if "defin" in g.name.lower()), gabs[-1])
        arq_prova = provs[0]  # se houver vários cadernos/tipos, usa só o primeiro

        try:
            respostas, motivo = parse_gabarito(texto_pdf(gab), prova["titulo"])
            texto = texto_pdf(arq_prova)
        except Exception as e:
            descartar(prova, "", f"erro ao ler PDF: {e}")
            continue
        if motivo:
            descartar(prova, "", motivo)
            continue
        if len(texto.replace("\f", "").strip()) < 500:
            descartar(prova, "", "PDF sem texto (provavelmente escaneado)")
            continue

        secao = recortar_especificos(texto)
        if secao is None and not args.manter_sem_secao:
            descartar(prova, "", "seção de conhecimentos específicos não encontrada")
            continue
        ini, fim = secao or (0, len(texto))

        certo_errado = set(respostas.values()) <= {"C", "E", "ANULADA"}
        questoes = segmentar_questoes(texto, ini, fim)
        if len(questoes) < 5:
            descartar(prova, "", "não foi possível separar as questões")
            continue

        n_ok = 0
        for num, corpo in questoes:
            prob = problema_de_conversao(corpo)
            if prob:
                descartar(prova, num, prob)
                continue
            resp = respostas.get(num)
            if resp is None:
                descartar(prova, num, "questão sem resposta no gabarito")
                continue
            if resp == "ANULADA":
                descartar(prova, num, "questão anulada")
                continue

            if certo_errado:
                enunciado, opcoes = limpar(corpo), [("C", "Certo"), ("E", "Errado")]
                tipo = "certo_errado"
            else:
                enunciado, opcoes = separar_opcoes(corpo)
                tipo = "multipla_escolha"
                if len(opcoes) not in (4, 5):
                    descartar(prova, num, "alternativas não encontradas")
                    continue
                if resp not in {l for l, _ in opcoes}:
                    descartar(prova, num, "resposta fora das alternativas")
                    continue
                if any(len(t) == 0 for _, t in opcoes):
                    descartar(prova, num, "alternativa vazia")
                    continue
            if len(enunciado) < 20:
                descartar(prova, num, "enunciado muito curto")
                continue

            chave = sem_acento(enunciado.lower())[:300] + "|" + "|".join(t.lower()[:60] for _, t in opcoes)
            if chave in vistos:
                descartar(prova, num, "duplicada")
                continue
            vistos.add(chave)

            saida.append({
                "subarea": prova["subarea"],
                "questao": enunciado,
                "opcoes": json.dumps([f"{l}) {t}" for l, t in opcoes], ensure_ascii=False),
                "resposta": resp,
                "tipo": tipo, "numero": num, "ano": prova["ano"], "orgao": prova["orgao"],
                "banca": prova["banca"], "cargo": prova["titulo"], "prova": prova["slug"],
            })
            n_ok += 1
        print(f"[{i}/{len(provas)}] {prova['slug']}: {n_ok} questões")

    DIR_DADOS.mkdir(exist_ok=True)
    with open(ARQ_QUESTOES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["subarea", "questao", "opcoes", "resposta"], extrasaction="ignore")
        w.writeheader()
        w.writerows(saida)
    if saida:
        with open(ARQ_COMPLETO, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(saida[0].keys()))
            w.writeheader()
            w.writerows(saida)
    with open(ARQ_DESCARTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["prova", "subarea", "numero", "motivo"])
        w.writeheader()
        w.writerows(descartes)

    # resumo
    print(f"\n{len(saida)} questões salvas em {ARQ_QUESTOES} (metadados em {ARQ_COMPLETO})")
    por_sub = Counter(q["subarea"] for q in saida)
    for sub in SUBAREAS:
        aviso = "" if por_sub[sub] >= 500 else "  <-- abaixo de 500!"
        print(f"  {sub:10s} {por_sub[sub]:5d}{aviso}")
    print("Por ano:", dict(sorted(Counter(q["ano"] for q in saida).items())))
    print(f"\n{len(descartes)} descartes (detalhes em {ARQ_DESCARTES}):")
    for motivo, n in Counter(d["motivo"] for d in descartes).most_common():
        print(f"  {n:5d}  {motivo}")
    if saida:
        print("\nAmostra para conferência manual:")
        for q in random.sample(saida, min(3, len(saida))):
            print(f"  [{q['subarea']}] {q['questao'][:120]}... -> {q['resposta']}")


# ================================================================ CLI
def main():
    ap = argparse.ArgumentParser(description="Coleta de questões do PCI Concursos")
    ap.add_argument("etapa", choices=["listar", "baixar", "manual", "extrair"])
    ap.add_argument("--ano-min", type=int, default=ANO_MIN_PADRAO, help="ano mínimo das provas (padrão 2020)")
    ap.add_argument("--manter-sobrepostas", action="store_true",
                    help="inclui provas listadas em mais de uma subárea (usa a primeira por prioridade)")
    ap.add_argument("--manter-sem-secao", action="store_true",
                    help="mantém provas sem seção 'conhecimentos específicos' detectada (pode incluir português etc.)")
    ap.add_argument("--limite", type=int, default=0, help="processa só as N primeiras provas (para testar)")
    ap.add_argument("--max-por-subarea", type=int, default=0,
                    help="no máximo N provas por subárea, as mais recentes primeiro (0 = todas)")
    ap.add_argument("--max-paginas", type=int, default=500,
                    help="limite de páginas lidas por listagem/busca (etapa listar, padrão 500)")
    ap.add_argument("--buscas", default="",
                    help="termos de busca extras, separados por vírgula (ex.: analista-de-dados,devops)")
    ap.add_argument("--sem-buscas-extras", action="store_true",
                    help="lê só as 3 listagens oficiais, como antes (etapa listar)")
    ap.add_argument("--espera", type=int, default=180,
                    help="segundos esperando a verificação de cada prova antes de pular (padrão 180)")
    ap.add_argument("--downloads", default=str(Path.home() / "Downloads"),
                    help="pasta onde o seu navegador salva os downloads (etapa manual)")
    args = ap.parse_args()
    {"listar": listar, "baixar": baixar, "manual": manual, "extrair": extrair}[args.etapa](args)


if __name__ == "__main__":
    main()
