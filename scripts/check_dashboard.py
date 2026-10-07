#!/usr/bin/env python3
"""Browser regressions for the original report and isolated account pages."""
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
SESSION = "felipe-account-pages-check"
PAGES = [
    ("campanha", "act_716311018073722", "relatorio-inicial-conta-01"),
    ("conta-01", "act_716311018073722", "historico-conta-01"),
    ("conta-02", "act_2174013390129316", "historico-conta-02"),
]


def browser(*args):
    result = subprocess.run(["agent-browser", "--session", SESSION, *args],
                            text=True, capture_output=True, check=True)
    return result.stdout


def evaluate(script):
    return json.loads(browser("eval", script))


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def check_page(slug, account_id, file_key):
    expected = json.loads((ROOT / "data" / f"relatorio-{slug}.json").read_text())
    browser("wait", "#report:not([hidden])")
    state = evaluate(r"""(() => {
      const check = (ok, message) => { if (!ok) throw Error(message); };
      check(document.querySelector('#spend').textContent === money(report.ads.totals.spend), 'investment');
      check(document.querySelector('#coverage').textContent.includes(String(report.meta.days)), 'coverage');
      check(document.querySelector('#account-id').textContent.includes(config.id), 'account label');
      check(ratio(10,0) === null && ratio(null,10) === null && ratio(0,10) === 0, 'division boundaries');
      check(ratio(20,1000,1000) === 20, 'CPM');
      check(csvField('=1+1').startsWith("\"'="), 'CSV formula');
      check(csvField(' \t@SUM(A1)').startsWith("\"'"), 'CSV whitespace formula');
      check(csvField('a"b') === '"a""b"', 'CSV quotes');
      check(safeLink('javascript:alert(1)') === null && safeLink('https://u:p@example.com') === null, 'unsafe URLs');
      const ids = [...document.querySelectorAll('#campaign-rows tr')].map(row => row.dataset.campaignId);
      check(ids.length === report.ads.campaigns.length, 'all campaigns');
      check(new Set(ids).size === ids.length, 'unique campaign IDs');
      if (config.legacy) {
        check(document.querySelector('#growth').textContent === '+5.170', 'original growth');
        check(document.querySelector('#growth-rate').textContent === '29,44%', 'original growth rate');
        check(report.meta.days === 60, 'original period');
      } else {
        check(!document.querySelector('#instagram') && !report.instagram, 'history must not include Instagram');
        check(document.querySelector('#summary-clicks').textContent === number(report.ads.totals.clicks), 'click KPI');
        check(!!document.querySelector('a[href="relatorio-campanha.html#instagram"]'), 'Instagram report link');
        check(report.meta.account.id === config.id && report.ads.accountId === config.id, 'account isolation');
      }
      return { account: config.id, ids, source, days: report.meta.days, spend: report.ads.totals.spend };
    })()""")
    assert state["account"] == account_id
    assert state["source"] == f"data/relatorio-{slug}.json"
    assert state["spend"] == expected["ads"]["totals"]["spend"]
    assert sorted(state["ids"]) == sorted(row["id"] for row in expected["ads"]["campaigns"])
    assert state["days"] == expected["meta"]["days"]
    first_id = expected["ads"]["campaigns"][0]["id"]
    browser("fill", "#search", first_id)
    assert evaluate("document.querySelectorAll('#campaign-rows tr').length") == 1
    assert evaluate("document.querySelector('#campaign-rows tr').dataset.campaignId") == first_id
    browser("fill", "#search", "")
    browser("select", "#sort", "clicks")
    assert evaluate("document.querySelector('#campaign-rows tr').dataset.campaignId") == max(expected["ads"]["campaigns"], key=lambda row: row["clicks"] or 0)["id"]
    browser("select", "#metric", "impressions")
    assert "Impressões" in evaluate("document.querySelector('#ads-chart-title').textContent")
    exported = evaluate(r"""(async () => {
      const create = URL.createObjectURL, click = HTMLAnchorElement.prototype.click;
      let blob, filename;
      URL.createObjectURL = value => { blob = value; return 'blob:regression-check'; };
      HTMLAnchorElement.prototype.click = function () { filename = this.download; };
      try { exportCSV(); return { filename, csv: await blob.text() }; }
      finally { URL.createObjectURL = create; HTMLAnchorElement.prototype.click = click; }
    })()""")
    assert exported["filename"] == f"felipe-pampolha-{file_key}-{expected['meta']['start']}-a-{expected['meta']['end']}.csv"
    rows = list(csv.DictReader(io.StringIO(exported["csv"].lstrip("\ufeff")), delimiter=";"))
    assert len(rows) == len(expected["ads"]["campaigns"])
    assert {row["ID da conta"] for row in rows} == {account_id}
    assert sorted(row["ID da campanha"] for row in rows) == sorted(state["ids"])
    assert {row["Período inicial"] for row in rows} == {expected["meta"]["start"]}
    assert {row["Fonte"] for row in rows} == {expected["ads"]["source"]}
    for width, height in [(320, 844), (390, 844), (1440, 900)]:
        browser("set", "viewport", str(width), str(height))
        assert evaluate("document.documentElement.scrollWidth <= innerWidth"), f"overflow {slug}: {width}"
        assert evaluate("[...document.querySelectorAll('.kpi-value')].every(value => value.scrollWidth <= value.clientWidth)"), f"KPI card overflow {slug}: {width}"
    route = f"**/data/relatorio-{slug}.json"
    bad = copy.deepcopy(expected)
    other_id = "act_2174013390129316" if account_id == "act_716311018073722" else "act_716311018073722"
    bad["meta"]["account"] = {"id": other_id, "businessId": "1270499364534184", "currency": "BRL"}
    invalid_payloads = [{}, bad]
    if slug != "campanha":
        wrong_ads = copy.deepcopy(expected)
        wrong_ads["ads"]["accountId"] = other_id
        invalid_payloads.append(wrong_ads)
    for payload in invalid_payloads:
        browser("network", "route", route, "--body", json.dumps(payload))
        browser("reload")
        browser("wait", "#retry:not([hidden])")
        assert evaluate("document.querySelector('#report').hidden && document.querySelector('#export').disabled && document.querySelector('#print').disabled")
        browser("network", "unroute", route)
        browser("click", "#retry")
        browser("wait", "#report:not([hidden])")
    print(f"OK: {slug}, {len(rows)} campaigns, {state['days']} days; account/CSV IDs, search, sort, viewport/card containment320/390/1440 and swapped-account rejection")


def main():
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        browser("open", f"{base}/relatorio-campanha.html")
        for index, (slug, account_id, file_key) in enumerate(PAGES):
            if index:
                browser("click", f'.report-links a[href="relatorio-{slug}.html"]')
                browser("wait", "--url", f"**/relatorio-{slug}.html")
            check_page(slug, account_id, file_key)
        browser("click", '.report-links a[href="relatorio-campanha.html"]')
        browser("wait", "--url", "**/relatorio-campanha.html")
        browser("wait", "#report:not([hidden])")
        assert evaluate("config.legacy && !!document.querySelector('#instagram')")
        print("OK: real navigation through all three pages and back to original")
    finally:
        browser("close")
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
