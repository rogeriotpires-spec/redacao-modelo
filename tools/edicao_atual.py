"""Diz qual edição de notícias está sendo gerada agora (horário de Brasília): a de horário mais próximo.
Uso: python3 tools/edicao_atual.py  ->  imprime, por exemplo, 12h"""
import json, os, datetime, zoneinfo
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
horas = sorted(int(e[:2]) for e in json.load(open("noticias/config.json", encoding="utf-8"))["editions"])
agora = datetime.datetime.now(zoneinfo.ZoneInfo("America/Sao_Paulo"))
m = agora.hour + agora.minute / 60
print(f"{min(horas, key=lambda h: (abs(h - m), -h)):02d}h")
