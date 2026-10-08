#!/usr/bin/env python3
"""Browser regression for consolidated periods, account origin and fail-closed load."""
import copy
import csv
import functools
import http.server
import io
import json
from pathlib import Path
import subprocess
import threading

ROOT = Path(__file__).resolve().parents[1]
SESSION = 'felipe-unified-check'


def browser(*args):
    return subprocess.run(['agent-browser', '--session', SESSION, *args], capture_output=True, text=True, check=True).stdout


def evaluate(script):
    return json.loads(browser('eval', script))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def main():
    snapshot = json.loads((ROOT / 'data/relatorio-unificado.json').read_text())
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/relatorio-campanha.html'
    try:
        browser('open', url)
        browser('wait', '#report:not([hidden])')
        recent_chart = evaluate("document.querySelector('#ig-chart').innerHTML")
        for view, spend, count in [('recent', 10399.22, 31), ('history', 29532.39, 93)]:
            browser('select', '#view', view)
            assert evaluate('report.ads.totals.spend') == spend
            assert evaluate("document.querySelector('#spend').textContent === money(report.ads.totals.spend)")
            assert evaluate("document.querySelectorAll('#campaign-rows tr').length") == count
            assert evaluate("document.querySelector('#reach').textContent === number(report.ads.totals.clicks)")
            assert evaluate("document.querySelector('#ig-days').textContent") == '58 / 60'
            assert evaluate("document.querySelector('#growth').textContent") == '+5.170'
            assert evaluate("document.querySelector('#ig-chart').innerHTML") == recent_chart
            assert evaluate("document.querySelector('#recent-summary').hidden") == (view == 'recent')
            for account in snapshot['views'][view]['accounts']:
                browser('select', '#campaign-account', account['id'])
                expected = sum(row['accountId'] == account['id'] for row in snapshot['views'][view]['ads']['campaigns'])
                assert evaluate("document.querySelectorAll('#campaign-rows tr').length") == expected
                assert evaluate("[...document.querySelectorAll('#campaign-rows tr')].every(row => row.dataset.accountId === document.querySelector('#campaign-account').value)")
                assert evaluate('report.ads.totals.spend') == spend
            csv_text = evaluate('campaignCSV()')
            rows = list(csv.DictReader(io.StringIO(csv_text), delimiter=';'))
            assert len(rows) == count  # CSV includes both accounts despite table filter.
            assert {row['ID da conta'] for row in rows} == {'act_716311018073722', 'act_2174013390129316'}
            assert abs(sum(float(row['Investimento BRL']) for row in rows) - spend) < .01
            for row in rows:
                source = next(item for item in snapshot['views'][view]['ads']['campaigns'] if item['id'] == row['ID da campanha'])
                assert row['ID da conta'] == source['accountId'] and row['Conta'] == source['accountName']
            browser('select', '#campaign-account', 'all')
            target_id = snapshot['views'][view]['ads']['campaigns'][0]['id']
            browser('fill', '#search', target_id)
            assert evaluate("document.querySelectorAll('#campaign-rows tr').length") == 1
            browser('fill', '#search', '')
            browser('select', '#sort', 'clicks')
            assert evaluate("document.querySelector('#campaign-rows tr').dataset.campaignId") == max(snapshot['views'][view]['ads']['campaigns'], key=lambda row: row['clicks'] or 0)['id']
            for width, height in [(320, 844), (390, 844), (1440, 900)]:
                browser('set', 'viewport', str(width), str(height))
                assert evaluate('document.documentElement.scrollWidth <= innerWidth'), f'page overflow {view}/{width}'
                assert evaluate("[...document.querySelectorAll('.kpi-value')].every(node => node.scrollWidth <= node.clientWidth)"), f'KPI overflow {view}/{width}'
        browser('open', url + '?view=history')
        browser('wait', '#report:not([hidden])')
        assert evaluate('report.ads.campaigns.length') == 93
        assert evaluate("document.querySelector('#download-pdf').getAttribute('href')") == 'relatorios/relatorio-consolidado.pdf'
        bad_account = copy.deepcopy(snapshot)
        bad_account['views']['history']['accounts'][1]['id'] = 'act_foreign'
        bad_campaign = copy.deepcopy(snapshot)
        bad_campaign['views']['recent']['ads']['campaigns'][0]['accountId'] = 'act_foreign'
        bad_reach = copy.deepcopy(snapshot)
        bad_reach['views']['history']['ads']['totals']['reach'] = 1000000
        missing_view = copy.deepcopy(snapshot)
        del missing_view['views']['history']
        route = '**/data/relatorio-unificado.json'
        for payload in [{}, bad_account, bad_campaign, bad_reach, missing_view]:
            browser('network', 'route', route, '--body', json.dumps(payload))
            browser('reload')
            browser('wait', '#retry:not([hidden])')
            assert evaluate("document.querySelector('#report').hidden && document.querySelector('#export').disabled && document.querySelector('#print').disabled && document.querySelector('#download-pdf').hidden")
            browser('network', 'unroute', route)
            browser('click', '#retry')
            browser('wait', '#report:not([hidden])')
        print('OK: 60 days/history sums; 31/93 campaign origins; account filters; CSV; independent IG chart; history URL;320/390/1440 containment;5 invalid payloads/retry.')
    finally:
        browser('close')
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
