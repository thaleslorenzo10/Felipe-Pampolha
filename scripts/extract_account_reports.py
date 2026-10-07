#!/usr/bin/env python3
"""Export full ad account histories by GET, through the last complete day."""

import argparse
import datetime as dt
import json
from pathlib import Path

from extract_campaign_report import END, ROOT, collect_ads, request, token_from
from check_account_reports import ACCOUNTS, BUSINESS, check_accounts


def collect_report(token, account_id, expected):
    account = request(account_id, {"fields": "id,name,currency,timezone_name,created_time,business"}, token)
    if (account.get("id"), account.get("name"), account.get("currency"),
            account.get("timezone_name"), account.get("business", {}).get("id")) != (
            account_id, expected["name"], "BRL", "America/Sao_Paulo", BUSINESS):
        raise ValueError("Identidade da conta diverge do contrato")
    created = dt.datetime.fromisoformat(account["created_time"]).date().isoformat()
    ads = collect_ads(token, account_id, created, END)
    ads["accountId"] = account_id
    ads["source"] += f" · {expected['label']} ({account_id})"
    ads["notes"].append(f"Histórico consultado desde a criação da conta em {created}, até {END} (último dia completo do recorte).")
    if ads["daily"]:
        ads["notes"].append(f"Primeira/última linha diária reportada: {ads['daily'][0]['date']} / {ads['daily'][-1]['date']}.")
    meta = {"title": f"{expected['label']} · Relatório de campanhas", "start": created, "end": END,
            "days": (dt.date.fromisoformat(END) - dt.date.fromisoformat(created)).days + 1,
            "account": {"id": account_id, "name": account["name"], "label": expected["label"],
                        "businessId": BUSINESS, "currency": account["currency"], "createdTime": account["created_time"]},
            "timezone": account["timezone_name"], "extractedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "sources": [ads["source"]], "status": "partial" if ads["missingDates"] else "complete",
            "notes": ["Histórico de mídia por conta, sem filtro por nome/status de campanha. Moeda: BRL.",
                      "Valores podem ser revisados posteriormente pela plataforma; este é um snapshot fixo.",
                      "Instagram não incluído: o histórico orgânico disponível não cobre todo este período."]}
    return {"meta": meta, "ads": ads}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token-file", type=Path, default=Path.home() / ".claude/credenciais/ads.env")
    args = parser.parse_args()
    token = token_from(args.token_file)
    reports = {key: collect_report(token, key, expected) for key, expected in ACCOUNTS.items()}
    check_accounts(reports)
    for account_id, report in reports.items():
        output = ROOT / "data" / ACCOUNTS[account_id]["file"]
        temporary = output.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        temporary.replace(output)
        print(json.dumps({"output": str(output), "account": account_id, "status": report["meta"]["status"],
                          "campaigns": len(report["ads"]["campaigns"]), "totals": report["ads"]["totals"]}))


if __name__ == "__main__":
    main()
