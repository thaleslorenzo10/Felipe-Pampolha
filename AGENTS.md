# Felipe-Pampolha — Codex

Leia [CLAUDE.md](CLAUDE.md) integralmente para as instruções do projeto.
Este arquivo adapta o ambiente Codex e atualiza os comandos de qualidade abaixo;
as demais convenções e instruções locais continuam valendo.

## Inicialização e continuidade

Leia `/Users/thaleslorenzo/.codex/VCT.md` e
`/Users/thaleslorenzo/.codex/CLAUDE-MIGRATION.md`. Se o SessionStart não entregou
inventário, rode `python3 /Users/thaleslorenzo/.codex/vct/runtime.py --project "$PWD"`.
Memória deste caminho: `/Users/thaleslorenzo/.codex/vct/projects/felipe-pampolha-d173bfcb5599e5d0/MEMORY.md`. Siga as pontes existentes para tópicos Claude sem
misturar memórias de repositórios com nomes parecidos. Skills, plugins e MCPs são
globais; configurações específicas de cliente continuam locais.

## Trabalho e ferramentas

Declare suposições, faça a menor mudança necessária e verifique seu resultado.
O agente principal coordena e revisa; delegue tarefas independentes com arquivos
disjuntos. Nomes de agentes em CLAUDE.md descrevem papéis: no Codex use as
ferramentas de colaboração realmente disponíveis e uma tarefa especialista.
Não invoque ferramentas Claude `Task`/`Skill` nem tipos de agente inexistentes.
Leia SKILL.md quando aplicável. Preserve AGENTS.md aninhados e trabalho em andamento.

## Stack e comandos

HTML/CSS/JS estático · Chart.js por CDN · npm só para qualidade

- Instalação de qualidade: `npm ci`; lint: `npm run lint`; self-check: `npm run lint:rules`.
- Dev estático: `python3 -m http.server 8000`.
- Build/typecheck/testes de aplicação: não se aplicam; nenhuma etapa de build foi criada.

O package.json foi acrescentado apenas para qualidade; a página continua estática. Leia também PRODUCT.md e DESIGN.md para mudanças na landing. Lint não exige abrir integrações nem imprimir tokens presentes no código.

## Qualidade e grafo

Baseline, limites e execução estão em [.codex/harness-report.md](.codex/harness-report.md).
Não aumentar o teto de 350 nem rebaixar erros existentes para passar lint.
Consulte `graphify query` antes de investigação de código **somente se**
`graphify-out/graph.json` existir; após mudar código, `graphify update .` mantém
esse grafo. Não gerar grafo completo automaticamente. Mudança de ferramenta
não exige abrir a página; mudanças visuais exigem agent-browser.
