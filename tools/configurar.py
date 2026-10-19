"""Gera as configurações a partir de cliente.json:
- noticias/config.json (portais nacionais + os da região do cliente, blocos, critério "peso para o veículo")
- programa/config.json (parâmetros da pauta do programa)
- site/cliente.json (o que as páginas mostram: nome, programa, cor)
- horários das rotinas em .github/workflows (noticias.yml e programa.yml)
Uso: python3 tools/configurar.py"""
import json, os, re
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
C = json.load(open("cliente.json", encoding="utf-8"))
P, R = C["programa"], C["regiao"]

# ---------- notícias ----------
n = json.load(open("tools/noticias-base.json", encoding="utf-8"))
n["_doc"] = f"Parâmetros da aba Notícias de {C['cliente']}. Gerado por tools/configurar.py a partir de cliente.json; ajustes finos podem ser feitos aqui."
nomes = {o["name"] for o in n["outlets"]}
n["outlets"] = [o for o in n["outlets"] if o["name"] not in {p["name"] for p in R["portais"]}] + R["portais"]
for s in n["segments"]:
    if s["key"] == "rio":
        s["key"], s["label"] = "regiao", R.get("rotulo_bloco") or R["nome"]
        s["note"] = f"{R['nome']}: governo do estado, Assembleia, prefeitura da capital, câmara municipal, segurança, transporte, economia e interior da região de cobertura do veículo"
    if s["key"] == "educacao":
        s["note"] = "Educação básica, técnica e superior: MEC, Enem, Fies, Prouni, universidades e institutos federais, redes estaduais e municipais da região, professores, greves, avaliações (Saeb, Ideb, Pisa)"
    if s["key"] == "esportes":
        s["note"] = "Futebol (com destaque para os clubes da região), Seleção, outros esportes e a política do esporte"
    if s["key"] == "ciencia":
        s["note"] = "Ciência, pesquisa, inovação, startups, inteligência artificial, big techs e regulação digital, saúde e medicina, espaço"
for cr in n["criteria"]:
    if cr["key"] == "peso_voce":
        cr["label"] = f"Peso para {C['veiculo']}"
        cr["how"] = f"Aderência à linha editorial de {C['veiculo']} e aos temas prioritários ({', '.join(C['temas_prioritarios'])}): forte = 10; média = 6; fraca = 3."
n["editions"] = [e.replace("h", ":00") for e in C["noticias"]["edicoes"]]
os.makedirs("noticias", exist_ok=True)
json.dump(n, open("noticias/config.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- programa ----------
os.makedirs("programa", exist_ok=True)
pc = {"_doc": f"Parâmetros da pauta do programa {P['nome']}. Gerado por tools/configurar.py a partir de cliente.json.",
      "programa": P["nome"], "veiculo": C["veiculo"], "apresentadores": P["apresentadores"], "horario": P["horario"],
      "itens": P["itens"], "linhas_resumo": P["linhas_resumo"], "metafora_percentual": P["metafora_percentual"],
      "perguntas_por_item": P["perguntas_por_item"], "fontes_por_item": "2 a 4", "linha_editorial": C["linha_editorial"],
      "fontes_preferidas": C["fontes_da_linha"], "blocos": [R["nome"] if b == "Região" else b for b in P["blocos"]], "virada_hora": P["virada_hora"]}
json.dump(pc, open("programa/config.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for f, k in (("noticias/index.json", "editions"), ("programa/index.json", "days")):
    if not os.path.exists(f): json.dump({k: []}, open(f, "w"))

# ---------- o que as páginas mostram ----------
os.makedirs("site", exist_ok=True)
json.dump({"produto": C["produto"], "cliente": C["cliente"], "veiculo": C["veiculo"], "programa": P["nome"],
           "apresentadores": P["apresentadores"], "horario": P["horario"], "dias": P["dias"], "gera_pauta_as": P["gera_pauta_as"], "virada_hora": P["virada_hora"],
           "edicoes": C["noticias"]["edicoes"], "cor": C["marca"]["cor"], "logo": C["marca"].get("logo")},
          open("site/cliente.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- horários das rotinas (cron em UTC; Brasília = UTC-3) ----------
h, m = map(int, P["gera_pauta_as"].split(":")); hu = (h + 3) % 24
dias = ",".join(str(d) for d in P["dias"])  # 0 = domingo, igual ao cron
def troca(arq, novo):
    p = f".github/workflows/{arq}"
    if not os.path.exists(p): return
    s = open(p, encoding="utf-8").read()
    s2 = re.sub(r'- cron: "[^"]*"(\s*#[^\n]*)?', f'- cron: "{novo}"', s, count=1)
    open(p, "w", encoding="utf-8").write(s2)
troca("programa.yml", f"{m} {hu} * * {dias}")
troca("noticias.yml", C["noticias"]["cron_utc"])
print(f"ok: {C['cliente']} · {len(n['outlets'])} portais · pauta {P['nome']} às {P['gera_pauta_as']} (dias {dias}) · notícias {C['noticias']['edicoes']}")
