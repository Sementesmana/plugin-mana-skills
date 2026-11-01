---
name: agente-bot-multiplicacao
description: "Mapa do agente-bot-multiplicacao (Sementes Maná): bot WhatsApp que vigia pedidos do Simple Agro com Uso da Semente = MULTIPLICAÇÃO, alerta o grupo Trigger pedidos (NOVO, MUDANCA_STATUS, MUDANCA_DADOS, faturamento via status_erp) e responde perguntas do grupo com Claude. Flask + APScheduler + banco-mana (schema multiplicacao), arquitetura data lake (só a ingestão fala com o SA). Traz decisões, armadilhas, contratos e pendências que o código não diz. Use SEMPRE no agente-bot-multiplicacao ou ao citar bot multiplicação, grupo Trigger pedidos, sa_lake, guarda de semeadura, status_erp, FATURADO TOTAL/PARCIAL, frete CIF rateado, bag não sacas, SILENT_BACKFILL, reconciliação, fromMe, 452."
---

# agente-bot-multiplicacao — mapa

## O que é
- Bot WhatsApp que monitora pedidos do Simple Agro (SA) com `uso_semente = MULTIPLICACAO` na safra ativa (grupo de produto Soja), avisa o grupo interno "Trigger pedidos" em horários fixos e responde perguntas livres do grupo (Claude sobre o snapshot).
- Repo `Sementesmana/agente-bot-multiplicacao` (isolado, Caminho A: código na raiz, Root Directory VAZIO no Railway). Dono: não declarado no repo.
- Produção: https://agente-bot-multiplicacao-production.up.railway.app (projeto Railway `Agente-bot-multiplicacao-SM`; a URL só aparece no SKILL.md, não no código).
- Banco-mana, schema `multiplicacao`. Nunca toca o SoftExpert.

## Onde está a verdade
- `agente_bot_multiplicacao.py` — ingestão do lake, ciclo de alerta, dedup (`_processar_pedido`), diff (`computar_alteracoes`), heartbeat, textos das mensagens.
- `sa_client.py` — login SA, filtro por uso da semente, achatamento do pedido (valor, frete rateado, status_erp, máscara de CPF). Cópia inline espelhada do cliente do agente-mapa-pedidos (não usa o SDK mana-simpleagro).
- `app.py` — rotas, auth (senha/token/secret), rate limit, scheduler (os dois crons), `/admin/migrate`, `/api/reconciliacao`.
- `claude_nlp.py` — system prompt do grupo + escolha gateway × Anthropic direto.
- `whatsapp_client.py` — contrato com o hub agente-whatsapp. `db.py` — pool e acesso ao schema. `migrations/*.sql` — DDL idempotente (comentários dizem o porquê).
- `templates/painel.html` — painel com 3 abas (Pedidos atuais, Log de alertas, Execuções do cron) + botão "atualizar lake" e disparo manual do cron.
- README está defasado (fala de cron único lendo o SA e auth só por `X-Router-Secret`): siga o código.

## Regras e decisões que o código não explica sozinho
- **Data lake (ADR 2026-07-29)**: o SA é tocado por UM caminho só — `ingerir_lake` (cron de ingestão + botão do painel). Alerta, painel e NLP do grupo leem `multiplicacao.sa_lake`, nunca o SA. Motivo: o SA é single-session e outros agentes dividem o usuário; cada chamada a mais é risco de 452. Não adicionar chamada ao SA no webhook/alerta, nem quando o grupo pede "atualiza o status".
- A ingestão roda ANTES do alerta, com folga (padrão 06/11/15 × 08/12/16 BRT). Mexer num horário exige mexer no outro.
- Ingestão que volta vazia NÃO sobrescreve o lake (preserva o último snapshot bom e registra erro no `cron_run`). Falha nunca vira dado.
- `pedido_estado` é o histórico acumulado usado para dedup; o lake é a foto atual. Pedido que sumiu do SA continua em `pedido_estado` ("fantasma") — por isso existe `/api/reconciliacao` (read-only), nascido da pergunta "são 57 mesmo?".
- **Alerta de dados (desde 2026-07-30)**: qualquer alteração dispara (status, valor, nº de itens, cultivares +/−/qtd, vendedor, fazenda, município/UF, faturamento), porque o time edita pedido no SA sem mudar status. TSI ainda fora do diff (não está no resumo do item).
- **Faturamento (decisão Xayer 2026-09-18)**: o grupo só é avisado de faturamento. Só vira mensagem a transição em que um dos lados é `FATURADO PARCIAL` ou `FATURADO TOTAL` (entrou, evoluiu, estornou). `LIBERADO → AGUARDANDO FATURAMENTO` (estado de repouso da maioria da carteira), `Erro Integração`, `ELIMINADO RESÍDUO` ficam calados, mas gravados e visíveis no painel e no NLP. `status_erp` viaja no `payload` JSONB, sem coluna/migration.
- **GUARDA DE SEMEADURA — não remover**: só compara `status_erp` se a chave já existe no payload antigo. Sem ela, o 1º cron após um deploy que passa a coletar um campo novo dispara UM ALERTA POR PEDIDO da carteira. Repetir a mesma guarda para qualquer campo novo no diff (ex.: TSI).
- Coluna "Status Pedido" do painel SA = `status_pedido + " / " + status_erp` (dois campos irmãos do mesmo documento, sem chamada extra). Valores reais medidos na sonda de 2026-09-18: `status_pedido` ∈ Integrado/Cancelado/Aguardando Aprovação/Reprovado; `status_erp` ∈ AGUARDANDO FATURAMENTO/FATURADO TOTAL/FATURADO PARCIAL/Erro Integração/ELIMINADO RESÍDUO/LIBERADO/CANCELADO. O SDK mana-simpleagro documenta `'Aprovado'`, que NÃO existe.
- **Valor (regra Maná validada 2026-05-13 no pedido 260000040022/1, R$ 259.000)**: total do pedido = soma das parcelas (já inclui frete CIF; bate com o "Total Pedido" do espelho). `total_preco_item` é LÍQUIDO sem frete (~3% abaixo em CIF): o frete (parcelas − líquidos) é rateado por item na proporção do líquido. Nunca usar `preco_frete_tabela_item` (vem zero em vários pedidos, mesmo bug do agente-financeiro-sa).
- **Unidade = bag, NUNCA sacas** (`item.quantidade` já vem em bag). Alinhado com agente-financeiro-sa e agente-pedidos; o prompt do Claude ensina isso.
- Heartbeat: cron agendado sem novidade manda "sinal de vida" no grupo; lake vazio manda alerta HONESTO ("data lake sem pedidos", alertas pausados) em vez de "sem novidades" — o "0 pedidos, sem novidades" já mascarou um apagão 452. Disparo manual não manda heartbeat (para o Xayer testar sem spam).
- **Quem fala com o bot é decidido no agente-router**: o `/webhook` não filtra grupo nem remetente e responde a qualquer grupo ou DM roteado com dados de pedidos (cliente, valor, vendedor). Não rotear grupo/DM novo para cá sem decidir quem pode ver.
- Acesso: `PAINEL_SENHA` cai no default público `mana2026` se a env faltar, e a senha trafega na query string (fica em log/histórico) → setar no Railway. `CRON_TOKEN` vazio NÃO é gerado: `/cron/verificar` e `/admin/migrate` recusam tudo (401).
- LGPD: legítimo interesse, grupo interno. CPF/CNPJ nunca em claro (máscara `***1234` + hash MD5 no banco); retenção `pedido_estado` enquanto a safra está ativa, `alerta_log` 5 anos.
- `workers=1` é obrigatório (SA single-session; rate limit e scheduler são in-process).

## Armadilhas conhecidas (sintoma → causa → o que fazer)
- Grupo inundado com um alerta por pedido após deploy → campo novo no diff sem guarda de semeadura, ou `pedido_estado` zerado com `SILENT_BACKFILL=false` → guarda sempre; para repovoar, ligar backfill na 1ª rodada.
- Grupo inundado com MUDANCA_DADOS em todos os pedidos no 1º cron pós-deploy → mudou a fórmula de valor/frete, a contagem de itens ou o nome/achatamento da cultivar; o diff compara valor, itens e cultivares SEM guarda e `SILENT_BACKFILL` só vale para pedido novo (a skill antiga dizia que recalcular valor era seguro: deixou de ser em 2026-07-30) → antes do deploy, criar guarda (ex.: versão do cálculo no payload, comparar só se igual) ou regravar `pedido_estado` em silêncio antes do 1º alerta.
- Pedidos novos entram sem alerta → `SILENT_BACKFILL` ausente no Railway: o default no CÓDIGO (e no `.env.example`) é `true` → no Railway tem de estar `false` explícito.
- "data lake sem pedidos" no grupo / alertas parados → ingestão falhou (SA 452, credencial, lake nunca ingerido) → ver aba Execuções (`ingest-*` com erro) e `/api/lake-status`; forçar pelo botão do painel.
- SA respondendo 452 → outro agente/humano logou com o mesmo usuário → `get_orders` reloga e tenta UMA vez só, de propósito (retry ilimitado vira guerra de login entre agentes).
- `/cron/verificar` estourando timeout de 60s do gunicorn → conexão nova por query no banco-mana remoto → resolvido com pool (`db.py`, 2026-08). Sempre devolver conexão com `_put_conn` (vazar congela o app; devolver com autocommit ligado contamina a próxima transação).
- Primeira query depois de ocioso morre com "server closed the connection" → Railway derruba conexão ociosa → keepalives do pool, não remover.
- WhatsApp não chega e não dá erro → (a) `X-API-Key` ausente/diferente do `WEBHOOK_SECRET` do hub = 401; (b) payload sem `classe`/`idempotency_key`/`agente` = hub aceita e não envia → ver contrato abaixo.
- Alerta perdido sem reenvio → falha no envio ao hub NÃO impede gravar o `pedido_estado`; fica só `enviado_ok=false` no `alerta_log` (aba Log de alertas). Invariante: ciclo repetido sem mudança = zero mensagem de pedido (só o heartbeat do cron); mensagem repetida = `pedido_estado` não foi gravado (erro de banco depois do envio).
- Bot respondendo a si mesmo → falta filtro `fromMe` (anti-loop crítico).
- Bot para de responder no grupo depois de ~20 perguntas → rate limit de 20 req/h por IP no `/webhook`, e todo tráfego vem do IP do agente-router → ajustar `_RATE_MAX_REQ` se virar problema.
- NLP falando de pedido que não existe mais → com lake vazio o NLP cai no `pedido_estado` (inclui fantasmas) → popular o lake.
- Smoke test do README via curl (`{"mensagem": ...}` sem `isGroup`/`phone`) responde no grupo REAL (destino cai em `MULTIPLICACAO_GRUPO_ID`) → testar ciente disso.
- `/health` não faz login no SA (só confere env): login real travava o health 5–30s e falhava por DNS no boot. Só o banco é crítico (503); SA/WhatsApp viram `warnings`.

## Contratos com sistemas externos
- **Simple Agro**: login AdonisJS (XSRF + Origin/Referer do painel tenant + Bearer); `GET /api/orders` filtrado por safra, grupo de produto Soja e `deleted=false`; filtro de `uso_semente` feito no cliente, normalizado (maiúsculo, sem acento). Safra/grupo vêm de `SA_SAFRA_ID`/`SA_GRUPO_ID` (trocar na virada de safra).
- **Hub agente-whatsapp** (porta única, ADR 2026-06-13): `POST /send-whatsapp` com `X-API-Key` = `WEBHOOK_SECRET` do hub; payload obriga `classe` + `idempotency_key` (uuid4 POR REQUISIÇÃO — dedup por conteúdo não serve, alerta legítimo repete texto) + `agente`. Resposta 200 `sucesso` (síncrono) ou 202 `enfileirado` (outbox: conta como sucesso; grava `outbox:<key>` no lugar do zaapi_id). Proibido Z-API direto.
- **agente-router → `/webhook`**: payload RAW Z-API (`text` é dict, texto em `text.message`; `phone` = id do grupo quando `isGroup`). Auth: `Authorization: Bearer` (padrão do router, `MULTIPLICACAO_BOT_SECRET` lá = `ROUTER_SHARED_SECRET` aqui), `X-Router-Secret` (legado) ou `?secret=` (debug). Conteúdo inválido/erro responde 200 `{ok:true, motivo}` (Z-API quer ACK rápido); só secret errado (401) e rate limit (429) fogem disso. Fora de grupo responde no DM do remetente.
- **mana-llm-gateway**: com `LLM_GATEWAY_URL` e `LLM_GATEWAY_KEY` usa o alias `LLM_MODEL` (padrão `mana-juridico`); faltando UMA das duas, cai no Anthropic direto (`CLAUDE_MODEL`) SEM erro — custo some do cockpit. O snapshot vai ao prompt cortado (200 pedidos, 20 itens).
- **banco-mana**: escreve só no schema `multiplicacao`.

## Como testar e subir
- Não há testes automatizados; o CI só compila os `.py` (e rodaria `test_*.py` se existissem).
- Deploy = `git push` na `main` → Railway (Procfile, gunicorn 1 worker, timeout 60). Depois: `/health` com `ok: true`, log de boot mostrando os jobs `ingest_*` e `verificar_*` agendados.
- Migrations: `POST /admin/migrate?token=CRON_TOKEN` aplica todos os `migrations/*.sql` em ordem (idempotente).
- Bootstrap de base nova: 1ª rodada com `SILENT_BACKFILL=true` (popula sem mandar), validar, trocar para `false` e redeploy.
- Operação: botão do painel = ingestão; `/cron/verificar?token=` = ciclo de alerta manual (lê o lake, não o SA). Painel e `/api/*` por `?senha=`.
- Skill antiga registrava `CRON_HORARIOS` no Railway com 09h (e não 08h) — valor de ambiente, conferir a variável antes de mexer.

## Pendências conhecidas
- `get_orders` usa `limit=-1` sem paginar — a API do SA trunca/mente nesse modo; o teste de truncamento foi num pedido de 1 item, não conclusivo. Paginar.
- Migrar o `sa_client` inline para o SDK mana-simpleagro; corrigir no SDK o vocabulário de `status_erp` (`'Aprovado'` inexistente).
- Expor TSI no resumo do item para entrar no diff (com guarda de semeadura).
- Prompt do NLP lista status `aprovado`/`recusado`, que não aparecem na sonda (real: Reprovado) — alinhar.
- "Atualizado:" da mensagem de mudança usa `datetime.now()` sem fuso (container em UTC → hora 3h adiantada); o heartbeat já usa BRT fixo.
- Resposta do `/webhook` sai com `classe="transacional"` (fila) embora seja conversa — avaliar `conversacional` conforme o padrão do hub.
- Filtros opcionais `EXCLUIR_STATUS` e `FILTRO_TIPO_PGTO` (se o ruído incomodar); `origem` no `ultimo_run` do `/health`; runbook de troubleshooting.
- Triagem do drift "agente-financeiro-sa omite multiplicação" (`ManaVault/00-Inbox/drift-agente-financeiro-sa-omite-multiplicacao.md`).
- Housekeeping: README e `.env.example` defasados (sem lake, gateway, pool, `CRON_INGEST_HORARIOS`); README/skill antiga citam `railway.json`, que não existe no repo.

## Para ir além
- Não há CLAUDE.md no repo. Nota canônica: `ManaVault/06-Agentes-e-Skills/agente-bot-multiplicacao.md` (ler antes; depois de mudar, atualizar `ultima-revisao` e seções afetadas; decisão arquitetural → ADR em `08-Decisoes/`).
- ADRs: `2026-05-12-novo-agente-bot-multiplicacao`, `2026-05-02-caminho-A-padrao-migracao`, data lake 2026-07-29 (citado na migration 002), porta única WhatsApp 2026-06-13.
- O porquê detalhado está nas docstrings de `agente_bot_multiplicacao.py`, `sa_client.extrair_resumo_pedido`, `whatsapp_client.py` e `db.py`.
