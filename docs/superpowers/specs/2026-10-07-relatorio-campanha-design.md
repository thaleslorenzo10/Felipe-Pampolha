# Dashboard de fechamento — Felipe Pampolha

## Brief confirmado
Cliente pediu relatório com destaques e números da campanha. Usuário confirmou dashboard, 60 dias (08/08–06/10/2026), todas as campanhas Meta + Instagram @felipepampolha.rio e investimento/custos visíveis. A rodada única de dúvidas foi respondida; plano autoaprovado conforme criar e AGENTS.md. Implementação local autorizada; publicação não solicitada.

## Entrega
Nova página estática `relatorio-campanha.html`, snapshot local em `data/relatorio-campanha.json`, sem credenciais no browser. Preservar landing e painel operacional. Sem framework, build ou backend novo. HTML/CSS/JS e gráficos SVG nativos; impressão pelo navegador e download CSV. Dados fixos, data de extração explícita.

## Leitura e visual
Resumo executivo com investimento, impressões, alcance deduplicado quando disponível e crescimento líquido de seguidores. Gráfico histórico do perfil, evolução de mídia, tabela de todas campanhas, destaques de anúncios quando disponíveis e metodologia/limitações. Navegação por âncoras, tabela ordenável, layout responsivo. Paleta navy #0A1747, azul #2A55C9, papel #F4F1EA, tinta #14161C; faixa verde/ciano/laranja da identidade existente. Tipografia de sistema para evitar dependência externa. Hierarquia editorial, valores grandes, tabelas legíveis; sem slogans persuasivos ou recomendações de segmentação política.

## Integridade
Nunca somar alcance diário/campanhas como pessoas únicas. CTR/CPC/CPM recalculados a partir de totais compatíveis. Null significa indisponível, zero exige fonte. Dados parciais explicitam cobertura. Crescimento líquido por diferença de snapshots com suas datas reais; não afirmar causalidade de anúncios. Não chamar snapshot intradiário de fechamento sem verificar coletor. Não fabricar comparativos, conteúdo ou dados.

## Contrato JSON v1
`meta`: title, start, end, days, extractedAt, timezone, profile, sources (strings), notes (strings), status (complete|partial).
`ads`: source, coverageDays, missingDates, noDeliveryDates, totals {spend, impressions, reach, clicks, linkClicks, engagements, videoViews} (número|null), daily [{date,spend,impressions,clicks}], campaigns [{id,name,objective,spend,impressions,reach,clicks,linkClicks,results,resultType}], highlights [{name,impressions,reach,spend,engagements,link}] . Campos não disponíveis null; listas vazias explícitas.
`instagram`: source, coverageDays, missingDates, baseline {date,followers,capturedAt}, end {date,followers,capturedAt}, daily [{date,followers,reach,profileViews,interactions}], totals {profileViews,interactions}, notes (strings). `capturedAt` representa o instante real de coleta (ISO), exibido em America/Sao_Paulo; o coletor guarda seguidores atuais sob a data nominal do dia anterior.
Campo opcional `ads.notes` permite ressalvas específicas. Valores integrais, sem formatação, datas ISO. Não incluir tokens, dados pessoais de seguidores ou URLs com credenciais.

## Verificação
Lint e self-check de regras; testes de integridade do snapshot e cálculos; revisão independente; agent-browser em 390×844 e 1440×900, screenshots inspecionados, console/rede, navegação, ordenação e exportação. Sem build/typecheck de aplicação nesta stack. Não publicar sem autorização aplicável.

## Ajustes confirmados pela fonte
API consultada com sucesso em todo intervalo; 51 dias sem entrega reportada separados das lacunas de coleta. Destaques incluem id e campaignName para distinguir nomes repetidos. Cliques totais e cliques no link divergentes na própria API estão documentados; nenhum ajuste inventado.
