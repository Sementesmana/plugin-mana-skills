---
name: agente-gestor-estoque
description: "Mapa do agente-gestor-estoque (Sementes Maná), bot WhatsApp N3 Flask+PG (schema gestor_estoque no banco-mana)+Railway: lê o % de comercialização por cultivar do agente-estoque, classifica em faixas (encalhado/avançado/crítico/ruptura), alerta o grupo Comercial Estoque e DMs pelo hub agente-whatsapp, responde menu de 8 opções (PDF/PNG) e envia o relatório diário das 18h. Traz decisões, armadilhas, contratos e pendências que o código não diz. Use SEMPRE no agente-gestor-estoque ou ao citar faixas, ruptura, encalhado, allowlist, fan-out, painel-config, painel_vendas, send-image, saldo maior/menor, relatório diário, Corteva, TSI, Syngenta DeuCash, grupo Comercial Estoque."
---

# agente-gestor-estoque — mapa

## O que é
- Bot WhatsApp N3 (dono: Xayer) que vigia o **% de comercialização por cultivar** e alerta risco de **ruptura** (vendido demais) ou **encalhe** (pouca saída). Nasceu espelhando o `agente-gestor-comercial`. ADR fundador: `ManaVault/08-Decisoes/2026-06-07-novo-agente-gestor-estoque.md`.
- Hoje faz quatro coisas: (1) alerta agendado por faixa ao grupo "Comercial Estoque" + DMs; (2) responde o menu no grupo e no DM (PDF/PNG); (3) relatório diário das 18h (imagem + Excel) ao grupo; (4) portal `/vendedores` que dispara os PNGs por DM.
- Repo `Sementesmana/agente-gestor-estoque` (branch `main`). Railway project `agente-gestor-estoque`, builder NIXPACKS, healthcheck `/health`. Produção: https://agente-gestor-estoque-production.up.railway.app (`/health` 200 conferido em 2026-11-01).
- Banco: banco-mana compartilhado, schema `gestor_estoque` (sem Postgres próprio).

## Onde está a verdade
- `app/integrations/estoque_api.py` — TODO dado de estoque, TSI, Corteva e Syngenta; as fórmulas e o porquê estão nas docstrings.
- `app/workers/webhook_router.py` — menu, gate, allowlist e os handlers de resposta. `_NUM_MENU` + `_intent_deterministico` são a lista real de comandos.
- `app/services/classificador.py` + `faixas.py` (faixas, valor vigente no banco) · `reconciliador.py` (state machine) · `orchestrator.py` (pipeline + fan-out + advisory lock) · `relatorio.py` (texto do alerta).
- `app/services/relatorio_diario.py` (18h) · `painel_vendas.py` (todos os PNGs, Pillow) · `pdf_variedade.py` (PDFs, reportlab).
- `app/workers/cron.py` — jobs dinâmicos da tabela `agendamentos` + job fixo do relatório diário.
- `app/config.py` — env fail-fast e o bloco LGPD (finalidade, base legal, retenção, política de log).
- `migrations/` — schema; o 001 traz comentários de idempotência e o seed do agendamento.

## Regras e decisões que o código não explica sozinho
- **Fonte única = agente-estoque (do Dayan).** Este agente NÃO fala com o Simple Agro nem com o Protheus. Totais vêm prontos de `/api/estoque/totais`; `resumo_totais` local é só fallback. Se o estoque mudar a regra, o gestor acompanha sozinho — não reimplementar conta aqui.
- **% por cultivar** é recalculado aqui porque o `/api/estoque` não entrega pronto: pedido LÍQUIDO (qtd − devolução) ÷ disponível (bag + compra − qualidade); disponível ≤ 0 com venda → 100. Se o estoque passar a expor `pct_comercializado`/`disponivel_bag`, o cliente usa direto (compat já escrito).
- **Faixas** (defaults): < 30 ENCALHADO (promoção) · 30–80 saudável, sem alerta · 80–95 AVANÇADO (possível ruptura) · ≥ 95 CRÍTICO (interromper vendas); `> 100` = ruptura consumada. Env `FAIXA_*` é só seed: o valor vigente (e os rótulos/ações) mora na tabela `config` (linha única, CHECK de ordem) e se edita em `/painel-config`.
- **Ruptura** nos PDFs/painel = saldo < 0 OU pct > 100 (igual ao painel do estoque). No alerta do cron, `ruptura` = só pct > 100.
- **Harness / zero-LLM nas respostas**: todo o inbound é determinístico. Claude só "dá polimento" no texto do alerta do grupo (jobs GRUPO/AMBOS), com regra de nunca alterar número, e cai no texto hard-coded se falhar. DM individual sai sempre hard-coded.
- **Menu (8 opções)**: 1/2 estoque maior/menor → PDF de todas as variedades; 3/4 saldo maior/menor e 5 painel → PNG Top 10 por saldo; 6 Corteva, 7 TSI, 8 Syngenta → PNG. Número ou nome. Saudação, `menu`, `opções` e `estoque` puro → menu. Mensagem sem palavra-chave é ignorada (sem spam).
- Desligados de propósito, "voltam quando pedidos": PDF por nome de variedade (`gerar_pdf_variedade`, `_match_variedade`), listas por faixa (ruptura/avançado/encalhado), `resumo`, `painel N`. O código existe, mas o roteamento não chama. Não "consertar" sem pedido.
- **Ordenação do PDF de estoque**: chave primária estoque (maior/menor); desempate saldo mais negativo primeiro; depois nome. Cultivar com tudo zero sai do PDF.
- **Re-fetch fresco** na hora de gerar PDF/PNG (ignora o cache de 5 min usado só para detectar texto) — tempo real, igual ao botão Atualizar do painel do estoque. `/painel?forcar=1` vai além: chama o refresh de cache do próprio agente-estoque (fura o cache do SA).
- **Allowlist do DM = tabela `destinatarios`** (ativo + número). No grupo qualquer membro pergunta. Match pelos últimos 8 dígitos (Z-API diverge no DDI/9º dígito). O portal `/vendedores` grava na MESMA tabela: cadastrar vendedor = dar acesso de consulta + entrar no fan-out de alertas.
- **State machine** por `nome_norm`: NOVO, MUDANÇA (SUPERSEDED + novo), PERSISTENTE, RESOLVIDO. 1 alerta ABERTO por cultivar (índice parcial único) + advisory lock na análise.
- **Fan-out DM**: 1 envio por destinatário por dia (índice único), cap `MAX_DMS_POR_EXECUCAO`, throttle `THROTTLE_DM_S`.
- **Relatório diário guarda snapshot próprio** (`relatorio_snapshot`, 1 por dia) porque o snapshot do agente-estoque é instável. Lê o de ontem ANTES de gravar o de hoje (Era → Está → %).
- **Corteva** (SOMOS Multiplicadores 2026): conta replicada aqui a partir do consolidado TSI + compras — base 9,7%, alavancas +2% +2%, máquina +1% (ligado por padrão), bônus por saca; faturamento base só Dermacor+Lumialza+Lumitreo. **Syngenta**: fonte única `/api/syngenta/resumo`; o cálculo local é aproximado (Rebate sem reciprocidade, RCA = 0) e só roda se o endpoint cair.
- LGPD (config.py): legítimo interesse; nunca logar nome de cliente/valor nem payload do `/api/estoque`; telefone mascarado (últimos 4). Retenção declarada: alertas/snapshots 2 anos.

## Armadilhas conhecidas (sintoma → causa → o que fazer)
- "Mando resumo / nome da variedade / ruptura e o bot não responde" → comando fora do gate ou desativado → é por decisão; usar o menu (1–8).
- "Bom dia" no grupo dispara o menu → saudações estão em `_MENU_WORDS` → comportamento atual; mexer só se o Xayer pedir.
- PNG não chega e vem PDF ou texto → fallback em cascata (PNG → PDF-resumo → texto). Primeiro suspeito: fontes ausentes em `static/fonts` (Poppins/DejaVuSerif, `truetype` levanta) ou o hub fora. Logo ausente NÃO quebra (cai no desenho vetorial).
- Faixas do relatório das 18h ≠ faixas do alerta → `relatorio_diario._faixa` tem cortes fixos próprios (90/60, ruptura = saldo < 0) que não leem a tabela `config` → ao mexer em faixa, decidir se o diário acompanha.
- Totais divergem do painel do estoque → `/api/estoque/totais` caiu e entrou o `resumo_totais` local → conferir o endpoint do estoque antes de mexer na conta.
- Números da Syngenta "estranhos" → fallback local aproximado em uso → conferir `/api/syngenta/resumo` no agente-estoque.
- Corteva diverge do simulador do estoque → a conta está duplicada aqui → mudança de regra da campanha tem de ser feita nos dois lados.
- Grupo recebe a lista inteira toda execução → a mensagem lista todos os ABERTOS (persistentes inclusos, marcando 🆕/🔁); só o contador de notificações distingue. A docstring do reconciliador ("só NOVO e MUDANÇA") não vale para o texto do grupo.
- Webhook responde 503 "webhook desabilitado" → falta `ROUTER_SHARED_SECRET` no gestor-estoque. Responde 401 → `ESTOQUE_BOT_SECRET` do router diferente do `ROUTER_SHARED_SECRET` daqui → os dois têm de ser iguais.
- `/health/deep` degraded com `claude: false` → o check só testa se `ANTHROPIC_API_KEY` começa com `sk-`, mesmo usando o gateway.
- Migration nova "não roda" → controle em `schema_migrations`: cada arquivo roda 1 vez; falha é só logada e o boot segue → olhar o log `[DB] migration ... falhou`. `{{SCHEMA}}` é obrigatório no SQL.
- Cron duplicado → APScheduler roda dentro do processo; com mais de 1 worker cada worker agenda. Manter `--workers 1`. O relatório diário não tem lock.
- DM do fan-out "pulada" à noite → a idempotência diária usa a data UTC → após 21h BRT já conta como o dia seguinte.
- CI verde não prova nada → o workflow só roda `test_*.py` na RAIZ; os testes vivem em `tests/` → rodar `pytest` local.

## Contratos com sistemas externos
- **agente-estoque** (`ESTOQUE_API_URL`, default a produção do estoque; Bearer opcional `ESTOQUE_API_TOKEN`): `/api/estoque` (envelope `status: ok` + `data[]`), `/api/estoque/totais`, `/api/cache/refresh`, `/api/tsi/consolidado` (`ok` + totais/produtos/receitas/meta), `/api/compras`, `/api/syngenta/resumo` e `/premiacao`. Só leitura. Mudança de shape lá quebra aqui.
- **Hub agente-whatsapp** (porta única, nunca Z-API direto): `/send-whatsapp` (texto), `/send-document` (PDF e XLSX), `/send-image` (PNG), header `X-API-Key`, campo `agente` = `agente-gestor-estoque`. Grupo = id `...-group`; DM = `55DDDNÚMERO`.
- **agente-router** (inbound): POST `/webhook` (ou `/webhook-router`) com o payload BRUTO da Z-API (`text.message`, `phone`, `fromMe` ignorado); auth `X-Router-Secret` ou Bearer = `ROUTER_SHARED_SECRET`. No router: `ESTOQUE_GRUPO_IDS`, `ESTOQUE_BOT_URL`, `ESTOQUE_BOT_SECRET`; o slot serve o grupo E a keyword DM `estoque` (sticky 30 min). Áudio chega já transcrito (Whisper no router).
- **Grupo "Comercial Estoque"**: `GRUPO_GESTOR_ESTOQUE_ID` = `120363409759904989-group`.
- **LLM**: mana-llm-gateway se `LLM_GATEWAY_URL` + `LLM_GATEWAY_KEY` (alias `LLM_MODEL`, default `mana-rapido`); senão Anthropic direto com `CLAUDE_MODEL` (Haiku). `ANTHROPIC_API_KEY` continua obrigatória no boot.
- **banco-mana**: escrever só em `gestor_estoque` (search_path fixado por conexão).

## Como testar e subir
- `pip install -r requirements.txt` e `pytest -q` (testes do classificador, sem rede/banco/LLM). Rodar local exige as env obrigatórias (o boot é fail-fast).
- Operação manual (Bearer): `POST /executar-analise` com `{usar_claude, enviar_whatsapp}` e `POST /executar-fan-out?dry_run=1` antes de disparar de verdade. Relatório diário: preview em `/relatorio-diario.png` e `.xlsx` (não envia); envio manual em `/relatorio-diario/enviar`.
- Destinatário novo: smoke-test pelo `/painel-config` antes de contar com ele.
- Deploy = `git push origin main` → Railway (~2 min); migrations no boot. Conferir `/health` e `/health/deep`.
- Liga/desliga por env: `ENABLE_CRON`, `ENABLE_CRON_LOAD`, `RELATORIO_DIARIO` (+ `RELATORIO_DIARIO_CRON`, default 18h BRT).
- Clone local do Xayer: `C:\Users\Sementes Mana\Desktop\ORQUESTRADOR\agente-gestor-estoque\`.

## Pendências conhecidas
- Envio ao hub sem `classe` e sem `idempotency_key` (o padrão Maná exige) — só manda `agente`.
- `PAINEL_SENHA` tem default fraco no código e a senha trafega na query string.
- Safra "26/27" fixa como default nos PNGs — revisar na virada de safra.
- Retenção de 2 anos declarada, sem rotina de expurgo.
- Excel do relatório diário leva clientes por variedade ao grupo — confirmar com o Xayer que o grupo é o público certo (LGPD).
- Código morto do NLP com Claude (`_classificar`) e respostas de texto antigas: manter ou limpar só com decisão.
- Possível migração para a habilidade `mana-habilidade-notificacao-whatsapp` (cadastro + cron + envio), que cita este agente como origem do código replicado.

## Para ir além
- Não há `CLAUDE.md` no repo. Nota canônica do vault: `ManaVault/06-Agentes-e-Skills/agente-gestor-estoque.md`; parecer original: `00-Inbox/2026-06-07-parecer-agente-gestor-estoque.md`; ADR fundador em `08-Decisoes`.
- Skills vizinhas: `agente-estoque` (fonte dos dados e do TSI), `agente-whatsapp`, `agente-router`, `mana-arquitetura-padrao`.
