#!/usr/bin/env python3
"""Read-only campaign export. Supabase input is an MCP SQL export, never a key.

Usage: python3 scripts/extract_campaign_report.py --supabase-export /tmp/export.json
Input: {"instagram": [rows from pampolha_ig_daily_metrics], "ads": [rows]}.
Include 2026-08-07 IG baseline and 2026-08-08..2026-10-06 for both series.
Use only project hojcntkggnwrvbvmcwxe; select metrics plus created_at/updated_at.
"""

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

START, END = "2026-08-08", "2026-10-06"
ACCOUNT, IG = "act_716311018073722", "17841401257663487"
BASE = "https://graph.facebook.com/v24.0"
DATES = [(dt.date.fromisoformat(START) + dt.timedelta(days=i)).isoformat() for i in range(60)]
ROOT = Path(__file__).resolve().parents[1]


def token_from(path):
    token = os.environ.get("META_ACCESS_TOKEN")
    if not token:
        for line in path.read_text().splitlines():
            if line.startswith("META_ACCESS_TOKEN="):
                token = line.split("=", 1)[1].strip().strip("\"'")
    if not token:
        raise RuntimeError("META_ACCESS_TOKEN ausente no ambiente/arquivo autorizado")
    return token


def request(path, params, token):
    # Never follow returned URLs: pagination uses cursors on this fixed host only.
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body = json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            body = json.load(exc)
        except (ValueError, OSError):
            raise RuntimeError(f"Meta HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("Meta indisponível: erro de conexão ou timeout") from None
    if "error" in body:
        error = body["error"]
        # Provider messages can echo input; codes suffice and contain no credentials.
        raise RuntimeError(f"Meta erro {error.get('code')} / {error.get('error_subcode')}")
    return body


def pages(path, params, token):
    rows, seen = [], set()
    params = dict(params)
    while True:
        body = request(path, params, token)
        if not isinstance(body.get("data"), list):
            raise ValueError("Meta retornou uma lista inválida")
        rows.extend(body["data"])
        paging = body.get("paging", {})
        if not paging.get("next"):
            return rows
        cursor = paging.get("cursors", {}).get("after")
        if not cursor or cursor in seen:
            raise ValueError("Paginação Meta incompleta ou repetida")
        seen.add(cursor)
        params["after"] = cursor


def number(row, key):
    value = row.get(key)
    return float(value) if value is not None else None


def action(row, name):
    return next((number(a, "value") for a in row.get("actions", []) if a.get("action_type") == name), None)


def total(rows, key):
    values = [r.get(key) for r in rows]
    return round(sum(values), 2) if values and all(v is not None for v in values) else None


def missing(rows):
    return sorted(set(DATES) - {r["date"] for r in rows})


def collect_ads(token, account_id=ACCOUNT, start=START, end=END):
    days = (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days + 1
    if days <= 0:
        raise ValueError("Período Meta inválido")
    dates = {(dt.date.fromisoformat(start) + dt.timedelta(days=i)).isoformat() for i in range(days)}
    account = request(account_id, {"fields": "id,currency,timezone_name"}, token)
    if account.get("id") != account_id or account.get("currency") != "BRL" or account.get("timezone_name") != "America/Sao_Paulo":
        raise ValueError("Conta, moeda ou fuso Meta diverge do contrato")
    common = {"time_range": json.dumps({"since": start, "until": end}), "limit": 100}
    fields = "spend,impressions,reach,clicks,inline_link_clicks,actions,video_play_actions"
    account_rows = pages(f"{account_id}/insights", dict(common, level="account", fields=fields), token)
    if len(account_rows) != 1:
        raise ValueError("Total Meta ausente ou duplicado")
    r = account_rows[0]
    ads = {"source": "Meta Marketing API v24.0 — conta completa, sem filtro por nome",
           "totals": {k: number(r, key) for k, key in [("spend", "spend"), ("impressions", "impressions"),
           ("reach", "reach"), ("clicks", "clicks"), ("linkClicks", "inline_link_clicks")]},
           "daily": [], "campaigns": [], "highlights": [], "notes": []}
    video = r.get("video_play_actions", [])
    ads["totals"].update(engagements=action(r, "post_engagement"),
                         videoViews=sum(float(v["value"]) for v in video) if video else None)
    daily = pages(f"{account_id}/insights", dict(common, level="account", fields="spend,impressions,clicks", time_increment=1), token)
    ads["daily"] = [{"date": r["date_start"], **{k: number(r, k) for k in ["spend", "impressions", "clicks"]}} for r in daily]
    absent = sorted(dates - {row["date"] for row in ads["daily"]})
    if absent:
        confirmation = pages(f"{account_id}/insights", dict(common, level="account", fields="spend,impressions,clicks",
                             time_range=json.dumps({"since": absent[0], "until": absent[-1]}), time_increment=1), token)
        if any(row["date_start"] in absent for row in confirmation):
            raise ValueError("Consulta de confirmação diverge da série diária")
    ads.update(coverageDays=days, missingDates=[], noDeliveryDates=absent)
    campaigns = pages(f"{account_id}/insights", dict(common, level="campaign", fields=fields + ",campaign_id,campaign_name,objective"), token)
    ads["campaigns"] = [{"id": r["campaign_id"], "name": r["campaign_name"], "objective": r.get("objective"),
                         **{k: number(r, k) for k in ["spend", "impressions", "reach", "clicks"]},
                         "linkClicks": number(r, "inline_link_clicks"), "results": None, "resultType": None} for r in campaigns]
    ads["campaigns"].sort(key=lambda r: r["spend"] or 0, reverse=True)
    try:
        ad_rows = pages(f"{account_id}/insights", dict(common, level="ad", fields=fields + ",ad_id,ad_name,campaign_name"), token)
        ads["highlights"] = [{"id": r["ad_id"], "name": r["ad_name"], "campaignName": r["campaign_name"],
                              **{k: number(r, k) for k in ["impressions", "reach", "spend"]},
                              "engagements": action(r, "post_engagement"), "link": None}
                             for r in sorted(ad_rows, key=lambda r: float(r.get("impressions", 0)), reverse=True)[:5]]
    except (RuntimeError, ValueError) as exc:
        ads["notes"].append(f"Detalhamento de anúncios indisponível: {exc}.")
    ads["notes"] += ["Campanhas com entrega reportada no intervalo, incluindo campanhas hoje pausadas/arquivadas; nenhuma filtragem por nome.",
                     "Alcance do período consultado no nível da conta: não é a soma do alcance diário ou das campanhas.",
                     "Destaques: cinco anúncios com mais impressões no intervalo; links públicos não coletados.",
                     "Resultados/conversões por objetivo não consolidados; engagements representa post_engagement e videoViews representa reproduções de vídeo.",
                     "Dias sem linha foram consultados novamente com sucesso: sem entrega reportada, distintos de falhas de coleta. A série preserva apenas observações retornadas; não preenche zeros."]
    if ads["daily"]:
        ads["notes"].append(f"Consulta dos {days} dias retornou {len(daily)} linhas diárias, de {daily[0]['date_start']} a {daily[-1]['date_start']}; a soma de investimento, impressões e cliques concilia com o total da conta no período.")
    if ads["totals"]["linkClicks"] is not None and ads["totals"]["clicks"] is not None and ads["totals"]["linkClicks"] > ads["totals"]["clicks"]:
        ads["notes"].append("A API reporta mais inline_link_clicks que clicks no mesmo período. Valores preservados sem ajuste; CPC e CTR usam clicks. Não tratar as duas contagens como um funil reconciliado.")
    return ads


def historical_ads(rows, reason):
    rows = [r for r in rows if START <= r["date"] <= END]
    if any(r["account_id"] != ACCOUNT for r in rows):
        raise ValueError("Conta Ads inesperada no export")
    daily = [{"date": r["date"], "spend": number(r, "total_spend"), "impressions": number(r, "total_impressions"),
              "clicks": number(r, "total_clicks")} for r in rows if r.get("total_impressions", 0) > 0]
    return {"source": "Supabase pampolha_ads_daily_metrics — somente DISTRIBUI, cobertura parcial",
            "coverageDays": len(daily), "missingDates": missing(daily), "daily": daily,
            "totals": {**{k: total(daily, k) for k in ["spend", "impressions", "clicks"]},
                       "reach": None, "linkClicks": None, "engagements": None, "videoViews": None},
            "campaigns": [], "highlights": [], "notes": [f"Meta indisponível: {reason}.",
            "Coletor histórico filtra DISTRIBUI; estes números não representam todas as campanhas.",
            "Zeros do coletor sem comprovação de entrega foram excluídos; alcance deduplicado indisponível."]}


def instagram(rows):
    if any(r["account_id"] != IG for r in rows):
        raise ValueError("Conta Instagram inesperada no export")
    rows = sorted(rows, key=lambda r: r["date"])
    if len({r["date"] for r in rows}) != len(rows):
        raise ValueError("Datas Instagram duplicadas no export")
    def endpoint(row):
        return {"date": row["date"], "followers": row["followers_count"] or None,
                "capturedAt": row["updated_at"]}
    baseline = next((r for r in rows if r["date"] == "2026-08-07"), None)
    end = next((r for r in rows if r["date"] == END), None)
    if baseline is None or end is None:
        raise ValueError("Snapshot base/final do Instagram ausente")
    daily = [{"date": r["date"], "followers": r["followers_count"] or None,
              "reach": r["reach"] or None, "profileViews": r["profile_views"] or None,
              "interactions": r["total_interactions"] or None, "capturedAt": r["updated_at"]}
             for r in rows if START <= r["date"] <= END]
    return {"source": "Supabase pampolha_ig_daily_metrics · coletor pampolha-snapshot v3",
            "coverageDays": len(daily), "missingDates": missing(daily), "baseline": endpoint(baseline),
            "end": endpoint(end), "daily": daily, "totals": {k: total(daily, k) for k in ["profileViews", "interactions"]},
            "notes": ["Seguidores são snapshots atuais na coleta, não fechamento do dia nominal. Base nominal 07/08 coletada em 08/08 às 03h; final nominal 06/10 coletado em 07/10 às 03h (Brasília). capturedAt registra o horário de persistência, próximo da coleta.",
                      "Variação líquida entre esses snapshots; não mede seguidores atribuídos aos anúncios.",
                      "Insights diários do Instagram consultados pelo coletor em janela UTC (00:00–23:59:59), diferente do dia de mídia em America/Sao_Paulo.",
                      "Totais de visitas e interações somam somente os dias presentes; lacunas não são zeros.",
                      "Coletor legado converte falhas/ausências em zero. Zeros sem comprovação ficam null neste relatório.",
                      f"Qualidade dos snapshots: {sum(r['followers_count'] == 0 for r in rows)} zeros de seguidores; {sum(b['followers_count'] < a['followers_count'] for a, b in zip(rows, rows[1:]))} quedas entre coletas consecutivas."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--supabase-export", type=Path, required=True)
    parser.add_argument("--token-file", type=Path, default=Path.home() / ".claude/credenciais/ads.env")
    parser.add_argument("--output", type=Path, default=ROOT / "data/relatorio-campanha.json")
    args = parser.parse_args()
    source = json.loads(args.supabase_export.read_text())
    try:
        ads = collect_ads(token_from(args.token_file))
    except (OSError, RuntimeError) as exc:
        # OSError includes missing credential file; do not print its contents.
        ads = historical_ads(source["ads"], type(exc).__name__ if isinstance(exc, OSError) else str(exc))
    ig = instagram(source["instagram"])
    historical = [r for r in source["ads"] if r["account_id"] == ACCOUNT and START <= r["date"] <= END]
    if ads["source"].startswith("Meta"):
        spend = round(sum(float(r["total_spend"]) for r in historical), 2)
        impressions = sum(r["total_impressions"] for r in historical)
        ads["notes"].append(f"Conferência com histórico Supabase ({len(historical)} dias, filtro DISTRIBUI): R${spend:.2f} e {impressions} impressões; API atual: R${ads['totals']['spend']:.2f} e {ads['totals']['impressions']:g} impressões. Diferenças de R${ads['totals']['spend'] - spend:.2f} e {ads['totals']['impressions'] - impressions:g} impressões; fontes coletadas em momentos distintos e histórico filtrado. O relatório usa a API atual.")
    report = {"meta": {"title": "Felipe Pampolha · Relatório de campanha", "start": START, "end": END,
              "days": 60, "extractedAt": dt.datetime.now(dt.timezone.utc).isoformat(), "timezone": "America/Sao_Paulo",
              "profile": "@felipepampolha.rio", "sources": [ads["source"], ig["source"]],
              "status": "partial" if ads["missingDates"] or ig["missingDates"] or not ads["campaigns"] else "complete",
              "notes": ["Moeda: BRL. Extração fixa de 60 dias; valores podem ser revisados posteriormente pela plataforma.",
                        "Instagram com lacunas em 10/09 e 13/09; crescimento líquido usa os snapshots base/final disponíveis."]},
              "ads": ads, "instagram": ig}
    from check_campaign_report import check
    check(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(args.output)
    print(json.dumps({"output": str(args.output), "status": report["meta"]["status"], "adsDays": ads["coverageDays"],
                      "campaigns": len(ads["campaigns"]), "instagramDays": ig["coverageDays"]}))


if __name__ == "__main__":
    main()
