#!/usr/bin/env python3
"""Validate the fixed report and exercise rejection of corrupted snapshots."""

import copy
import datetime as dt
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

START, END = "2026-08-08", "2026-10-06"
DATES = {(dt.date.fromisoformat(START) + dt.timedelta(days=i)).isoformat() for i in range(60)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def numeric(value):
    return value is None or (type(value) in (int, float) and math.isfinite(value) and value >= 0)


def fields(row, keys):
    require(all(key in row and numeric(row[key]) for key in keys), "Campos numéricos ausentes/inválidos")


def equal_total(rows, key, expected):
    if rows and expected is not None and all(row[key] is not None for row in rows):
        tolerance = 0.02 if key == "spend" else 0.001
        require(abs(sum(row[key] for row in rows) - expected) <= tolerance, f"Total inconsistente: {key}")


def check(report):
    raw = json.dumps(report, ensure_ascii=False, allow_nan=False)
    require(not re.search(r"EAA[A-Za-z0-9]{30,}|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.|access_token\s*[=:]|Bearer\s+[A-Za-z0-9]|sb_secret_", raw, re.I), "Possível segredo no snapshot")
    meta, ads, ig = (report[k] for k in ("meta", "ads", "instagram"))
    require((meta["start"], meta["end"], meta["days"]) == (START, END, 60), "Período incorreto")
    require(meta["timezone"] == "America/Sao_Paulo", "Fuso incorreto")
    require(meta["status"] in ("partial", "complete"), "Status incorreto")
    require(bool(meta["title"]) and bool(meta["profile"]) and bool(meta["sources"]), "Metadados incompletos")
    require(dt.datetime.fromisoformat(meta["extractedAt"]).tzinfo is not None, "Extração sem fuso")
    for series, keys in [(ads, ["spend", "impressions", "clicks"]), (ig, ["followers", "reach", "profileViews", "interactions"])]:
        dates = [row["date"] for row in series["daily"]]
        require(len(dates) == len(set(dates)), "Datas duplicadas")
        require(set(dates) <= DATES and dates == sorted(dates), "Datas fora do período/desordenadas")
        no_delivery = series.get("noDeliveryDates", [])
        require(len(no_delivery) == len(set(no_delivery)) and set(no_delivery) <= DATES, "Datas sem entrega inválidas")
        require(not set(no_delivery) & set(dates), "Data simultaneamente com/sem entrega")
        require(series["missingDates"] == sorted(DATES - set(dates) - set(no_delivery)), "Lacunas inconsistentes")
        require(series["coverageDays"] == len(dates) + len(no_delivery), "Cobertura inconsistente")
        require(isinstance(series["source"], str) and bool(series["source"]), "Fonte ausente")
        for row in series["daily"]:
            fields(row, keys)
    if ads["missingDates"] or ig["missingDates"]:
        require(meta["status"] == "partial", "Cobertura parcial rotulada completa")
    fields(ads["totals"], ["spend", "impressions", "reach", "clicks", "linkClicks", "engagements", "videoViews"])
    fields(ig["totals"], ["profileViews", "interactions"])
    for key in ["spend", "impressions", "clicks"]:
        equal_total(ads["daily"], key, ads["totals"][key])
    ids = [r["id"] for r in ads["campaigns"]]
    require(len(ids) == len(set(ids)), "Campanhas duplicadas")
    for row in ads["campaigns"]:
        fields(row, ["spend", "impressions", "reach", "clicks", "linkClicks", "results"])
        require(isinstance(row["name"], str) and "objective" in row and "resultType" in row, "Campanha incompleta")
    for key in ["spend", "impressions", "clicks", "linkClicks"]:
        equal_total(ads["campaigns"], key, ads["totals"][key])
    for row in ads["highlights"]:
        fields(row, ["spend", "impressions", "reach", "engagements"])
        require(isinstance(row["name"], str) and "link" in row, "Destaque incompleto")
        require(isinstance(row["id"], str) and isinstance(row["campaignName"], str), "Identidade do anúncio ausente")
        if row["link"] is not None:
            url = urlsplit(row["link"])
            require(url.scheme == "https" and url.hostname is not None and not url.username and not url.password and not url.query, "Link inseguro")
    for key in ["profileViews", "interactions"]:
        equal_total(ig["daily"], key, ig["totals"][key])
        if any(row[key] is None for row in ig["daily"]):
            require(ig["totals"][key] is None, "Total IG esconde métrica indisponível")
    require(ig["baseline"]["date"] == "2026-08-07" and ig["end"]["date"] == END, "Base/fim incorretos")
    for row in [ig["baseline"], *ig["daily"], ig["end"]]:
        fields(row, ["followers"])
        require(row["followers"] is None or row["followers"] > 0, "Zero suspeito em seguidores")
        require(dt.datetime.fromisoformat(row["capturedAt"]).tzinfo is not None, "Coleta sem fuso")
    if ig["daily"] and ig["daily"][-1]["date"] == END:
        require(ig["end"]["followers"] == ig["daily"][-1]["followers"], "Seguidores finais inconsistentes")
    followers = [row["followers"] for row in [ig["baseline"], *ig["daily"]] if row["followers"] is not None]
    require(all(b >= a * 0.8 for a, b in zip(followers, followers[1:])), "Queda de seguidores >20%: requer investigação")


def self_check(report):
    mutations = [lambda r: r["meta"].update(start="2026-08-09"),
                 lambda r: r["ads"]["totals"].update(spend=-1),
                 lambda r: r["meta"].update(title="EAA" + "x" * 40),
                 lambda r: r["instagram"]["baseline"].update(followers=0),
                 lambda r: r["ads"].update(coverageDays=r["ads"]["coverageDays"] + 1)]
    if report["ads"]["daily"]:
        mutations.append(lambda r: r["ads"]["daily"].append(r["ads"]["daily"][0]))
    if report["ads"]["campaigns"]:
        mutations.append(lambda r: r["ads"]["campaigns"].append(r["ads"]["campaigns"][0]))
    if report["ads"]["totals"]["spend"] is not None and any(
            rows and all(row["spend"] is not None for row in rows)
            for rows in [report["ads"]["daily"], report["ads"]["campaigns"]]):
        mutations.append(lambda r: r["ads"]["totals"].update(spend=r["ads"]["totals"]["spend"] + 100))
    for mutate in mutations:
        corrupted = copy.deepcopy(report)
        mutate(corrupted)
        try:
            check(corrupted)
        except ValueError:
            continue
        raise ValueError("Self-check não rejeitou snapshot corrompido")
    return len(mutations)


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "data/relatorio-campanha.json"
    document = json.loads(path.read_text())
    check(document)
    cases = self_check(document)
    print(f"OK: contrato, cobertura, reconciliação, snapshots, segredos e {cases} casos de corrupção.")
