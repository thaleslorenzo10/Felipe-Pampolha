# Validação — dashboard de campanha

## Estado inicial
- Branch `codex/relatorio-campanha-60-dias`.
- Alterações anteriores preservadas: exclusão de `.claude/settings.json`, arquivos não versionados de harness, AGENTS.md e npm.
- Dependências de qualidade instaladas via `npm ci --ignore-scripts --no-audit --no-fund` usando lockfile existente.
- Baseline `npm run lint`: exit 0, 0 erros e 65 avisos anteriores no dashboard operacional.
- Baseline `npm run lint:rules`: três grupos passaram.
- Build e typecheck de aplicação não existem: HTML/CSS/JS estático.

## Fontes verificadas
- Supabase MCP respondeu para as tabelas específicas de Felipe; atualizado até data nominal 06/10/2026.
- Histórico Instagram e Ads sem linhas em 10 e 13/09/2026.
- Meta autenticado: conta em BRL, America/Sao_Paulo, conforme coleta do agente de dados.
- Coletor `pampolha-snapshot` confirmado: histórico Ads filtra DISTRIBUI e não cobre todas campanhas. Seguidores são o total no instante de coleta do dia seguinte, não fechamento comprovado do dia nominal.

## Execução
- `python3 scripts/check_campaign_report.py`: passou contrato, reconciliação, cobertura, ausência de segredos e oito casos negativos. Cenários sem campanhas/sem diário também conferidos após correção pela revisão independente.
- `python3 scripts/check_dashboard.py`: passou totais, crescimento, fórmulas e divisões null/zero, CSV contra fórmulas, links inseguros, busca, ordenação, troca de gráfico, largura 390/1440, erro de snapshot e recuperação.
- ESLint final: zero erros, mesmos 65 avisos anteriores; HTML novo zero erros/avisos. Self-check de regras passou.
- Gitleaks com --redact em scripts, data e HTML novo: nenhum segredo encontrado.
- Agent-browser: screenshots desktop 1440×900, mobile390×844, gráficos e página completa inspecionados. Letras dos eixos ampliadas no mobile. Sem overflow horizontal.
- Axe: zero violações detectadas; verificações inconclusivas automáticas para rótulos SVG/área rolável conferidas visualmente, sem alegação de certificação completa WCAG.
- Rede após limpeza/reload: HTML200 e JSON200; sem erros JS. Favicon inline previne requisição404.
- CSV efetivamente baixado: oito campanhas; soma735,68 concilia com fonte.
- PDF gerado e todas as seis páginas renderizadas/inspecionadas após correção de títulos órfãos. Dependências temporárias de renderização via uv, sem alterar dependências do projeto.
- Revisão independente: sem achados pendentes após correção do checker. Revisão localizada final também aprovada; revisor inspecionou as seis páginas reais do PDF.
- Artefatos de QA em /tmp/felipe-relatorio-qa/; não são fontes de dados nem publicados.

## Resultado e limitações dos dados
- Investimento Meta735,68; impressões80.551; alcance deduplicado54.327; oito campanhas. Nove dias com entrega reportada;17/08–06/10 sem resultados na reconsulta bem-sucedida. Não equivale a lacuna técnica.
- Instagram17.562→22.732, variação5.170 (29,44%), snapshots coletados08/08 e07/10 às03hBRT. Histórico diário58/60; visitas88.968 e interações269.020 representam dias registrados, não total completo comprovado.
- API retorna1.871 cliques totais e1.918 cliques no link; divergência reconfirmada e anotada sem ajuste. CPC/CTR usam cliques totais explicitamente.
- Fonte histórica de mídia é filtrada DISTRIBUI; não substitui consulta completa à API. Diferença histórica deR$0,23/21impressões documentada, sem causa inventada.
- Sem deploy: confirmação de publicação ainda necessária conforme instruções do projeto.

## Adaptação Lorenzo Admin 1.2
- Pedido adicional aplicado em relatorio-campanha.html: folhas e script locais compartilhados reutilizados sem alterações, Figtree local, menu lateral232px, header compacto, cartões brancos e fundo#f4f6f9.
- JavaScript de dados idêntico ao commit anterior; snapshot e fórmulas preservados.
- ESLint do relatório: zero erros/avisos. Lint geral: zero erros e os mesmos65 avisos preexistentes. Self-check das regras e contrato dos dados passaram.
- Regressão de navegador passou: totais, crescimento, custos, CSV, URLs, campanhas, busca, ordenação, métrica, viewports390/1440 e falha/recuperação de carga.
- Agent-browser: desktop1440×900 e mobile390×844 inspecionados, sem overflow; menu abre/fecha, Escape retorna foco ao botão, âncora fecha menu e foca seção. Logo e fonte carregadas, recursosHTTP200, console sem erros.
- Axe: zero violações, duas categorias inconclusivas (contrasteSVG e cabeçalho de tabela) conferidas visualmente. Não constitui certificação completa de acessibilidade.
- PDF atualizado em /tmp/felipe-relatorio-qa/relatorio-lorenzo.pdf: seis páginas renderizadas e inspecionadas, sem sidebar, cortes ou páginas extras.
- Revisão independente: especificação e qualidade aprovadas, nenhum achado. Artefatos de revisão em /tmp/felipe-ds-review.md e screenshots /tmp/felipe-ds-*.png.
- Nenhuma publicação realizada nesta adaptação.
