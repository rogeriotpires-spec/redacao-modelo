"""Regra das notícias: uma notícia só pode se repetir nas edições do MESMO dia.
Notícia que já saiu em edição de dia anterior (últimos 4 dias) só fica se tiver "desdobramento" (fato novo).
Uso: python3 tools/noticias_repeticao.py noticias/AAAA-MM-DD-HHh.json [--aplicar]
Sem --aplicar só lista (sai com 1 se houver repetida); com --aplicar remove as repetidas, refaz o "top" e corrige x_trends."""
import json, os, re, sys, unicodedata, glob
from datetime import date, timedelta
STOP = set("""para pela pelo pelos pelas como mais menos sobre entre desde quando onde quem qual quais porque
este esta isto esse essa isso aquele aquela seus suas dele dela deles delas nosso nossa voce voces eles elas
ainda depois antes agora hoje ontem amanha semana dias anos sendo sera foram fosse tinha teve tem vai vao
pode podem deve devem fazer feito disse diz dizer contra todo toda todos todas cada outro outra outros outras muito muita
entao assim tambem apenas mesmo mesma nunca sempre nada tudo algo alguem governo brasil""".split())
def norm(t):
    t = "".join(c for c in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(c) != "Mn")
    return {w for w in re.findall(r"[a-z0-9][a-z0-9.,]*[a-z0-9]|[a-z0-9]", t) if (len(w) >= 4 or w.isdigit()) and w not in STOP}
def sim(a, b): return len(a & b) / min(len(a), len(b)) if a and b else 0
path = sys.argv[1]; aplicar = "--aplicar" in sys.argv
ed = os.path.basename(path)[:-5]; dia = date.fromisoformat(ed[:10])
d = json.load(open(path, encoding="utf-8"))
ant = []
for k in range(1, 5):
    for f in sorted(glob.glob(f"noticias/{(dia - timedelta(days=k)).isoformat()}-*.json")):
        for it in json.load(open(f, encoding="utf-8")).get("items", []):
            ant.append((os.path.basename(f)[:-5], it.get("id"), norm(it.get("title")), norm((it.get("title") or "") + " " + (it.get("summary") or "")[:300]), it.get("title")))
rep = []
for it in d.get("items", []):
    if it.get("desdobramento") or it.get("fato_diferente"): continue
    t, s = norm(it.get("title")), norm((it.get("title") or "") + " " + (it.get("summary") or "")[:300])
    hit = next((a for a in ant if a[1] == it.get("id") or sim(t, a[2]) >= .5 or sim(s, a[3]) >= .5), None)
    if hit: rep.append((it, hit))
for it, h in rep: print(f'REPETIDA de outro dia: "{it.get("title")}" já saiu em {h[0]} ("{h[4]}")')
if not rep: print("sem repetição de dias anteriores")
if aplicar and rep:
    fora = {it["id"] for it, _ in rep}
    d["items"] = [i for i in d["items"] if i["id"] not in fora]
    n = len(d.get("top") or [])
    top = [i for i in (d.get("top") or []) if i not in fora]
    for i in sorted(d["items"], key=lambda x: -(x.get("score") or 0)):
        if len(top) >= n: break
        if i["id"] not in top: top.append(i["id"])
    d["top"] = top
    for x in d.get("x_trends") or []:
        if x.get("item_id") in fora: x["item_id"] = None
    d.setdefault("removidas_repetidas", []).extend(it.get("title") for it, _ in rep)
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"removidas {len(rep)}; restam {len(d['items'])} notícias")
sys.exit(1 if rep and not aplicar else 0)
