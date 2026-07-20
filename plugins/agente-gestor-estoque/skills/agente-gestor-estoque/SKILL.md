---
name: agente-gestor-estoque
description: Bot WhatsApp N3 da Sementes Maná LTDA que alerta a comercialização de estoque por cultivar. Lê o % de comercialização de cada cultivar do agente-estoque (/api/estoque), classifica em faixas (encalhado/avançado/crítico/ruptura) e alerta o grupo Comercial Estoque e DM via agente-whatsapp; responde inbound por texto e áudio via agente-router. Respostas determinísticas (Harness/zero-LLM): nome de variedade → PDF da posição; resumo/resumo maior/resumo menor → PDF de todas as variedades por estoque; saldo/saldo maior/saldo menor → mesmo PDF ordenado por saldo; painel/painel N → infográfico PNG Painel de Vendas (logo, KPIs, Top 10 por maior saldo, donut) como imagem inline via /send-image. Faixas e destinatários no painel-config; idempotência e allowlist no DM. Use SEMPRE no agente-gestor-estoque: faixas, ruptura, encalhado, avançado, crítico, allowlist, fan-out, painel-config, NLP inbound, painel, painel_vendas, send-image, Pillow, top 10 saldo, saldo maior/menor, schema gestor_estoque, grupo Comercial Estoque.
---

# Agente Gestor de Estoque — Sementes Maná LTDA

Bot WhatsApp N3 (do Xayer) que monitora o **% de comercialização por cultivar** lido do
[[agente-estoque]] (do Dayan) e alerta risco de **ruptura** (muito vendido, perto de esgotar)
ou **encalhe** (pouca saída). Espelha o `agente-gestor-comercial`. ADR fundador:
`ManaVault/08-Decisoes/2026-06-07-novo-agente-gestor-estoque.md`.

## Localização do código

- **Repo:** `Sementesmana/agente-gestor-estoque` (GitHub, branch `main`)
- **Clone local:** `C:\Users\Sementes Mana\Desktop\ORQUESTRADOR\agente-gestor-estoque\`
- **Railway:** project `agente-gestor-estoque` (production)
- **URL:** https://agente-gestor-estoque-production.up.railway.app
- **Banco:** banco-mana compartilhado, schema `gestor_estoque` (NÃO tem Postgres anexo próprio)

## Regra de alerta (faixas do % de comercialização — editáveis no /painel-config)

| Faixa | % | Status | Ação |
|---|---|---|---|
| 🟠 Encalhado | `< 30` | ENCALHADO | Promoção imediata |
| — | `30–80` | saudável (sem alerta) | — |
| 🟡 Avançado | `80 ≤ x < 95` | AVANÇADO | Possibilidade de ruptura |
| 🔴 Crítico | `≥ 95` | CRÍTICO | Interromper vendas (`> 100` = ruptura consumada) |

## Métrica (idêntica ao dashboard de estoque)

```
disponivel    = bag + compra_bag − qualidade_bag
% comercializ = qtd_bag / disponivel × 100   (se disponivel ≤ 0 e qtd_bag > 0 → 100)
saldo         = disponivel − qtd_bag
```

⚠️ O `/api/estoque` NÃO devolve o % pronto (é calculado no JS do dashboard). O agente
replica a fórmula em `app/integrations/estoque_api.calcular_pct`. Se o agente-estoque um dia
expuser `pct_comercializado`/`disponivel_bag` no JSON, o cliente usa direto.

## Estrutura

```
agente-gestor-estoque/
├── app/
│   ├── config.py            ← env fail-fast + LGPD header + mascarar_tel
│   ├── main.py              ← Flask, rotas, Flask-Limiter, cron.iniciar()
│   ├── auth/bearer.py       ← Bearer / senha painel / router-secret
│   ├── models/db.py         ← pool PG, search_path por schema, run_migrations ({{SCHEMA}})
│   ├── integrations/        ← estoque_api (fonte única), whatsapp (+enviar_documento/enviar_imagem), claude
│   ├── services/            ← classificador (faixas), faixas (config), reconciliador
│   │                          (state machine), relatorio, destinatarios, agendamentos,
│   │                          orchestrator, pdf_variedade (PDF posição + resumo, reportlab),
│   │                          painel_vendas (PNG Painel de Vendas Top 10, Pillow)
│   └── workers/             ← cron (APScheduler editável), webhook_router (NLP inbound + PDF/PNG)
├── migrations/              ← 001_init.sql + 002_breakdown_colunas.sql
├── templates/               ← painel.html + painel-config.html (Alpine.js)
├── static/css/mana.css · static/fonts/ (Poppins+DejaVuSerif) · static/img/logo maná.png
└── tests/test_classificador.py  ← 12 testes determinísticos
```

## Pipeline

```
CRON (editável) → GET /api/estoque → classifica faixa → reconcilia state machine PG
   → relatório (Claude Haiku + fallback) → agente-whatsapp (grupo + fan-out DM) → snapshot
```

State machine (tabela `alertas`, chave `nome_norm`): NOVO / MUDANÇA de faixa (SUPERSEDED+novo) /
PERSISTENTE / RESOLVIDO (voltou saudável). Idempotência: UNIQUE parcial `(nome_norm) WHERE status='ABERTO'` + advisory lock.

## Endpoints

- `GET /health`, `GET /health/deep`
- `POST /executar-analise` (Bearer) — body `{usar_claude, enviar_whatsapp}`
- `POST /executar-fan-out?dry_run=1` (Bearer)
- `GET /alertas` (Bearer), `POST /notificar-grupo` (Bearer)
- `GET /painel?senha=`, `GET /painel-config?senha=`
- `GET|POST /api/faixas` (senha) · `GET|POST|PUT|DELETE /api/destinatarios[/<id>]` + `/<id>/smoke-test` (senha)
- `GET|POST|PUT|DELETE /api/agendamentos[/<id>]` (senha)
- `POST /webhook` (X-Router-Secret ou Bearer) — inbound do router

## Inbound (perguntas — texto e áudio)

- **Grupo "Comercial Estoque"** (`120363409759904989-group`): qualquer membro pergunta. Sem allowlist.
- **DM**: keyword `estoque` no agente-router → relay + sticky 30min. Só números **cadastrados e ativos
  em Destinatários** consultam (allowlist, padrão PA); não cadastrado recebe aviso. "estoque" puro → menu.
- **Comandos:** `painel` / `painel N` (imagem PNG do Painel de Vendas — Top 10 saldo), `resumo` / `resumo maior` / `resumo menor` (PDF da tabela por **estoque**), `saldo` / `saldo maior` / `saldo menor` (mesma tabela PDF ordenada por **saldo**), `ruptura`/`crítico`, `avançado`, `encalhado`, ou nome de variedade ("76KA72", "saldo do NEO791" → PDF da posição).
- **Áudio:** o agente-router transcreve via Whisper antes de rotear — funciona de graça.
- NLP: atalho determinístico (akita: determinístico antes do LLM) + fallback Claude Haiku.

## Resposta em PDF (Harness Engineering — zero LLM)

Espelha o `agente-gestor-comercial` (`pdf_ocorrencia.py`). Todo o fluxo é **determinístico**
(código no comando; Claude só como fallback de intent): detecção do nome via `_match_variedade`
(bate o texto contra `nome_norm` do `/api/estoque`, cache 5 min), **re-fetch fresco** na hora de
gerar (tempo real, igual ao botão Atualizar do painel), render reportlab puro, envio pela **porta
única** `/send-document` do agente-whatsapp (`whatsapp.enviar_documento`). Identidade Maná verde/ouro.

- **Nome de variedade → `gerar_pdf_variedade`** (`app/services/pdf_variedade.py`): header, faixa/RUPTURA,
  composição (Produzido + Compra − Reprovação − Venda = Saldo), % e **tabela de pedidos** (drill-down).
- **`resumo` → `gerar_pdf_resumo`**: tabela "Detalhamento por Cultivar" (Estoque · Compra · Qualidade ·
  Qtd Pedida · Saldo · % Pedido), sem drill-down, numa página.
  - **Ordenação (`_ordem_resumo` + `_criterio_resumo`):** `criterio` = `estoque` (default) ou `saldo`.
    `estoque` → chave PRIMÁRIA estoque (`maior` desc / `menor` asc), desempate **saldo mais negativo primeiro**, nome.
    `saldo` (comandos `saldo`/`saldo maior`/`saldo menor`) → chave PRIMÁRIA saldo (`maior` desc / `menor` asc), desempate estoque ↓, nome.
  - **Filtro:** remove cultivares 100% zerados (estoque, compra, qualidade, venda e saldo = 0).
- **Ruptura (nos 2 PDFs):** `venda > disponível` (saldo < 0) OU pct > 100 — igual ao painel.
- Handlers: `_responder_pdf_variedade`, `_responder_pdf_resumo` em `app/workers/webhook_router.py`.
  Fallback pra texto (`_resp_cultivar`/`_resp_resumo`) se geração/envio falhar. Dep: `reportlab`.

## Resposta em IMAGEM — comando `painel` (Harness Engineering — zero LLM, desde 2026-06-22)

Comando **`painel`** (ou `painel N`, N=3..20, default 10) gera o **PAINEL DE VENDAS** — um
infográfico **PNG** que espelha o painel oficial Maná. Determinístico (Pillow puro, **sem
dependência de sistema no Railway** — mesmo princípio do reportlab; fontes embutidas).
Re-fetch **fresco** do `/api/estoque` na hora, render, envio como **IMAGEM inline** (com
preview no chat) pela **nova porta `/send-image`** do [[agente-whatsapp]]
(`whatsapp.enviar_imagem`).

- **Gerador:** `app/services/painel_vendas.gerar_png_painel(itens, top_n=10, safra, foco_acao)`.
- **Conteúdo:** cabeçalho com **logo oficial** (`static/img/logo maná.png`), 5 KPIs (Estoque/
  disponível, Vendido, Saldo, Comercialização %, nº com saldo negativo), ranking **Top 10 por
  MAIOR saldo disponível** com **donut** de %, nota de concentração e faixa institucional.
- **Métrica:** idêntica ao dashboard (estoque = `bag+compra−qualidade`; comercialização = `qtd/disponível`).
- **Fontes:** `static/fonts/` (Poppins + DejaVuSerif), embutidas no repo.
- **Logo:** loader tolerante (qualquer arquivo `logo*` em `static/img/`); ausência/erro →
  desenho vetorial dos anéis (fallback, **nunca quebra** o painel).
- **Handler:** `_responder_painel` + intent `PAINEL` + `_top_n` em `app/workers/webhook_router.py`.
  **Fallback gracioso:** se a imagem falhar → PDF-resumo → texto. Dep: `Pillow`.

## Schema PostgreSQL (`gestor_estoque` no banco-mana)

`config` (faixas/labels, linha única) · `alertas` (state machine) · `notificacoes` (auditoria) ·
`snapshots` (agregado) · `destinatarios` (fan-out DM + allowlist) · `agendamentos` (cron) · `cache` (NLP).

## Variáveis de ambiente

Obrigatórias: `BANCO_MANA_URL`, `ANTHROPIC_API_KEY`, `WHATSAPP_URL`, `WHATSAPP_API_KEY`,
`GRUPO_GESTOR_ESTOQUE_ID` (=`120363409759904989-group`), `BEARER_TOKEN`.
Opcionais: `ESTOQUE_API_URL`, `ESTOQUE_API_TOKEN`, `ROUTER_SHARED_SECRET`, `PAINEL_SENHA`,
`DB_SCHEMA` (default gestor_estoque), `CLAUDE_MODEL`, `FAIXA_ENCALHADO_MAX/AVANCADO_MIN/CRITICO_MIN`,
`THROTTLE_DM_S`, `MAX_DMS_POR_EXECUCAO`, `TZ`.

Router (agente-router): `ESTOQUE_GRUPO_IDS`, `ESTOQUE_BOT_URL`, `ESTOQUE_BOT_SECRET`
(=`ROUTER_SHARED_SECRET` do agente). Slot serve grupo E keyword DM "estoque".

## Integrações

- **Upstream:** [[agente-estoque]] `/api/estoque` (fonte única — não re-implementa Simple Agro), [[agente-router]] inbound.
- **Downstream:** [[agente-whatsapp]] `/send-whatsapp` (texto), `/send-document` (PDF), `/send-image` (PNG painel — desde 2026-06-22), banco-mana.

## Deploy

`git push origin main` → Railway auto-deploy (~2min). Migrations rodam idempotentes no startup.
Crivos akita aplicados (Bearer, rate-limit, fail-fast, fallback, idempotência, logs mascarados, LGPD).

## Como modificar

- **Mudar faixa default:** env `FAIXA_*` ou (em runtime) `/painel-config` aba Faixas → tabela `config`.
- **Adicionar comando inbound:** `app/workers/webhook_router.py` — `_intent_deterministico` (atalho) + handler `_resp_*`.
- **Mudar layout/colunas do PDF:** `app/services/pdf_variedade.py` (`gerar_pdf_variedade` / `gerar_pdf_resumo`).
- **Mudar layout/KPIs/cores do painel PNG:** `app/services/painel_vendas.py` (`gerar_png_painel`). Trocar o logo: substituir `static/img/logo maná.png` (qualquer `logo*` serve). Texto FOCO E AÇÃO: parâmetro `foco_acao` em `_responder_painel`.
- **Mudar ordenação do resumo:** `_ordem_resumo` + bloco de sort em `_responder_pdf_resumo`.
- **Mudar texto do relatório:** `app/services/relatorio.py` (`formatar_hardcoded` + prompt Claude).
- **Novo destinatário DM:** `/painel-config` aba Destinatários (também é a allowlist de consulta).

## Notas no ManaVault

- `06-Agentes-e-Skills/agente-gestor-estoque.md` — nota canônica
- `08-Decisoes/2026-06-07-novo-agente-gestor-estoque.md` — ADR fundador
- `00-Inbox/2026-06-07-parecer-agente-gestor-estoque.md` — parecer original
