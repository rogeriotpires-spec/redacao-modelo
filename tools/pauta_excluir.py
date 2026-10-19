"""Exclui um item da pauta (botão de lixeira da página de pautas).
Uso: PAYLOAD='{"tipo":"programa|conteudo|sobdemanda|quente","data":"AAAA-MM-DD","titulo":"..."}' python3 tools/pauta_excluir.py"""
import json, os, re, sys
from datetime import datetime, timezone, timedelta
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
p = json.loads(os.environ["PAYLOAD"])
tipo, data, tit = p.get("tipo"), str(p.get("data", "")), str(p.get("titulo", "")).strip()
if not tit: sys.exit("título vazio")
agora = datetime.now(timezone(timedelta(hours=-3))).replace(microsecond=0).isoformat()
def carregar(f):
    if not os.path.exists(f): sys.exit(f"arquivo não existe: {f}")
    return json.load(open(f, encoding="utf-8"))
def gravar(f, d): json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n = 0
if tipo == "programa":
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data): sys.exit("data inválida")
    f = f"programa/{data}.json"; d = carregar(f); antes = len(d.get("itens", []))
    d["itens"] = [x for x in d.get("itens", []) if x.get("titulo", "").strip() != tit]; n = antes - len(d["itens"])
elif tipo == "conteudo":
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data): sys.exit("data inválida")
    f = f"pautas/{data}.json"; d = carregar(f)
    for s in d.get("slots", []):
        a = len(s.get("options", [])); s["options"] = [o for o in s.get("options", []) if o.get("title", "").strip() != tit]; n += a - len(s["options"])
    d["slots"] = [s for s in d.get("slots", []) if s.get("options")]
elif tipo == "sobdemanda":
    f = "pautas/sob-demanda.json"; d = carregar(f)
    for x in d.get("items", []):
        a = len(x.get("options", [])); x["options"] = [o for o in x.get("options", []) if o.get("title", "").strip() != tit]; n += a - len(x["options"])
    d["items"] = [x for x in d.get("items", []) if x.get("options")]
elif tipo == "quente":
    f = "pautas/quentes.json"; d = carregar(f); a = len(d.get("alerts", []))
    d["alerts"] = [x for x in d.get("alerts", []) if x.get("title", "").strip() != tit]; n = a - len(d["alerts"])
else: sys.exit("tipo inválido")
if not n: sys.exit("item não encontrado (talvez já excluído)")
d.setdefault("excluidos", []).append({"titulo": tit, "em": agora})
gravar(f, d); print(f"excluído de {f}: {tit}")
