#!/usr/bin/env python3
"""Verify consolidation against immutable sources and exercise failure cases."""

import copy
import json

from build_unified_report import ADDITIVE, DAILY, DATA, add, build, combine, dates_between, validate_sources
from check_account_reports import ACCOUNTS, BUSINESS, END
from check_campaign_report import require


def check_unified(document):
    require(document['meta']['version'] == 1 and document['meta']['businessId'] == BUSINESS, 'Negócio/versão incorretos')
    require(document['meta']['currency'] == 'BRL' and document['meta']['timezone'] == 'America/Sao_Paulo', 'Moeda/fuso incorretos')
    require(set(document['views']) == {'recent', 'history'}, 'Recortes incorretos')
    for name, report in document['views'].items():
        ads, meta = report['ads'], report['meta']
        require({a['id'] for a in report['accounts']} == set(ACCOUNTS) and len(report['accounts']) == 2, 'Contas incorretas')
        require(ads['totals']['reach'] is None, 'Alcance entre contas não pode ser somado')
        for key in ADDITIVE:
            require(ads['totals'][key] == add([a['totals'][key] for a in report['accounts']]), f'Total não concilia: {key}')
        for rows in (ads['campaigns'], ads['highlights']):
            ids = [(row['accountId'], row['id']) for row in rows]
            require(len(ids) == len(set(ids)), 'Identidades duplicadas')
            for row in rows:
                require(row['accountId'] in ACCOUNTS, 'Campanha/anúncio de outra conta')
                require(row['accountName'] == ACCOUNTS[row['accountId']]['name'] and row['accountLabel'] == ACCOUNTS[row['accountId']]['label'], 'Rótulo de origem incorreto')
        dates = set(dates_between(meta['start'], END))
        require(meta['days'] == len(dates) and set(ads['missingDates']) <= dates, 'Período/cobertura inválidos')
        require(ads['coverageDays'] == len(dates) - len(ads['missingDates']), 'Cobertura incorreta')
        require(report['instagram']['period'] == {'start': '2026-08-08', 'end': END, 'days': 60}, 'Período Instagram alterado')
        for key in DAILY:
            require(add([r[key] for r in ads['daily']]) == ads['totals'][key], f'Série não concilia: {name}/{key}')
        for key in ('spend', 'impressions', 'clicks', 'linkClicks'):
            require(add([r[key] for r in ads['campaigns']]) == ads['totals'][key], f'Campanhas não conciliam: {name}/{key}')
    require(document == build(), 'Snapshot diverge das fontes verificadas/proveniência')


def negative_checks(document):
    mutations = [
        lambda r: r['meta'].update(businessId='0'),
        lambda r: r['meta'].update(currency='USD'),
        lambda r: r['meta']['provenance']['relatorio-campanha.json'].update(sha256='0' * 64),
        lambda r: r['views']['history']['ads']['totals'].update(reach=1526298),
        lambda r: r['views']['recent']['ads']['totals'].update(spend=10399.23),
        lambda r: r['views']['recent']['accounts'][0].update(id='act_other'),
        lambda r: r['views']['history']['ads']['campaigns'][0].update(accountId='act_other'),
        lambda r: r['views']['history']['ads']['campaigns'].append(r['views']['history']['ads']['campaigns'][0]),
        lambda r: r['views']['recent']['ads']['daily'][0].update(spend=0),
        lambda r: r['views']['history']['meta'].update(start='2025-01-01'),
        lambda r: r['views']['history']['instagram']['period'].update(start='2025-08-19'),
        lambda r: r['views']['history']['instagram']['baseline'].update(followers=1),
        lambda r: r['views']['recent']['ads'].update(coverageDays=59),
    ]
    for mutate in mutations:
        corrupted = copy.deepcopy(document)
        mutate(corrupted)
        try:
            check_unified(corrupted)
        except ValueError:
            continue
        raise ValueError('Snapshot corrompido foi aceito')
    return len(mutations)


def check_unknowns_and_sources():
    original = json.loads((DATA / 'relatorio-campanha.json').read_text())
    histories = {account: json.loads((DATA / config['file']).read_text()) for account, config in ACCOUNTS.items()}
    first, second = [histories[account] for account in ACCOUNTS]
    identities = [first['meta']['account'], second['meta']['account']]
    # One observed account plus one unavailable account must yield null, not a partial total.
    date = original['ads']['daily'][0]['date']
    fake_second = copy.deepcopy(second)
    fake_second['ads']['totals']['spend'] = None
    fake_identity = copy.deepcopy(identities)
    fake_identity[1]['createdTime'] = '2026-08-01T00:00:00-0300'
    combined = combine([original, fake_second], fake_identity, '2026-08-08', original['instagram'], 'check')
    require(combined['ads']['daily'][0]['spend'] is None and date in combined['ads']['missingDates'], 'Ausência convertida em zero')
    require(combined['ads']['totals']['spend'] is None, 'Total indisponível convertido em parcial')
    # The actual account did not exist yet: known structural absence retains the observed value.
    combined = combine([original, second], identities, '2026-08-08', original['instagram'], 'check')
    require(combined['ads']['daily'][0] == original['ads']['daily'][0], 'Pré-criação confundida com lacuna')
    mutations = [lambda r: r['meta'].update(profile='@other'),
                 lambda r: r['ads'].update(accountId=identities[1]['id']),
                 lambda r: r['ads'].update(source='other'),
                 lambda r: r['ads']['campaigns'][0].update(id='unknown-campaign')]
    for mutate in mutations:
        corrupted = copy.deepcopy(original)
        mutate(corrupted)
        try:
            validate_sources(corrupted, histories)
        except ValueError:
            continue
        raise ValueError('Fonte incorreta foi aceita')
    return len(mutations)


if __name__ == '__main__':
    snapshot = json.loads((DATA / 'relatorio-unificado.json').read_text())
    check_unified(snapshot)
    print(f'OK: proveniência, ambas as contas/períodos, reconciliação exata, Instagram limitado a 60 dias; '
          f'{negative_checks(snapshot) + check_unknowns_and_sources()} casos negativos e propagação de ausências.')
