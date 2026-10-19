"""Coleta os assuntos em alta no X (Brasil) e grava noticias/trends.json.
Fontes públicas, sem login: trends24.in e, se falhar, getdaytrends.com. Roda no GitHub Actions.
Não usa a API do X (paga). Cada trend: nome, volume (quando houver), posição, link de busca no X."""
import html, json, os, re, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
BRT = timezone(timedelta(hours=-3))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "noticias", "trends.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", "Accept-Language": "pt-BR,pt;q=0.9"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def limpa(s): return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

def vol(txt):
    m = re.search(r"([\d.,]+)\s*([KkMm]?)", txt or "")
    if not m: return None
    n = float(m.group(1).replace(".", "").replace(",", ".")) if m.group(2) == "" else float(m.group(1).replace(",", "."))
    return int(n * (1000 if m.group(2).lower() == "k" else 1_000_000 if m.group(2).lower() == "m" else 1))

def trends24():
    h = get("https://trends24.in/brazil/")
    bloco = re.search(r'<ol class="trend-card__list">(.*?)</ol>', h, re.S)
    if not bloco: raise RuntimeError("trends24: lista não encontrada")
    out = []
    for li in re.findall(r"<li[^>]*>(.*?)</li>", bloco.group(1), re.S):
        nome = re.search(r'class="trend-link"[^>]*>(.*?)</a>', li, re.S)
        if not nome: continue
        cnt = re.search(r'data-count="(\d+)"', li) or re.search(r'class="tweet-count"[^>]*>(.*?)<', li, re.S)
        v = int(cnt.group(1)) if cnt and cnt.group(1).isdigit() else vol(cnt.group(1) if cnt else "")
        out.append({"nome": limpa(nome.group(1)), "volume": v or None})
    return out, "trends24.in"

def getdaytrends():
    h = get("https://getdaytrends.com/brazil/")
    out = []
    for row in re.findall(r'<td class="main">(.*?)</td>', h, re.S)[:50]:
        nome = re.search(r"<a[^>]*>(.*?)</a>", row, re.S)
        if not nome: continue
        v = re.search(r"([\d.,]+\s*[KkMm]?)\s*(tweets|posts)", row)
        out.append({"nome": limpa(nome.group(1)), "volume": vol(v.group(1)) if v else None})
    if not out: raise RuntimeError("getdaytrends: lista não encontrada")
    return out, "getdaytrends.com"

erros = []
for f in (trends24, getdaytrends):
    try:
        lista, fonte = f()
        if lista: break
    except Exception as e:
        erros.append(f"{f.__name__}: {str(e)[:150]}"); lista, fonte = [], None
if not lista:
    print("::warning::Não consegui ler os trends do X: " + " | ".join(erros)); sys.exit(0)
vistos, trends = set(), []
for i, t in enumerate(lista):
    k = t["nome"].lower()
    if k in vistos: continue
    vistos.add(k)
    t["posicao"] = len(trends) + 1
    t["url"] = "https://x.com/search?q=" + urllib.parse.quote(t["nome"])
    trends.append(t)
    if len(trends) >= 50: break
json.dump({"coletado": datetime.now(BRT).replace(microsecond=0).isoformat(), "fonte": fonte, "trends": trends},
          open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(trends)} trends de {fonte}: " + ", ".join(t["nome"] for t in trends[:10]))
