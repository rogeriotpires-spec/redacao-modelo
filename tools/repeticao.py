"""Aponta pautas repetidas: compara cada opção (conteúdo) ou item (programa) com os 3 dias anteriores
e com os outros itens do mesmo dia. Uso:
  python3 tools/repeticao.py pautas/AAAA-MM-DD.json
  python3 tools/repeticao.py programa/AAAA-MM-DD.json
Sai com erro (1) se achar repetição sem o campo "desdobramento" preenchido."""
import json, os, re, sys, glob, unicodedata
from datetime import date, timedelta

STOP = set("""para pela pelo pelos pelas como mais menos sobre entre desde quando onde quem qual quais porque porquê
este esta isto esse essa isso aquele aquela seus suas dele dela deles delas nosso nossa voce você vocês eles elas
ainda depois antes agora hoje ontem amanha amanhã semana dias anos sendo será foram fosse tinha teve tem têm vai vão
pode podem deve devem fazer feito disse diz dizer contra todo toda todos todas cada outro outra outros outras muito muita
porque então assim também tambem apenas mesmo mesma nunca sempre nada tudo algo alguem alguém governo brasil
""".split())

def norm(t):
    t = unicodedata.normalize("NFD", (t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return {w for w in re.findall(r"[a-z0-9][a-z0-9.,]*[a-z0-9]|[a-z0-9]", t) if (len(w) >= 4 or w.isdigit()) and w not in STOP}

def sim(a, b):
    if not a or not b: return 0
    return len(a & b) / min(len(a), len(b))  # sobreposição relativa ao texto menor

def itens(path):
    d = json.load(open(path, encoding="utf-8")); out = []
    if "slots" in d:
        for s in d["slots"]:
            for i, o in enumerate(s.get("options", [])):
                out.append((f'{s.get("time","")} opção {"AB"[i] if i < 2 else i+1}', o.get("title", ""), (o.get("title", "") + " " + o.get("fact", "")), o.get("desdobramento")))
    elif "itens" in d:
        for k, x in enumerate(d["itens"]):
            txt = " ".join([x.get("titulo", ""), x.get("resumo", "")] + list(x.get("contexto") or []))
            out.append((f"item {k+1}", x.get("titulo", ""), txt, x.get("desdobramento") or x.get("avulsa")))
    return out

def main():
    path = sys.argv[1]; pasta = os.path.dirname(path); dia = os.path.basename(path)[:10]
    d0 = date.fromisoformat(dia); limiar = 0.42 if pasta.endswith("programa") else 0.38
    atuais = [(r, t, norm(txt), dd) for r, t, txt, dd in itens(path)]
    anteriores = []
    for k in range(1, 4):
        f = os.path.join(pasta, (d0 - timedelta(days=k)).isoformat() + ".json")
        if os.path.exists(f): anteriores += [(f"{os.path.basename(f)[:10]} {r}", t, norm(txt)) for r, t, txt, _ in itens(f)]
    excluidos = []
    # temas apagados com a lixeira não voltam: os "excluidos" do próprio dia e dos 3 anteriores contam como já usados
    for k in range(0, 4):
        f = os.path.join(pasta, (d0 - timedelta(days=k)).isoformat() + ".json")
        if os.path.exists(f):
            for x in json.load(open(f, encoding="utf-8")).get("excluidos", []):
                excluidos.append((f"excluído pelo usuário em {os.path.basename(f)[:10]}", x.get("titulo", ""), norm(x.get("titulo", ""))))
    if pasta.endswith("pautas"):
        for extra, chave, campo_t, campo_f in (("sob-demanda.json", "items", None, None), ("quentes.json", "alerts", "title", "fact")):
            f = os.path.join(pasta, extra)
            if not os.path.exists(f): continue
            for x in json.load(open(f, encoding="utf-8")).get(chave, []):
                quando = (x.get("done") or x.get("requested") or x.get("time") or "")[:10]
                if not quando or not (d0 - timedelta(days=3)).isoformat() <= quando < dia: continue
                if chave == "items":
                    for o in x.get("options", []): anteriores.append((f"sob demanda {quando}", o.get("title", ""), norm(o.get("title", "") + " " + o.get("fact", ""))))
                else: anteriores.append((f"pauta quente {quando}", x.get(campo_t, ""), norm(x.get(campo_t, "") + " " + x.get(campo_f, ""))))
    achados = []
    for i, (r, t, w, dd) in enumerate(atuais):
        for r2, t2, w2 in anteriores:
            s = sim(w, w2)
            if s >= limiar: achados.append((s, dd and not r2.startswith("excluído"), f'{r} "{t}" repete {r2} "{t2}" ({s:.0%})'))
        for r2, t2, w2 in excluidos:  # compara título com título (o excluído só tem título)
            wt = norm(t); s = sim(wt, w2)
            if s >= 0.5 and len(wt & w2) >= 3: achados.append((s, False, f'{r} "{t}" repete tema {r2} "{t2}" ({s:.0%})'))
        for r2, t2, w2, _ in atuais[i+1:]:
            if r.split(" ")[0] == r2.split(" ")[0] and pasta.endswith("pautas"): continue  # opções A e B do mesmo horário já são temas diferentes por regra
            s = sim(w, w2)
            if s >= (0.24 if pasta.endswith("programa") else limiar): achados.append((s, False, f'{r} "{t}" repete {r2} "{t2}" no mesmo dia ({s:.0%}): funda os dois num item só'))
    ruins = [a for a in achados if not a[1]]
    for s, dd, msg in sorted(achados, key=lambda a: a[0], reverse=True): print(("OK (desdobramento) " if dd else "REPETIDO: ") + msg)
    if not achados: print("sem repetição")
    sys.exit(1 if ruins else 0)

main()
