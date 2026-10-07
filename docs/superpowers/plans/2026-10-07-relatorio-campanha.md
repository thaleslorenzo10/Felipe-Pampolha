# Dashboard de campanha — Implementation Plan

> Execução: superpowers:subagent-driven-development, ondas paralelas com arquivos disjuntos. Somente orquestrador commita.

**Goal:** Entregar dashboard de 60 dias conferido, apresentável à cliente, com mídia e crescimento Instagram.
**Architecture:** Página estática separada consome snapshot agregado local sem segredos; coleta autenticada fora do browser.
**Tech Stack:** HTML/CSS/JS, SVG nativo, Python stdlib para coleta; ESLint existente.
**Spec:** docs/superpowers/specs/2026-10-07-relatorio-campanha-design.md

## Global Constraints
- Período 2026-08-08 a 2026-10-06, 60 dias, America/Sao_Paulo.
- Todas as campanhas Meta da conta documentada; nenhum filtro DISTRIBUI.
- Investimento e custos visíveis; dados fixos, sem publicação.
- Preservar alterações preexistentes e credenciais. Sem escrever memória.
- Não alterar configurações de lint nem ampliar teto de 350 linhas.

## Review Focus
- Dias ausentes não viram zero; alcance não é aditivo.
- Snapshots de seguidores possuem instante de coleta distinto da data nominal.
- Totais de campanhas conciliam com total da conta ou diferença é explicada.
- Nomes externos são texto, nunca HTML; URLs limitadas a https seguro.
- Falha de carga e listas vazias devem ser visíveis; CSV deve evitar formula injection.

### Task 1: Coleta e snapshot verificável
**Files:** criar scripts/extract_campaign_report.py, scripts/check_campaign_report.py, data/relatorio-campanha.json.
**Depends-on:** nenhum. **Produces:** contrato JSON v1 integral definido na spec.
- [x] Ler fontes existentes sem imprimir segredos. Conferir Meta via token global autorizado existente; consultar apenas conta/perfil Felipe.
- [x] Coletar total conta, série diária, campanhas e anúncios do intervalo por GET com paginação e checagem de erro no corpo. Extrair histórico Instagram no Supabase; investigar definição de datas no coletor quando possível.
- [x] Reconciliar cobertura, totais e fonte. Se Meta indisponível, usar histórico agregado com ressalva explícita de ausência do detalhamento por campanha, sem alegar relatório completo.
- [x] Produzir snapshot sem tokens, valores inválidos ou precisão fabricada. Criar check executável que falhe em datas duplicadas, período incorreto, totais inconsistentes e segredos. `python3 scripts/check_campaign_report.py` deve passar.

### Task 2: Interface do dashboard
**Files:** criar relatorio-campanha.html; CSS e JS inline, script com no máximo 350 linhas.
**Depends-on:** contrato da spec; pode executar em paralelo à coleta. **Consumes:** data/relatorio-campanha.json.
- [x] Construir layout da spec com estados de carga/erro/indisponível, respeitando null e cobertura.
- [x] Criar SVGs acessíveis de seguidores e mídia sem interpolar lacunas como zero. Expor datas reais da base/fim e notas.
- [x] Tabela completa de campanhas ordenável por investimento; custo por clique e CPM recalculados. Highlights apenas quando fonte fornecer. Não criar métricas de conversão de objetivos misturados.
- [x] Implementar impressão, CSV seguro, navegação mobile e foco visível, com nomes via textContent.
- [x] Validar lint do novo HTML e relatar decisões ao orquestrador.

### Task 3: Integração, revisão e entrega
**Files:** docs/superpowers/plans/2026-10-07-relatorio-campanha-validation.md; correções localizadas nos arquivos novos.
**Depends-on:** tasks 1 e 2.
- [x] Revisão independente do snapshot, fórmulas, segurança e requisitos.
- [x] `npm run lint`, `npm run lint:rules`, `python3 scripts/check_campaign_report.py` passam sem novos erros.
- [x] Servir localmente, abrir em agent-browser com sessão própria; conferir desktop/mobile, console/rede, âncoras, ordenação e exportação; ler screenshots.
- [x] Registrar evidências e limitações. Commit somente arquivos da tarefa. Tentar abrir resultado local no Codex e fornecer preview/artefatos quando o host não oferecer o handler; publicação permanece pendente de autorização.

## Ledger
- Pré-voo: tasks 1 e 2 independentes por arquivo e usam o mesmo contrato JSON; task 3 integra. Cada tarefa tem verificação própria.
- Inventário VCT executado em modo somente leitura via função inventory, pois bootstrap criaria arquivo de memória e não há pedido de gravação de memória. Harness existente preservado.
- Branch codex/relatorio-campanha-60-dias; mudanças preexistentes de harness e settings não pertencem à tarefa.

- Integração concluída: adicionado scripts/check_dashboard.py para regressão real no navegador. Revisão independente corrigiu self-check com listas vazias. Impressão conferida em seis páginas depois de correção de quebras.
- Meta: 60 dias consultados; nove com entrega e 51 sem entrega reportada. Campo ads.noDeliveryDates distingue ausência de entrega de falha de coleta.
- open_in_codex indisponível neste host (No handler registered); apresentação final por screenshot, arquivo e link local. Nenhuma publicação executada.

### Task 4: Aplicar Lorenzo Admin 1.2 ao relatório
Pedido adicional: usar o novo design system da Lorenzo Media. Referência: folhas locais `admin-dashboard.css`, `admin-sidebar.css`, `menu-standard.css` e menu do dashboard existente, já padronizado no commit a04d4df. A documentação V3/V4 da agência tem escopo de landing e não governa este relatório.

**Files:** modificar somente apresentação de `relatorio-campanha.html`; reutilizar assets locais sem alterar as folhas compartilhadas. Preservar snapshot, fórmulas, IDs, filtros, CSV e critérios do relatório.
- [x] Substituir capa e navegação horizontal por cabeçalho compacto e menu Lorenzo; usar Figtree local, cartões brancos, azul e fundo claro do padrão atual.
- [x] Revisão independente do diff, sem mudança nas regras dos indicadores.
- [x] Conferir desktop 1440×900, celular 390×844, menu por teclado/toque, console/rede, acessibilidade e PDF sem navegação.
- [x] Executar verificações existentes, registrar resultado e commitar apenas arquivos desta tarefa. Publicação continua sem autorização.
