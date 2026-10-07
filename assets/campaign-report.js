'use strict';
const sources = {
  'data/relatorio-campanha.json': { id: 'act_716311018073722', name: 'Felipe Mendes Pampolha', label: 'Conta 01', legacy: true, key: 'relatorio-inicial-conta-01' },
  'data/relatorio-conta-01.json': { id: 'act_716311018073722', name: 'Felipe Mendes Pampolha', label: 'Conta 01', legacy: false, key: 'historico-conta-01' },
  'data/relatorio-conta-02.json': { id: 'act_2174013390129316', name: 'Felipe Mendes 02', label: 'Conta 02', legacy: false, key: 'historico-conta-02' }
};
const source = document.body.dataset.source;
const config = Object.hasOwn(sources, source) ? sources[source] : null;
const $ = id => document.getElementById(id);
const valid = value => typeof value === 'number' && Number.isFinite(value);
const number = value => valid(value) ? value.toLocaleString('pt-BR', { maximumFractionDigits: 0 }) : '—';
const money = value => valid(value) ? value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : '—';
const percent = value => valid(value) ? `${value.toLocaleString('pt-BR', { maximumFractionDigits: 2 })}%` : '—';
const ratio = (a, b, multiplier = 1) => valid(a) && valid(b) && b > 0 ? a / b * multiplier : null;
const signed = value => valid(value) ? `${value > 0 ? '+' : ''}${number(value)}` : '—';
const dayTime = value => Date.parse(`${String(value).slice(0, 10)}T12:00:00Z`);
const date = value => Number.isFinite(dayTime(value)) ? new Date(dayTime(value)).toLocaleDateString('pt-BR', { timeZone: 'UTC' }) : 'Data indisponível';
const captured = (row, withTime = true) => row?.capturedAt && Number.isFinite(Date.parse(row.capturedAt)) ? new Date(row.capturedAt).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo', day: '2-digit', month: '2-digit', year: 'numeric', ...(withTime ? { hour: '2-digit', minute: '2-digit' } : {}) }) : date(row?.date);
const pointTime = row => row.capturedAt && Number.isFinite(Date.parse(row.capturedAt)) ? Date.parse(row.capturedAt) : dayTime(row.date);
const text = (id, value) => { $(id).textContent = value; };
const cell = (tag, value) => { const element = document.createElement(tag); element.textContent = value; return element; };
let report;

function notes(id, values) {
  $(id).replaceChildren(...values.filter(Boolean).map(value => cell('li', value)));
  $(id).hidden = !values.filter(Boolean).length;
}

function svgElement(tag, attributes, content) {
  const element = document.createElementNS('http://www.w3.org/2000/svg', tag);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  if (content !== undefined) element.textContent = content;
  return element;
}

function chart(id, rows, key, title, fromZero) {
  const target = $(id);
  target.replaceChildren();
  const data = rows.filter(row => Number.isFinite(dayTime(row.date))).sort((a, b) => pointTime(a) - pointTime(b));
  const available = data.filter(row => valid(row[key]));
  if (!available.length) { const empty = cell('p', 'Não há dados disponíveis para este gráfico.'); empty.className = 'chart-empty'; target.append(empty); return; }
  const values = available.map(row => row[key]);
  const lower = Math.min(...values), upper = Math.max(...values), padding = Math.max((upper - lower) * .12, 1);
  const min = fromZero ? 0 : Math.max(0, lower - padding), max = Math.max(upper + padding, min + 1);
  const start = Math.min(dayTime(report.meta.start), pointTime(data[0]));
  const end = Math.max(dayTime(report.meta.end), pointTime(data[data.length - 1]), start + 86400000);
  const x = row => 68 + (pointTime(row) - start) / (end - start) * 720;
  const y = value => 220 - (value - min) / (max - min) * 190;
  const svg = svgElement('svg', { viewBox: '0 0 810 264', class: 'chart', role: 'img', 'aria-labelledby': `${id}-title ${id}-desc` });
  svg.append(svgElement('title', { id: `${id}-title` }, title));
  svg.append(svgElement('desc', { id: `${id}-desc` }, `${available.length} registros. De ${captured(available[0])} a ${captured(available[available.length - 1])}. Mínimo ${number(lower)}, máximo ${number(upper)}. Valores detalhados na tabela após o gráfico.`));
  for (let tick = 0; tick < 4; tick++) {
    const value = min + (max - min) * tick / 3, yy = y(value);
    svg.append(svgElement('line', { x1: 68, x2: 788, y1: yy, y2: yy, class: 'grid' }));
    svg.append(svgElement('text', { x: 57, y: yy + 4, 'text-anchor': 'end' }, value.toLocaleString('pt-BR', { notation: 'compact', maximumFractionDigits: 1 })));
  }
  let path = '', previous = null;
  data.forEach(row => {
    if (!valid(row[key])) { previous = null; return; }
    const continuous = previous && dayTime(row.date) - dayTime(previous.date) === 86400000;
    path += `${continuous ? 'L' : 'M'}${x(row)},${y(row[key])} `;
    previous = row;
  });
  svg.append(svgElement('path', { d: path, class: 'series' }));
  available.forEach(row => {
    const point = svgElement('circle', { cx: x(row), cy: y(row[key]), r: 3.2, class: 'point' });
    point.append(svgElement('title', {}, `${captured(row)}: ${key === 'spend' ? money(row[key]) : number(row[key])}`));
    svg.append(point);
  });
  [0, .5, 1].forEach(position => {
    const label = new Date(start + (end - start) * position).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', ...(new Date(start).getUTCFullYear() !== new Date(end).getUTCFullYear() ? { year: '2-digit' } : {}), timeZone: 'America/Sao_Paulo' });
    svg.append(svgElement('text', { x: 68 + 720 * position, y: 250, 'text-anchor': position === 0 ? 'start' : position === 1 ? 'end' : 'middle' }, label));
  });
  target.append(svg);
}

function dataRows(id, rows, keys) {
  $(id).replaceChildren(...rows.map(row => {
    const tr = document.createElement('tr');
    keys.forEach(key => tr.append(cell('td', key === 'date' ? (row.capturedAt ? `${date(row.date)} · coleta ${captured(row)}` : date(row[key])) : key === 'spend' ? money(row[key]) : number(row[key]))));
    return tr;
  }));
  if (!rows.length) { const tr = document.createElement('tr'), td = cell('td', 'Nenhum registro disponível.'); td.colSpan = keys.length; tr.append(td); $(id).append(tr); }
}

function renderCampaigns() {
  const hasResults = report.ads.campaigns.some(row => valid(row.results));
  $('result-heading').hidden = !hasResults;
  text('campaign-note', hasResults ? 'CPC calculado sobre todos os cliques. Resultados dependem do objetivo e não são somados entre tipos distintos.' : 'CPC calculado sobre todos os cliques. Resultado por objetivo não disponível; a tabela mostra métricas de entrega.');
  const query = $('search').value.toLocaleLowerCase('pt-BR'), key = $('sort').value;
  const rows = report.ads.campaigns.filter(row => `${row.name || ''} ${row.id || ''}`.toLocaleLowerCase('pt-BR').includes(query)).sort((a, b) => key === 'name' ? String(a.name).localeCompare(String(b.name), 'pt-BR') : (valid(b[key]) ? b[key] : -Infinity) - (valid(a[key]) ? a[key] : -Infinity));
  $('campaign-rows').replaceChildren(...rows.map(row => {
    const tr = document.createElement('tr'), name = cell('td', row.name || 'Campanha sem nome');
    name.append(cell('small', row.objective === 'LINK_CLICKS' ? 'Tráfego / cliques no link' : row.objective || 'Objetivo indisponível'));
    name.append(cell('small', `ID: ${row.id || 'indisponível'}`)); tr.dataset.campaignId = row.id || '';
    tr.append(name);
    [money(row.spend), number(row.impressions), number(row.reach), number(row.clicks), money(ratio(row.spend, row.clicks)), money(ratio(row.spend, row.impressions, 1000))].forEach(value => tr.append(cell('td', value)));
    if (hasResults) { const result = cell('td', number(row.results)); result.append(cell('small', row.resultType || 'Tipo indisponível')); tr.append(result); }
    return tr;
  }));
  if (!rows.length) { const tr = document.createElement('tr'), td = cell('td', report.ads.campaigns.length ? 'Nenhuma campanha corresponde à busca.' : 'O detalhamento por campanha não está disponível nesta fonte.'); td.colSpan = hasResults ? 8 : 7; td.className = 'table-empty'; tr.append(td); $('campaign-rows').append(tr); }
  text('campaign-count', `${rows.length} de ${report.ads.campaigns.length} campanhas disponíveis`);
}

function safeLink(value) {
  try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password && !url.search && !url.hash ? url.href : null; } catch { return null; }
}

function renderHighlights() {
  $('highlights').replaceChildren();
  if (!report.ads.highlights.length) { $('highlights').append(cell('p', 'Sem detalhamento de anúncios disponível nesta extração.')); return; }
  report.ads.highlights.forEach(item => {
    const article = document.createElement('article'); article.className = 'highlight';
    article.append(cell('h3', item.name || 'Anúncio sem nome'));
    if (item.campaignName) article.append(cell('p', item.campaignName));
    article.append(cell('p', `${number(item.impressions)} impressões · ${number(item.reach)} de alcance`));
    article.append(cell('p', `Investimento: ${money(item.spend)} · Interações: ${number(item.engagements)}`));
    const url = safeLink(item.link);
    if (url) { const link = cell('a', 'Abrir publicação'); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; article.append(link); }
    $('highlights').append(article);
  });
}

function renderAdsChart() {
  const key = $('metric').value;
  chart('ads-chart', report.ads.daily, key, `${$('metric').selectedOptions[0].textContent} por dia`, true);
}

function renderInstagram(ig) {
  const meta = report.meta;
  const growth = valid(ig.baseline?.followers) && valid(ig.end?.followers) ? ig.end.followers - ig.baseline.followers : null;
  text('growth', signed(growth));
  text('profile', meta.profile);
  text('growth-window', `Coletas: ${captured(ig.baseline, false)} a ${captured(ig.end, false)}`);
  text('baseline-followers', number(ig.baseline?.followers)); text('end-followers', number(ig.end?.followers));
  text('baseline-date', captured(ig.baseline)); text('end-date', captured(ig.end));
  text('growth-rate', percent(ratio(growth, ig.baseline?.followers, 100))); text('profile-views', number(ig.totals.profileViews)); text('interactions', number(ig.totals.interactions));
  text('ig-days', `${number(ig.coverageDays)} / ${meta.days}`); text('ig-coverage', `${number(ig.coverageDays)} de ${meta.days} dias nominais com registros. ${ig.missingDates.length ? `Datas nominais ausentes: ${ig.missingDates.map(date).join(', ')}.` : ''}`);
  notes('ig-notes', [...ig.notes, ig.missingDates.length ? `Datas sem registro: ${ig.missingDates.map(date).join(', ')}.` : null]);
  const history = ig.baseline && !ig.daily.some(row => row.date === ig.baseline.date) ? [ig.baseline, ...ig.daily] : ig.daily;
  chart('ig-chart', history, 'followers', 'Histórico de seguidores do Instagram', false);
  dataRows('ig-rows', history, ['date', 'followers']);
}

function render() {
  const { meta, ads, instagram: ig } = report, totals = ads.totals;
  const period = `${date(meta.start)} a ${date(meta.end)}`;
  text('coverage', `${period} · ${meta.days} dias`); text('period-badge', period);
  text('footer-period', `${config.label} · ${period}`);
  text('account-title', `${config.label} · ${meta.account?.name || config.name}`);
  text('account-id', `ID da conta: ${config.id} · Meta Ads · BRL`);
  text('account-source', `Fonte: ${ads.source}. Mídia exclusiva desta conta; não inclui nem soma a outra conta.`);
  text('spend', money(totals.spend)); text('impressions', number(totals.impressions)); text('reach', number(totals.reach));
  if (ig) renderInstagram(ig); else text('summary-clicks', number(totals.clicks));
  text('ads-coverage', `${ads.daily.length} dias com entrega reportada · ${number(ads.coverageDays)} dias consultados`);
  const noDelivery = ads.noDeliveryDates || [];
  const lastDelivery = ads.daily.length ? ads.daily[ads.daily.length - 1].date : null;
  const afterDelivery = lastDelivery && noDelivery.length && noDelivery.every(value => dayTime(value) > dayTime(lastDelivery));
  text('ads-chart-note', `Eixo vertical a partir de zero. ${noDelivery.length ? (afterDelivery ? `Sem entrega reportada após ${date(lastDelivery)}. ` : `${noDelivery.length} dias sem entrega reportada no período. `) : ''}Os dias sem entrega reportada ficam sem pontos. Ausências de dados não são convertidas em zero.`);
  text('clicks', number(totals.clicks)); text('cpc', money(ratio(totals.spend, totals.clicks))); text('cpm', money(ratio(totals.spend, totals.impressions, 1000))); text('ctr', percent(ratio(totals.clicks, totals.impressions, 100)));
  notes('ads-notes', [...(ads.notes || []), ads.missingDates.length ? `Datas sem dados na série: ${ads.missingDates.map(date).join(', ')}.` : null]);
  notes('sources', [...new Set(meta.sources)]); notes('report-notes', meta.notes);
  const extracted = new Date(meta.extractedAt);
  text('extracted', `Extração: ${Number.isFinite(extracted.getTime()) ? extracted.toLocaleString('pt-BR', { timeZone: meta.timezone }) : 'indisponível'} · Fuso: ${meta.timezone}. Snapshot fixo; esta página não atualiza as fontes automaticamente.`);
  renderAdsChart(); dataRows('ads-rows', ads.daily, ['date', 'spend', 'impressions', 'clicks']); renderCampaigns(); renderHighlights();
  const partial = meta.status !== 'complete';
  $('status').className = `status${partial ? ' partial' : ''}`;
  const coverage = `${ig ? `Instagram: ${number(ig.coverageDays)} de ${meta.days} dias com registros. ` : ''}Mídia: ${number(ads.coverageDays)} de ${meta.days} dias consultados.`;
  text('status-text', `${coverage} ${partial ? 'Cobertura parcial; consulte as ressalvas em cada seção.' : 'Consulta concluída; critérios e fontes ao final do relatório.'}`);
  $('report').hidden = false; $('export').disabled = !ads.campaigns.length; $('print').disabled = false;
}

function csvField(value) {
  let result = value === null || value === undefined ? '' : String(value);
  const first = Array.from(result.trimStart()).find(character => character.charCodeAt(0) > 32);
  if (typeof value === 'string' && ['=', '+', '-', '@'].includes(first)) result = `'${result}`;
  return `"${result.replace(/"/g, '""')}"`;
}

function campaignCSV() {
  const header = ['ID da conta', 'Conta', 'ID da campanha', 'Fonte', 'Período inicial', 'Período final', 'Campanha', 'Objetivo', 'Investimento BRL', 'Impressões', 'Alcance', 'Cliques', 'Cliques no link', 'CPC BRL', 'CPM BRL', 'Resultado', 'Tipo de resultado'];
  const rows = report.ads.campaigns.map(row => [config.id, report.meta.account?.name || config.name, row.id, report.ads.source, report.meta.start, report.meta.end, row.name, row.objective, row.spend, row.impressions, row.reach, row.clicks, row.linkClicks, ratio(row.spend, row.clicks), ratio(row.spend, row.impressions, 1000), row.results, row.resultType]);
  return [header, ...rows].map(row => row.map(csvField).join(';')).join('\r\n');
}

function exportCSV() {
  const csv = campaignCSV();
  const url = URL.createObjectURL(new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a'); link.href = url; link.download = `felipe-pampolha-${config.key}-${report.meta.start}-a-${report.meta.end}.csv`; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function load() {
  $('retry').hidden = true; $('report').hidden = true; $('print').disabled = true; $('export').disabled = true;
  document.querySelector('main').setAttribute('aria-busy', 'true'); $('status').className = 'status'; text('status-text', 'Carregando os dados do relatório…');
  try {
    if (!config || config.id !== document.body.dataset.expectedAccount) throw new Error('invalid-source');
    const response = await fetch(source, { cache: 'no-store' });
    if (!response.ok) throw new Error('snapshot-unavailable');
    const data = await response.json();
    const meta = data.meta, account = meta?.account;
    const validDate = value => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(dayTime(value)) && new Date(dayTime(value)).toISOString().slice(0, 10) === value;
    if (!validDate(meta?.start) || !validDate(meta?.end) || meta.end < meta.start || meta.days !== (dayTime(meta.end) - dayTime(meta.start)) / 86400000 + 1 || !data.ads?.totals) throw new Error('invalid-report');
    if (config.legacy && (meta.start !== '2026-08-08' || meta.end !== '2026-10-06' || !data.instagram?.totals)) throw new Error('invalid-legacy');
    if ((!config.legacy || account) && (account?.id !== config.id || account?.businessId !== '1270499364534184' || account?.currency !== 'BRL')) throw new Error('wrong-account');
    if ((!config.legacy || data.ads.accountId) && data.ads.accountId !== config.id) throw new Error('wrong-ads-account');
    if (!config.legacy && data.instagram) throw new Error('unexpected-instagram');
    for (const [object, keys] of [[data.meta, ['sources', 'notes']], [data.ads, ['daily', 'campaigns', 'highlights', 'missingDates']], ...(data.instagram ? [[data.instagram, ['daily', 'notes', 'missingDates']]] : [])]) {
      if (keys.some(key => !Array.isArray(object[key]))) throw new Error('invalid-report');
    }
    report = data; render();
  } catch {
    $('status').className = 'status error'; text('status-text', 'Não foi possível carregar um relatório válido. Tente novamente. Se o problema persistir, solicite a atualização do arquivo de dados.'); $('retry').hidden = false;
  } finally { document.querySelector('main').setAttribute('aria-busy', 'false'); }
}
window.addEventListener('beforeprint', () => document.querySelectorAll('.data-notes').forEach(detail => { if (!detail.hasAttribute('data-was-open')) detail.dataset.wasOpen = String(detail.open); detail.open = true; }));
window.addEventListener('afterprint', () => document.querySelectorAll('.data-notes').forEach(detail => { detail.open = detail.dataset.wasOpen === 'true'; delete detail.dataset.wasOpen; }));
$('metric').addEventListener('change', renderAdsChart);
$('search').addEventListener('input', renderCampaigns); $('sort').addEventListener('change', renderCampaigns);
$('export').addEventListener('click', exportCSV); $('print').addEventListener('click', () => window.print()); $('retry').addEventListener('click', load);
load();
