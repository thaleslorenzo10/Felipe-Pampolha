# Relatório unificado — Felipe Pampolha

Pedido: reunir contas 01 e 02 no mesmo PDF e tudo em um dashboard, preservando o design Lorenzo Media e a publicação já autorizada.

## Escopo e decisões
- Endereço principal: `/relatorio-campanha`. Visão inicial dos 60 dias (08/08–06/10/2026), com as duas contas; seletor para todo o histórico disponível até 06/10.
- Uma tabela de campanhas com origem por conta e filtro. Resumo por conta preserva alcance deduplicado individual; alcance combinado fica indisponível, nunca somado.
- Instagram mantém seu período próprio de 60 dias e as duas lacunas registradas. Não extrapolar histórico nem atribuir crescimento às campanhas.
- PDF único do histórico completo, contendo resumo dos 60 dias e Instagram com período explícito. Links antigos de contas redirecionam ao dashboard único; PDFs antigos permanecem como arquivos da entrega anterior.
- Reutilizar snapshots verificados, funções e layout. Nenhuma nova dependência ou alteração da landing/antigo painel operacional.

## Execução
1. Dados (independente): gerar snapshot consolidado a partir das três fontes existentes; validar identidades, datas, somas, campanhas de investimento zero, nulls, cobertura e hashes.
2. UI (independente): adaptar relatório existente, seletor de período, identificação/filtro de conta, CSV e link PDF; preservar estados de erro e compatibilidade das páginas anteriores.
3. Integração: redirects, lint, verificações de dados/browser e revisão independente.
4. PDF: gerar histórico sem filtros; conferir páginas, 93 IDs de campanhas, totais e período IG; inspeção visual.
5. Publicação: GitHub integrado à Vercel, sobre a main atual sem sobrescrever alterações alheias; conferir fontes e PDF byte a byte, telas desktop/mobile e navegação no domínio.

## Critérios de aceite
- Histórico: 93 campanhas, R$ 29.532,39; 60 dias: 31 campanhas, R$ 10.399,22.
- Alcance global não somado, custos calculados de totais; cada linha identifica sua conta.
- IG: 58/60 dias, +5.170 seguidores, crescimento 29,44%, sem apresentar esses números como histórico de 414 dias.
- CSV, busca, filtros e PDF conferidos; nenhum segredo publicado.

## Verificação local — 08/10/2026
- Snapshot determinístico reconciliado; 17 casos negativos e propagação de ausências aprovados; fontes originais intactas.
- Revisão independente sem achados críticos/importantes restantes. Corrigida legenda dos destaques para cinco por conta.
- Regressões no navegador: 31/93 campanhas, filtros 70/23, CSV com identidades, rejeição de payload incorreto, recuperação e contenção em 320/390/1440 px.
- ESLint: zero erros; 65 avisos preexistentes no painel operacional. Self-check das regras aprovado; sem build/typecheck aplicável.
- Gitleaks com redação: nenhuma ocorrência nos arquivos alterados.
- PDF consolidado: 19 páginas, 93 IDs conferidos e totais/períodos presentes; inspeção visual de resumo, tabelas, Instagram e destaques.
