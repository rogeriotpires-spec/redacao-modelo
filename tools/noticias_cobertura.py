"""Depois da edição: confere nas manchetes coletadas (coleta-noticias.json) quais outros portais deram cada fato,
acrescenta esses portais à notícia e recalcula a nota de cobertura e a nota final pela regra do config.
Uso: python3 tools/noticias_cobertura.py noticias/AAAA-MM-DD-HHh.json coleta-noticias.json"""
import json, re, sys, unicodedata
ed_path, col_path = sys.argv[1], sys.argv[2]
cfg = json.load(open("noticias/config.json", encoding="utf-8"))
ed = json.load(open(ed_path, encoding="utf-8")); col = json.load(open(col_path, encoding="utf-8"))
STOP = set("""para pela pelo pelos pelas como mais menos sobre entre desde quando onde quem qual quais este esta isto esse essa isso
seus suas dele dela deles delas ainda depois antes agora hoje ontem amanha diz disse apos contra todo toda todos todas cada outro outra
muito pode podem deve sera foram fazer feito apenas mesmo mesma nunca sempre nada tudo vai vao veja entenda saiba video videos ao vivo
brasil governo""".split())
def kw(t):
    t = unicodedata.normalize("NFD", (t or "").lower()); t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return {w for w in re.findall(r"[a-z0-9]+", t) if (len(w) >= 4 or w.isdigit()) and w not in STOP}
camp = {o["name"]: o.get("camp") for o in cfg["outlets"]}
def nota_cob(n):
    pts = [(1, 2), (3, 5), (6, 8), (9, 10)]
    if n <= 0: return 0
    if n >= 9: return 10
    for (a, x), (b, y) in zip(pts, pts[1:]):
        if a <= n <= b: return round(x + (y - x) * (n - a) / (b - a), 1)
W = {"cobertura": 10, "destaque": 8, "persistencia": 6, "peso_voce": 7}
for c in cfg.get("criteria", []):
    k = c.get("key") or c.get("id")
    if k in W and c.get("weight"): W[k] = c["weight"]
acresc = 0
for it in ed.get("items", []):
    alvo = kw(it.get("title", "") + " " + (it.get("summary", "").split(". ")[0]))
    tem = {o["name"] for o in it.get("outlets", [])}
    for p in col.get("portais", []):
        if p["nome"] in tem: continue
        for m in p.get("manchetes", []):
            k = kw(m["titulo"]); inter = k & alvo
            if len(inter) >= 3 and len(inter) / max(1, len(k)) >= 0.5:
                it.setdefault("outlets", []).append({"name": p["nome"], "url": m.get("link", ""), "camp": camp.get(p["nome"], p.get("camp")), "position": "editoria", "via": "coleta"})
                tem.add(p["nome"]); acresc += 1; break
    sc = it.setdefault("scores", {}); sc["cobertura"] = max(sc.get("cobertura") or 0, nota_cob(len(it.get("outlets", []))))
    if all(k in sc for k in W): it["score"] = round(sum(sc[k] * W[k] for k in W) / sum(W.values()), 1)
top_n = cfg.get("top_overall", len(ed.get("top", [])) or 5)
ed["top"] = [x["id"] for x in sorted(ed.get("items", []), key=lambda x: x.get("score") or 0, reverse=True)[:top_n]]
ed["portais_na_coleta"] = sum(1 for p in col.get("portais", []) if p.get("manchetes"))
json.dump(ed, open(ed_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"cobertura: +{acresc} portais acrescentados; {len({o['name'] for it in ed['items'] for o in it.get('outlets', [])})} portais distintos na edição")
