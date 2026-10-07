# Relatórios por conta — implementação

**Objetivo:** páginas separadas das contas Felipe Pampolha 01 e 02, no Lorenzo Admin 1.2, com todas as campanhas do período. Decisão explícita do usuário: TODO o histórico disponível de cada conta. Consultar desde a criação da conta até06/10/2026, último dia completo deste fechamento.

**Contas verificadas:** `act_716311018073722` (Felipe Mendes Pampolha) e `act_2174013390129316` (Felipe Mendes 02), ambas no negócio `1270499364534184` (Felipe Pampolha), BRL e America/Sao_Paulo. A segunda foi criada em17/08/2026.

**Arquitetura:** preservar relatório existente, publicar artefatos locais independentes por conta e reutilizar apresentação/comportamento já validados. Snapshot sem credenciais, coletado por GET na API. As páginas históricas são de mídia (Meta Ads), com link ao relatório existente de60 dias para a análise do Instagram. Não misturar sua cobertura limitada com o histórico completo de anúncios.

## Restrições
- Sem filtro por nome/status das campanhas; incluir entrega reportada no intervalo, inclusive campanhas hoje pausadas e nomes repetidos com IDs distintos.
- Alcance deduplicado somente no nível da conta; taxas recalculadas pelos totais. Nunca somar alcance das duas contas.
- Não atualizar o snapshot anterior silenciosamente. Conta e período explícitos na tela e no CSV. Períodos históricos explícitos e distintos por conta; metadados da conta conferidos na API.
- Preservar folhas Admin compartilhadas e todas as alterações preexistentes. Sem publicação externa.

## Tarefas
- [x] Dados: parametrizar a coleta existente sem alterar seu padrão; coletar dois snapshots separados, validar identidade, conciliar total/diário/campanhas e testar rejeição de troca de conta.
- [x] Interface: duas páginas de mídia com links entre relatórios, período dinâmico, identidade visível, IDs das campanhas, CSV por conta e mesma apresentação Lorenzo. Reutilizar CSS/JS comuns caso necessário para evitar três implementações divergentes.
- [x] Integração: revisão independente; lint, checks de contrato e navegador para ambas as contas, mobile/desktop, links, busca, exportação e PDF. Commits pelo coordenador.

## Critérios de aceite
Cada página deve mostrar somente a mídia de sua conta; CSV deve carregar conta/ID/período. Campanhas homônimas não podem se fundir. Sem segredos no HTML/JSON. Erro de fonte deve ser visível. O relatório anterior continua funcional. PDF e gráficos sem cortes.

## Contrato acordado entre agentes
- Novos snapshots contêm `meta` e `ads` (sem objeto Instagram); original preserva `instagram`.
- `meta.account`: id, name, label, businessId, currency, createdTime.
- Datas e dias inclusivos vêm de meta, não de texto fixo. Inícios verificados: conta01 em19/08/2025; conta02 em17/08/2026.
- collect_ads recebe conta/início/fim opcionais e mantém os valores antigos como padrão.
- Novo validador verifica identidade/intervalo/conciliação de anúncios sem exigir60dias.

## Entrega verificada
- Conta 01: 414 dias consultados, 70 campanhas, R$ 19.868,85, 2.458.244 impressões e alcance de 946.376. Conta 02: 51 dias, 23 campanhas, R$ 9.663,54, 1.494.360 impressões e alcance de 579.922. Totais por conta conciliados com diário e campanhas.
- Verificação dos dados: 13 casos negativos e 8 legados; padrão de 60 dias preservado. Regressão no navegador: três páginas em 320/390/1440 px, busca, ordenação, gráfico, rejeição de identidades trocadas, recuperação e CSV.
- CSVs efetivamente baixados e reconciliados: IDs de conta e campanha, 70/23 linhas e somas de investimento corretas.
- Lint: zero erros, 65 avisos anteriores no dashboard operacional; arquivos novos sem avisos. Self-check de regras passou. Aplicação estática, sem build/typecheck.
- Gitleaks com --redact: nenhum segredo em scripts, dados e HTML/CSS/JS do relatório. Snapshot original permanece idêntico.
- Agent-browser: desktop e celular inspecionados, rede com respostas 200/304 e console sem erros. Axe detectou zero violações nas duas contas; contraste SVG e cabeçalho de tabela têm verificações automáticas inconclusivas, conferidas manualmente, sem certificação WCAG.
- Corrigidos no QA: valor financeiro transbordando cartão no celular (teste mede conteúdo, além do viewport) e nota órfã do PDF original (espaçamento de impressão).
- PDFs finais renderizados e conferidos: original com 6 páginas, conta 01 com 12 e conta 02 com 7. Todos os IDs de campanhas presentes; tabelas sem cortes e cabeçalhos repetidos. Artefatos: /tmp/felipe-campanha-final.pdf, /tmp/felipe-conta-01-final.pdf e /tmp/felipe-conta-02-final.pdf.
- Revisão independente aprovou especificação e qualidade sem achados pendentes (/tmp/felipe-accounts-review.md). Nenhuma publicação externa realizada.
