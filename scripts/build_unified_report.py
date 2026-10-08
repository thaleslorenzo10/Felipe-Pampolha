#!/usr/bin/env python3
"""Combine the verified snapshots; no API calls and no invented unique reach."""

import copy
import datetime as dt
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from check_account_reports import ACCOUNTS, BUSINESS, END, check_accounts
from check_campaign_report import START, check, require

DATA = Path(__file__).resolve().parents[1] / 'data'
ADDITIVE = ('spend', 'impressions', 'clicks', 'linkClicks', 'engagements', 'videoViews')
DAILY = ('spend', 'impressions', 'clicks')
FILES = ('relatorio-campanha.json', 'relatorio-conta-01.json', 'relatorio-conta-02.json')


def dates_between(start, end):
    first = dt.date.fromisoformat(start)
    return [(first + dt.timedelta(days=i)).isoformat()
            for i in range((dt.date.fromisoformat(end) - first).days + 1)]


def add(values):
    """Unavailable input is unavailable total; decimal arithmetic protects cents."""
    return None if any(value is None for value in values) else float(sum((Decimal(str(v)) for v in values), Decimal(0)))


def validate_sources(recent, histories):
    check(recent)
    check_accounts(histories)
    first, second = ACCOUNTS
    require(recent['meta']['profile'] == '@felipepampolha.rio', 'Perfil incorreto')
    require(recent['ads'].get('accountId', first) == first, 'Conta do recorte incorreta')
    require(recent['ads']['source'] == 'Meta Marketing API v24.0 — conta completa, sem filtro por nome', 'Fonte do recorte incorreta')
    history = histories[first]['ads']
    require(recent['ads']['daily'] == [r for r in history['daily'] if r['date'] >= START], 'Recorte não corresponde ao histórico da Conta 01')
    known = {r['id'] for r in history['campaigns']}
    require(all(r['id'] in known for r in recent['ads']['campaigns']), 'Campanha do recorte em outra conta')
    require(START <= histories[second]['meta']['start'] <= END, 'Conta 02 exige recorte adicional')


def combine(reports, identities, start, instagram, title):
    dates = dates_between(start, END)
    accounts, campaigns, highlights = [], [], []
    sources, notes = [], [
        'As duas contas estão reunidas; cada campanha e anúncio mantém sua conta de origem.',
        'Alcance único entre contas indisponível: públicos podem se sobrepor. O alcance é exibido separadamente por conta e não é somado.',
        'CPC, CPM e CTR são calculados pelos totais correspondentes, nunca pela média das taxas.',
        'Instagram corresponde somente a 08/08/2026–06/10/2026, com 58 de 60 dias disponíveis; não representa o histórico completo da mídia.',
    ]
    daily_maps = []
    for report, identity in zip(reports, identities):
        meta, ads = report['meta'], report['ads']
        source = f"{ads['source']} · {identity['label']} ({identity['id']})" if identity['id'] not in ads['source'] else ads['source']
        sources.append(source)
        accounts.append({**{key: identity[key] for key in ('id', 'name', 'label')},
                         **{key: meta[key] for key in ('start', 'end', 'days')},
                         **copy.deepcopy({key: ads[key] for key in ('totals', 'coverageDays', 'missingDates', 'noDeliveryDates')}),
                         'source': source})
        annotation = dict(accountId=identity['id'], accountName=identity['name'], accountLabel=identity['label'])
        campaigns.extend({**copy.deepcopy(row), **annotation} for row in ads['campaigns'])
        highlights.extend({**copy.deepcopy(row), **annotation} for row in ads['highlights'])
        notes.extend(f"{identity['label']}: {note}" for note in ads['notes'])
        notes.append(f"{identity['label']}: datas anteriores à criação em {identity['createdTime'][:10]} não têm atividade possível nesta conta.")
        daily_maps.append({row['date']: row for row in ads['daily']})
    daily, missing, no_delivery = [], [], []
    for date in dates:
        values, observed, unknown = [], False, False
        for report, identity, daily_map in zip(reports, identities, daily_maps):
            if date in daily_map:
                observed = True
                values.append(daily_map[date])
            elif date < identity['createdTime'][:10] or date in report['ads']['noDeliveryDates']:
                values.append(dict.fromkeys(DAILY, 0))
            else:
                unknown = True
                values.append(dict.fromkeys(DAILY, None))
        if unknown:
            missing.append(date)
        if observed:
            daily.append({'date': date, **{key: add([row[key] for row in values]) for key in DAILY}})
        elif not unknown:
            no_delivery.append(date)
    totals = {key: add([report['ads']['totals'][key] for report in reports]) for key in ADDITIVE}
    totals['reach'] = None
    sources.append(instagram['source'])
    extracted = max(report['meta']['extractedAt'] for report in reports)
    return {
        'meta': {'title': title, 'start': start, 'end': END, 'days': len(dates), 'timezone': 'America/Sao_Paulo',
                 'extractedAt': extracted, 'profile': '@felipepampolha.rio', 'sources': sources,
                 'status': 'partial' if missing or instagram['missingDates'] else 'complete', 'notes': notes[:4]},
        'ads': {'source': 'Meta Marketing API v24.0 · contas Felipe Pampolha 01 e 02', 'totals': totals,
                'daily': daily, 'campaigns': campaigns, 'highlights': highlights, 'notes': list(dict.fromkeys(notes)),
                'coverageDays': len(dates) - len(missing), 'missingDates': missing, 'noDeliveryDates': no_delivery},
        'accounts': accounts, 'instagram': copy.deepcopy(instagram),
    }


def build():
    raw = {name: (DATA / name).read_bytes() for name in FILES}
    original, first, second = [json.loads(raw[name]) for name in FILES]
    histories = {account: report for account, report in zip(ACCOUNTS, (first, second))}
    validate_sources(original, histories)
    identities = [first['meta']['account'], second['meta']['account']]
    instagram = {**copy.deepcopy(original['instagram']), 'period': {'start': START, 'end': END, 'days': 60},
                 'profile': original['meta']['profile']}
    recent = combine([original, second], identities, START, instagram, 'Felipe Pampolha · 60 dias e Instagram')
    history = combine([first, second], identities, first['meta']['start'], instagram, 'Felipe Pampolha · Histórico completo das contas 01 e 02')
    return {'meta': {'version': 1, 'businessId': BUSINESS, 'currency': 'BRL', 'timezone': 'America/Sao_Paulo',
                     'extractedAt': max(original['meta']['extractedAt'], first['meta']['extractedAt'], second['meta']['extractedAt']),
                     'provenance': {name: {'sha256': hashlib.sha256(value).hexdigest(),
                                           'extractedAt': json.loads(value)['meta']['extractedAt']} for name, value in raw.items()}},
            'views': {'recent': recent, 'history': history}}


if __name__ == '__main__':
    document = build()
    from check_unified_report import check_unified
    check_unified(document)
    destination = DATA / 'relatorio-unificado.json'
    destination.write_text(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(f'OK: {destination.name}, 31 campanhas nos 60 dias e 93 no histórico; alcance separado por conta.')
