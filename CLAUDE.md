# Dashboard Distribuição de Conteúdo — Felipe Pampolha

> Memória do projeto para o Claude Code. Curto e de alto sinal.

## Comportamento

1. **Pensar antes de codar** — declare a suposição. Se há duas leituras possíveis, apresente as duas em vez de escolher em silêncio. Se algo está de fato ambíguo, pare e pergunte.
2. **Simplicidade primeiro** — o mínimo de código que resolve. Sem feature especulativa, sem abstração de uso único, sem configurabilidade não pedida.
3. **Mudança cirúrgica** — toque só no que o pedido exige. Siga o estilo que já está no arquivo. Não reformate nem "melhore" trecho vizinho.
4. **Execução verificável** — transforme a tarefa em algo conferível. Aqui isso quase sempre significa abrir a página no navegador e ler o screenshot, não só editar o HTML.

## Superfícies

| Arquivo | Rota | O que é |
|---|---|---|
| [home.html](home.html) | `/home` | Landing de apresentação do candidato. Público externo. Domínio: `www.felipemendespampolha.com.br`. |
| [dashboard-distribuicao.html](dashboard-distribuicao.html) | `/dashboard-distribuicao` | Painel interno de métricas de Ads e orgânico. |

Não existe `index.html`: a raiz não serve nada. As duas páginas são independentes e não
compartilham CSS nem JS — de propósito, já que uma é pública e a outra é ferramenta interna.

Contexto e regras da landing: [PRODUCT.md](PRODUCT.md) e [DESIGN.md](DESIGN.md). **Nada de
biografia, proposta ou número entra na `/home` sem fonte primária** — o PRODUCT.md lista o que já
foi verificado e o que está barrado por falta de confirmação.

## Stack

HTML/CSS/JS puro em **arquivos estáticos avulsos** — sem build, sem bundler, sem gerenciador de pacotes. Dependências entram por CDN:

- **Chart.js 4.4.0** (`cdn.jsdelivr.net`, UMD) — os dois gráficos
- **Inter** via Google Fonts

Deploy na **Vercel** (`vercel.json`, `cleanUrls: true`).

## Comandos canônicos

Não há `package.json` nem `Makefile`. Os comandos abaixo são a verdade deste repositório:

- **Install:** não há
- **Lint:** não há
- **Typecheck:** não há
- **Test:** não há
- **Build:** não há — o arquivo servido é o arquivo do repositório
- **Run/Dev:** `python3 -m http.server 8000`, depois `/home.html` ou `/dashboard-distribuicao.html`

## O que um agente erraria sem saber

- **Cada página é um arquivo só** — CSS, markup e JS juntos. Criar `src/`, módulos ou etapa de build muda o modelo de deploy e não foi pedido.
- **Os assets da `/home` vivem em [assets/](assets/)**: `fotos/*.webp` (material de campanha cedido pelo cliente, já convertido e renomeado por assunto) e `video/*.mp4` com `.vtt` de legenda e `-poster.webp`. As legendas foram transcritas por Whisper e revisadas à mão — se trocar um vídeo, gere a legenda junto: sem ela o axe acusa violação crítica.
- **Credenciais estão hardcoded no HTML público** (`TOKEN` do Meta Graph API na linha 537, `SB_KEY` anon do Supabase na linha 549). É deliberado dentro do modelo atual — página estática sem backend, chamando as APIs direto do browser —, mas significa que qualquer visitante lê o token de Ads. Tratar como dívida conhecida: **não trocar por variável de ambiente sem antes definir onde o proxy vai rodar**, senão o dashboard simplesmente para de carregar.
- **Duas fontes de dados, propósitos diferentes:**
  - **Meta Graph API v19.0** (`graph.facebook.com`) — ao vivo. Ads via `act_716311018073722`, filtrado por campanha contendo `DISTRIBUI`; orgânico via IG `17841401257663487` / FB Page `723961930805216`.
  - **Supabase REST** (`hojcntkggnwrvbvmcwxe`) — histórico. Tabelas `pampolha_ads_daily_metrics`, `pampolha_ig_daily_metrics`, `pampolha_ig_demographics`. Existe porque a **API do IG só expõe 30 dias** de orgânico; uma Edge Function (fora deste repositório) grava snapshot diário às 03h BRT.
- **O IG Insights limita o range a 30 dias.** `loadAll()` já fatia o período com `IG_MAX_RANGE` e buffer de 1h. Ao mexer em filtro de data, mantenha o fatiamento — sem ele o preset "Este ano" quebra.
- **Últimos 3–5 dias de novos seguidores vêm subestimados** por lag de reporte do Instagram. O aviso está na tela; não "corrija" o número.
- **Auto-refresh de 60 min** (`secondsLeft = 3600`) com countdown por `setInterval` de 1s. Dark mode em `localStorage["dashboard_theme"]` + `data-theme` no `<html>`.
- **Tokens de marca Lorenzo Media** ficam em `:root` (`--lm-navy #0F1B87`, `--lm-light #EAE5E2`, etc.) com bloco espelhado em `:root[data-theme="dark"]`. Cor nova entra como token, não como hex solto.
- **O logo do rodapé é um data URI base64 de ~17 KB dentro do HTML** (o `logo.png` da raiz é a mesma arte). Ao editar o arquivo com ferramenta de texto, cuidado para não quebrar essa linha.

## Verificação visual

Toda mudança aqui gera tela, então nenhuma está pronta sem passar pelo navegador (`agent-browser`, sessão nomeada): abrir, screenshot e **ler** o screenshot, conferir `console` e `network requests`. Erro de console ou requisição 4xx/5xx conta como bug mesmo com a tela parecendo certa. Conferir em 390×844 e 1440×900.

## Roteamento de especialistas

| Agente | Quando usar |
|---|---|
| `frontend-design` / `impeccable` | Mudança de layout, tipografia ou hierarquia visual do dashboard. |
| `dataviz` | Qualquer alteração nos gráficos Chart.js do dashboard — escala, eixo, série, legenda. |
| `impeccable` | Mudança visual na `/home`. Rode o detector depois: `node ~/.claude/skills/impeccable/scripts/detect.mjs --json home.html`. As supressões já justificadas ficam em `.impeccable/config.json`. |
| `code-reviewer` | Depois de editar o JS de fetch, cálculo de KPI ou renderização de tabela. |
| `ads-meta` / `ads-attribution` | Dúvida sobre a semântica das métricas do Meta Ads (CPC, CPM, alcance, atribuição) antes de mudar como o número é calculado ou rotulado. |
