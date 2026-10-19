"""Fila entre workflows que mexem no mesmo arquivo.
Espera terminarem as execuções dos workflows indicados que foram criadas ANTES desta
(ordem de chegada: quem pediu primeiro roda primeiro; não há espera mútua).
Uso: python3 tools/esperar.py programa.yml programa-avulso.yml pauta-excluir.yml
Precisa de GH_TOKEN, GITHUB_REPOSITORY e GITHUB_RUN_ID (o Actions já fornece os dois últimos)."""
import json, os, sys, time, urllib.request

REPO, RUN, TOKEN = os.environ["GITHUB_REPOSITORY"], int(os.environ["GITHUB_RUN_ID"]), os.environ.get("GH_TOKEN", "")
LIMITE = int(os.environ.get("ESPERA_MAX_MIN", "40")) * 60


def api(path):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}{path}", headers={
        "Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "painel-fila"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


eu = api(f"/actions/runs/{RUN}")
chave = (eu["created_at"], RUN)
inicio = time.time()
avisado = False
while True:
    antes = []
    for wf in sys.argv[1:]:
        for st in ("in_progress", "queued", "waiting", "pending", "requested"):
            try:
                runs = api(f"/actions/workflows/{wf}/runs?status={st}&per_page=30").get("workflow_runs", [])
            except Exception as e:
                print(f"aviso: não consegui consultar {wf}: {e}")
                runs = []
            antes += [f'{r["name"]} (#{r["run_number"]})' for r in runs if r["id"] != RUN and (r["created_at"], r["id"]) < chave]
    antes = sorted(set(antes))
    if not antes:
        print("fila livre" + (f" depois de {int(time.time() - inicio)}s" if avisado else ""))
        break
    if not avisado:
        print("::notice::Aguardando terminar antes de começar: " + ", ".join(antes))
        avisado = True
    if time.time() - inicio > LIMITE:
        print(f"::warning::Esperei {LIMITE // 60} minutos e sigo assim mesmo. Ainda rodando: " + ", ".join(antes))
        break
    time.sleep(20)
