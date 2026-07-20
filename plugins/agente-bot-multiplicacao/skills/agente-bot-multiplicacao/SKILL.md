---
name: agente-bot-multiplicacao
description: >
  Bot WhatsApp da Sementes Maná LTDA para pedidos do Simple Agro com Uso da Semente =
  MULTIPLICAÇÃO. Flask + APScheduler no Railway, cron 08/12/16 BRT, deduplica por
  pedido e status, envia alertas NOVO e MUDANCA_STATUS via agente-whatsapp ao grupo
  Trigger pedidos e responde consultas via agente-router e Claude NLP. Use SEMPRE
  que precisar trabalhar com o agente-bot-multiplicacao — modificar cron, ajustar
  filtros, depurar valores SA, alterar dedup, NLP inbound, painel, parse Z-API, ou
  entender a arquitetura. Também quando mencionar: bot multiplicação, grupo Trigger
  pedidos, MULTIPLICAÇÃO, frete CIF rateado, parcelas canônicas, APScheduler, payload
  Z-API raw, fromMe filter, bag (não sacas), pedido 260000040022, agente-router
  Bearer, agente-whatsapp X-API-Key.
---

# Agente Bot Multiplicação — Sementes Maná

Bot WhatsApp da Sementes Maná que monitora pedidos do Simple Agro com `Uso da Semente = MULTIPLICAÇÃO` na safra ativa, alerta o grupo "Trigger pedidos" em horários fixos (08/12/16 BRT) e responde consultas conversacionais.

## Infraestrutura

| Item | Valor |
|---|---|
| URL produção | `https://agente-bot-multiplicacao-production.up.railway.app` |
| Repositório | `github.com/Sementesmana/agente-bot-multiplicacao` (isolado, Caminho A) |
| Projeto Railway | `Agente-bot-multiplicacao-SM` |
| Service Railway | `agente-bot-multiplicacao` |
| Root Directory | **VAZIO** (código na raiz) |
| Branch | `main` |
| Workers | **1** (constraint SA: 1 sessão por usuário) |
| Stack | Python 3.11 + Flask + Gunicorn + APScheduler + PostgreSQL + Claude |

## Estrutura de arquivos

```
agente-bot-multiplicacao/
├── app.py                       Flask + APScheduler + 7 rotas
├── agente_bot_multiplicacao.py  Lógica de negócio (job, dedup, formatadores)
├── sa_client.py                 Cliente Simple Agro
├── whatsapp_client.py           Wrapper /send-whatsapp do agente-whatsapp
├── claude_nlp.py                NLP inbound (system prompt + chamada Claude)
├── db.py                        Acesso banco-mana (schema multiplicacao)
├── templates/painel.html        Painel Maná verde+ouro com 2 abas
├── migrations/001_init.sql      DDL idempotente (3 tabelas + índices)
├── requirements.txt             Deps fixadas
├── Procfile                     gunicorn workers=1
├── railway.json                 healthcheck /health
├── .env.example                 Todas envs documentadas
└── README.md
```

## Variáveis de ambiente (Railway)

| Variável | Descrição | Default |
|---|---|---|
| `SA_BASE_URL` | API Simple Agro | `https://sementesmana.api.simpleagro.com.br:3333` |
| `SA_USERNAME` / `SA_PASSWORD` | credenciais SA | — |
| `SA_SAFRA_ID` | safra ativa | `69a5d85cae03f50036ee2531` |
| `SA_GRUPO_ID` | grupo Soja | `610a8b743829fd00385c48c9` |
| `AGENTE_WHATSAPP_URL` | hub outbound | `https://agente-whatsapp-production-eac3.up.railway.app` |
| `AGENTE_WHATSAPP_API_KEY` | **mesma string** do `WEBHOOK_SECRET` do agente-whatsapp | — |
| `MULTIPLICACAO_GRUPO_ID` | grupo "Trigger pedidos" | `120363409038345631-group` |
| `ROUTER_SHARED_SECRET` | mesma string do `MULTIPLICACAO_BOT_SECRET` do agente-router | — |
| `ANTHROPIC_API_KEY` | NLP inbound | — |
| `CLAUDE_MODEL` | modelo | `claude-opus-4-6` |
| `BANCO_MANA_URL` | URL pública banco-mana | — |
| `PAINEL_SENHA` | auth painel/APIs | `mana2026` |
| `CRON_TOKEN` | auth de `/cron/verificar` e `/admin/migrate` | gerado |
| `CRON_HORARIOS` | triggers cron | `08:00,12:00,16:00` |
| `CRON_TIMEZONE` | TZ | `America/Sao_Paulo` |
| `CRON_DIAS` | dias da semana | `mon,tue,wed,thu,fri,sat,sun` |
| `SILENT_BACKFILL` | popula sem disparar (apenas na 1ª rodada) | `false` |
| `USO_SEMENTE_TARGET` | valor que dispara alerta | `MULTIPLICACAO` |

## Endpoints

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/` | público | info |
| GET | `/health` | público | banco crítico, SA/WA toleráveis (200 se banco OK) |
| GET/POST | `/cron/verificar?token=` | CRON_TOKEN | dispara job manual |
| POST | `/admin/migrate?token=` | CRON_TOKEN | aplica `001_init.sql` idempotente |
| POST | `/webhook` | Bearer / X-Router-Secret / ?secret= | inbound do agente-router |
| GET | `/api/pedidos?senha=` | PAINEL_SENHA | snapshot atual JSON |
| GET | `/api/alertas?senha=` | PAINEL_SENHA | log de disparos |
| GET | `/painel?senha=` | PAINEL_SENHA | painel HTML (2 abas) |

## Schema banco-mana (`multiplicacao`)

```
pedido_estado    → snapshot atual por pedido (PK: id_pedido_sa)
                   campos: status_atual, cliente_nome, valor_total, payload (JSONB com itens), ts_atualizado
alerta_log       → auditoria de cada disparo (tipo NOVO/MUDANCA_STATUS/BACKFILL)
cron_run         → registro de cada execução (origem, ts_inicio, ts_fim, stats)
```

## ⚠️ REGRA CRÍTICA: Cálculo de valor por item (frete CIF rateado)

**NUNCA usar `total_preco_item` direto como valor do item.** Esse campo é LÍQUIDO sem frete. Em pedidos CIF, fica ~3% abaixo do "Total Item" mostrado no espelho impresso do SA.

**Fórmula canônica (regra Maná validada 2026-05-13 contra pedido 260000040022/1):**

```python
# 1. Total do pedido = SOMA DAS PARCELAS (fonte canônica, já inclui frete)
sum_parcelas = sum(p.valor_parcela for p in order.pagamento.parcelas)

# 2. Frete total embutido nas parcelas (subtrai líquidos dos itens)
sum_liquidos = sum(item.total_preco_item for item in order.itens)
frete_total = sum_parcelas - sum_liquidos    # pode ser 0 se sem frete

# 3. Rateio proporcional do frete por item
for item in order.itens:
    proporcao = item.total_preco_item / sum_liquidos
    frete_item = frete_total * proporcao
    valor_item_final = item.total_preco_item + frete_item
```

**Validação:** pedido 260000040022/1, soma de itens = soma de parcelas = "Total Pedido" do espelho = R$ 259.000.

**NÃO usar `preco_frete_tabela_item`** (campo é zero em vários pedidos — mesmo bug documentado no `agente-financeiro-sa`).

## ⚠️ REGRA CRÍTICA: Unidade = bag (NUNCA "sacas")

- Campo `item.quantidade` no SA já vem em **bag**.
- Padrão Maná alinhado com `agente-financeiro-sa` e `agente-pedidos-sa`.
- System prompt do Claude (`claude_nlp.py`) ensina explicitamente: "UNIDADE = bag, NUNCA sacas/sc/scs".
- Template de mensagem outbound: `• {cultivar} — {qtd:g} bag`.

## Lógica de dedup (idempotência)

```
Pedido visto pela primeira vez:
  SILENT_BACKFILL=true  → grava como BACKFILL (sem mensagem)
  SILENT_BACKFILL=false → grava como NOVO + envia mensagem 🌱

Pedido já existe + mesmo status: atualiza payload + ts_atualizado (sem mensagem)
Pedido já existe + status mudou: grava como MUDANCA_STATUS + envia mensagem 🔄
```

Garantia: rodar o cron 100x dispara mensagem zero (idempotente). Caso B (mesmo status) sobrescreve o `payload->itens` no banco com snapshot fresco — útil quando recalcula valor (ex: depois de mudar a fórmula de frete).

## Parse de payload Z-API (inbound)

O agente-router envia o payload RAW da Z-API. Estrutura esperada:

```json
{
  "isGroup": true,
  "fromMe": false,
  "phone": "120363409038345631-group",
  "participantPhone": "5564...",
  "participantName": "Xayer",
  "senderName": "Xayer",
  "text": { "message": "pedidos do hygor" },
  "origem_audio": false
}
```

**Cuidados:**
- `payload.text` é **dict** (não string). Mensagem vem em `text.message`.
- Filtrar `fromMe=true` (anti-loop crítico).
- `payload.phone` é o `grupo_id` quando `isGroup=true`.
- Retornar **200 sempre** (Z-API espera ACK rápido). Erros viram `{ok: true, motivo: "..."}`.

## Auth do `/webhook` (3 formatos aceitos, compat)

```python
def _check_router_secret():
    # 1. Authorization: Bearer <token>   (padrão do agente-router)
    # 2. X-Router-Secret: <token>        (legado)
    # 3. ?secret=<token>                 (debug via browser)
```

O `agente-router` envia `Authorization: Bearer <MULTIPLICACAO_BOT_SECRET>`. O bot espera bater com `ROUTER_SHARED_SECRET`.

## Auth pra falar com `agente-whatsapp`

`POST /send-whatsapp` exige header `X-API-Key: <WEBHOOK_SECRET>` (sem isso retorna 401 silencioso). Config local: env `AGENTE_WHATSAPP_API_KEY` = mesma string do `WEBHOOK_SECRET` do agente-whatsapp.

## Comandos operacionais comuns

```powershell
# Dispara cron manual
curl.exe -X POST "https://agente-bot-multiplicacao-production.up.railway.app/cron/verificar?token=$CRON_TOKEN"

# Roda migrations (idempotente)
curl.exe -X POST "https://agente-bot-multiplicacao-production.up.railway.app/admin/migrate?token=$CRON_TOKEN"

# Lista alertas
curl.exe "https://agente-bot-multiplicacao-production.up.railway.app/api/alertas?senha=mana2026"

# Health
curl.exe "https://agente-bot-multiplicacao-production.up.railway.app/health"
```

## Disciplina vault (OBRIGATÓRIA)

**Antes de modificar:** ler `ManaVault/06-Agentes-e-Skills/agente-bot-multiplicacao.md` (nota canônica com histórico completo e pendências).

**Depois de modificar:**
- Atualizar `ultima-revisao` no frontmatter
- Atualizar seções afetadas (endpoints, vars, integrações)
- Se for decisão arquitetural: criar ADR em `08-Decisoes/`

## Decisões relacionadas

- `ManaVault/08-Decisoes/2026-05-12-novo-agente-bot-multiplicacao.md` — ADR de criação
- `ManaVault/08-Decisoes/2026-05-02-caminho-A-padrao-migracao.md` — código na raiz, Root Directory vazio
- `ManaVault/00-Inbox/drift-agente-financeiro-sa-omite-multiplicacao.md` — drift descoberto

## Integrações com outros agentes

- **agente-router** envia mensagens do grupo → `/webhook` (via Bearer)
- **agente-whatsapp** recebe mensagens → `/send-whatsapp` (via X-API-Key)
- **banco-mana** centraliza schema `multiplicacao`
- **Simple Agro** consulta `/api/orders` (workers=1, re-login em 401)

## Pendências V1.x

1. Filtro opcional `EXCLUIR_STATUS=cancelado,recusado` — se ruído ficar problemático
2. Filtro opcional `FILTRO_TIPO_PGTO` — venda à vista vs prazo
3. Adicionar `origem` (cron/manual) no `ultimo_run` do `/health`
4. Runbook de troubleshooting (401, schema vazio, payload Z-API mudou)
5. Triagem do drift `agente-financeiro-sa` (Inbox)

## Histórico relevante

- 2026-05-12: scaffold V1 + deploy + outbound + inbound em produção
- 2026-05-12: bug `whatsapp_client` sem `X-API-Key` (401 silencioso) → resolvido com env nova
- 2026-05-12: healthcheck tolerante a schema vazio e SA DNS lento
- 2026-05-13: fix valor por item com frete CIF rateado proporcionalmente (regra canônica Maná)
