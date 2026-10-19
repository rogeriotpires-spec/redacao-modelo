#!/usr/bin/env bash
# Gera o PDF das pautas do programa mais recentes (programa/AAAA-MM-DD.pdf). Uso: tools/pdf.sh [AAAA-MM-DD ...]
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf /tmp/pdfsite && mkdir -p /tmp/pdfsite/programa && cp -r site/. /tmp/pdfsite/ && cp programa/*.json /tmp/pdfsite/programa/ && { [ -d marca ] && cp -r marca /tmp/pdfsite/ || true; }
npm i --silent --no-save playwright@1.47.2 >/dev/null 2>&1
(cd /tmp/pdfsite && python3 -m http.server 8777 >/dev/null 2>&1 &) ; sleep 1
node tools/pdf-programa.js "$@"
