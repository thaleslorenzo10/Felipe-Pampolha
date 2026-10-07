#!/usr/bin/env python3
"""Validate complete account histories, isolation, totals and corrupted snapshots."""

import copy
import datetime as dt
import json
from pathlib import Path
import re

from check_campaign_report import equal_total, fields, require

BUSINESS = "1270499364534184"
ACCOUNTS = {
    "act_716311018073722": {"name": "Felipe Mendes Pampolha", "label": "Felipe Pampolha 01", "file": "relatorio-conta-01.json", "start": "2025-08-19"},
    "act_2174013390129316": {"name": "Felipe Mendes 02", "label": "Felipe Pampolha 02", "file": "relatorio-conta-02.json", "start": "2026-08-17"},
}
END = "2026-10-06"


def check_accounts(reports):
    require(set(reports) == set(ACCOUNTS), "Conjunto de contas incorreto")
    campaigns, highlights = set(), set()
    for account_id, report in reports.items():
        raw = json.dumps(report, ensure_ascii=False, allow_nan=False)
        require(not re.search(r"EAA[A-Za-z0-9]{30,}|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.|access_token\s*[=:]|Bearer\s+[A-Za-z0-9]|sb_secret_", raw, re.I), "Possível segredo no snapshot")
        require(set(report) == {"meta", "ads"}, "Histórico por conta deve conter somente mídia")
        meta, ads = report["meta"], report["ads"]
        account, expected = meta["account"], ACCOUNTS[account_id]
        require(account["id"] == account_id and ads["accountId"] == account_id, "Conta trocada no snapshot")
        require(account["name"] == expected["name"] and account["label"] == expected["label"], "Nome/rótulo de conta incorreto")
        require(account["businessId"] == BUSINESS and account["currency"] == "BRL", "Negócio/moeda incorretos")
        created = dt.datetime.fromisoformat(account["createdTime"])
        require(created.tzinfo is not None and created.date().isoformat() == expected["start"], "Criação da conta incorreta")
        require(meta["start"] == expected["start"] and meta["end"] == END, "Período histórico incorreto")
        start = dt.date.fromisoformat(meta["start"])
        days = (dt.date.fromisoformat(meta["end"]) - start).days + 1
        dates = {(start + dt.timedelta(days=i)).isoformat() for i in range(days)}
        require(meta["days"] == days and meta["timezone"] == "America/Sao_Paulo", "Dias/fuso incorretos")
        require(dt.datetime.fromisoformat(meta["extractedAt"]).tzinfo is not None, "Extração sem fuso")
        require(meta["title"] == f"{expected['label']} · Relatório de campanhas", "Título incorreto")
        require(ads["source"].startswith("Meta Marketing API") and account_id in ads["source"], "Fonte Ads incorreta")
        require(meta["sources"] == [ads["source"]], "Fontes inconsistentes")
        require(meta["status"] in ("partial", "complete"), "Status incorreto")
        delivered = [row["date"] for row in ads["daily"]]
        absent, missing = ads["noDeliveryDates"], ads["missingDates"]
        for sequence in [delivered, absent, missing]:
            require(len(sequence) == len(set(sequence)) and sequence == sorted(sequence), "Datas duplicadas/desordenadas")
            require(set(sequence) <= dates, "Datas fora do período")
        require(not set(delivered) & set(absent), "Data com/sem entrega simultânea")
        require(set(missing) == dates - set(delivered) - set(absent), "Lacunas inconsistentes")
        require(ads["coverageDays"] == len(delivered) + len(absent), "Cobertura incorreta")
        require(not missing or meta["status"] == "partial", "Cobertura parcial rotulada completa")
        fields(ads["totals"], ["spend", "impressions", "reach", "clicks", "linkClicks", "engagements", "videoViews"])
        for row in ads["daily"]:
            fields(row, ["spend", "impressions", "clicks"])
        for key in ["spend", "impressions", "clicks"]:
            equal_total(ads["daily"], key, ads["totals"][key])
        ids = set()
        for row in ads["campaigns"]:
            fields(row, ["spend", "impressions", "reach", "clicks", "linkClicks", "results"])
            require(isinstance(row["id"], str) and bool(row["id"]) and row["id"] not in ids, "Campanha duplicada/inválida")
            require(isinstance(row["name"], str) and "objective" in row and "resultType" in row, "Campanha incompleta")
            ids.add(row["id"])
        require(not campaigns & ids, "Campanhas cruzadas entre contas")
        campaigns.update(ids)
        for key in ["spend", "impressions", "clicks", "linkClicks"]:
            equal_total(ads["campaigns"], key, ads["totals"][key])
        ids = set()
        for row in ads["highlights"]:
            fields(row, ["spend", "impressions", "reach", "engagements"])
            require(isinstance(row["id"], str) and row["id"] not in ids, "Anúncio duplicado/inválido")
            require(isinstance(row["name"], str) and isinstance(row["campaignName"], str) and row["link"] is None, "Destaque incompleto")
            ids.add(row["id"])
        require(not highlights & ids, "Anúncios cruzados entre contas")
        highlights.update(ids)


def self_check(reports):
    first, second = ACCOUNTS
    mutations = [lambda r: r[first]["meta"]["account"].update(id=second),
                 lambda r: r[first]["ads"].update(accountId=second),
                 lambda r: r[first]["meta"]["account"].update(label=ACCOUNTS[second]["label"]),
                 lambda r: r[first]["meta"]["account"].update(businessId="0"),
                 lambda r: r[first].update(ads=r[second]["ads"]),
                 lambda r: r[first]["meta"].update(start="2026-08-08"),
                 lambda r: r[first]["ads"]["totals"].update(spend=-1),
                 lambda r: r[first]["meta"].update(title="EAA" + "x" * 40),
                 lambda r: r[first]["ads"].update(coverageDays=0)]
    if reports[first]["ads"]["daily"]:
        mutations.append(lambda r: r[first]["ads"]["daily"].append(r[first]["ads"]["daily"][0]))
        mutations.append(lambda r: r[first]["ads"]["totals"].update(spend=r[first]["ads"]["totals"]["spend"] + 100))
    if reports[first]["ads"]["campaigns"]:
        mutations.append(lambda r: r[first]["ads"]["campaigns"].append(r[first]["ads"]["campaigns"][0]))
        if reports[second]["ads"]["campaigns"]:
            mutations.append(lambda r: r[second]["ads"]["campaigns"][0].update(id=r[first]["ads"]["campaigns"][0]["id"]))
    for mutate in mutations:
        corrupted = copy.deepcopy(reports)
        mutate(corrupted)
        try:
            check_accounts(corrupted)
        except ValueError:
            continue
        raise ValueError("Self-check aceitou snapshot corrompido")
    return len(mutations)


def check_collector():
    from unittest.mock import patch
    import extract_campaign_report as collector

    # A zero-spend impression is still delivery; omitted metrics remain null.
    for account_id, start, end, use_defaults in [
            (collector.ACCOUNT, collector.START, collector.END, True),
            ("act_2174013390129316", "2026-08-17", END, False)]:
        row = {"date_start": start, "spend": "0", "impressions": "1", "reach": "1", "clicks": "0",
               "campaign_id": "test-campaign", "campaign_name": "Test", "objective": "LINK_CLICKS"}

        def fake_request(path, params, token):
            require(path == account_id, "Coletor consultou outra conta")
            return {"id": account_id, "currency": "BRL", "timezone_name": "America/Sao_Paulo"}

        def fake_pages(path, params, token):
            require(path == f"{account_id}/insights" and "filtering" not in params, "Coleta filtrada/cruzada")
            interval = json.loads(params["time_range"])
            require(start <= interval["since"] <= interval["until"] <= end, "Consulta fora do intervalo")
            if params["level"] == "ad" or interval["since"] > start:
                return []
            return [row]

        with patch.object(collector, "request", fake_request), patch.object(collector, "pages", fake_pages):
            ads = collector.collect_ads("test") if use_defaults else collector.collect_ads("test", account_id, start, end)
        require(len(ads["campaigns"]) == 1 and ads["campaigns"][0]["spend"] == 0, "Entrega sem gasto excluída")
        require(ads["totals"]["linkClicks"] is None, "Métrica ausente convertida em zero")
        require(ads["coverageDays"] == (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days + 1,
                "Coletor não respeitou os dias do intervalo")


if __name__ == "__main__":
    data = Path(__file__).resolve().parents[1] / "data"
    documents = {key: json.loads((data / expected["file"]).read_text()) for key, expected in ACCOUNTS.items()}
    check_accounts(documents)
    check_collector()
    print(f"OK: duas contas isoladas, períodos completos, totais reconciliados e {self_check(documents)} casos negativos.")
