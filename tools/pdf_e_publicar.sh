#!/usr/bin/env bash
# Depois de mexer na pauta: gera o PDF das pautas recentes, grava no repositório e publica o site.
set -uo pipefail
cd "$(dirname "$0")/.."
git config --local --unset-all http.https://github.com/.extraheader || true
[ -n "${GHT:-}" ] && git remote set-url origin "https://x-access-token:${GHT}@github.com/${GITHUB_REPOSITORY}.git"
git config user.name "github-actions[bot]"; git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git fetch -q origin main && git reset -q --hard origin/main
if tools/pdf.sh; then
  mkdir -p /tmp/pdf && cp programa/*.pdf /tmp/pdf/ 2>/dev/null || true
  for i in 1 2 3 4; do
    git fetch -q origin main && git reset -q --hard origin/main
    cp /tmp/pdf/*.pdf programa/ 2>/dev/null || true
    git add programa/*.pdf 2>/dev/null || true
    git diff --cached --quiet && break
    git commit -qm "PDF da pauta do programa" && git push -q origin HEAD:main && break
    sleep $((i*4))
  done
else echo "::warning::Não consegui gerar o PDF"; fi
tools/publicar.sh
