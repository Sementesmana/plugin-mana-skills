---
name: agente-tms
description: Agente TMS Maná (Sementes Maná) — planejamento de entregas + cotação de frete. Flask workers=1 + PostgreSQL banco-mana schema `tms` (ADR 2026-05-30) + Railway. Lê agendamentos do Simple Agro, painel kanban por data, rota OSRM por estrada com Ponto de Referência obrigatório, caminhão ideal pelos Perfis de Veículo (bags+tara), cotação por DM WhatsApp via agente-whatsapp. Retorno chega via agente-router → /webhook-retorno, casa por últimos-8-dígitos do telefone e calcula SAVING (estimado − retornado) sem precisar deixar painel aberto. Use SEMPRE que trabalhar com agente-tms — endpoints, schema tms, painel HTML, cotação, SAVING, OSRM, caminhão ideal, integração agente-whatsapp/agente-router, CRUD cadastros, polling /api/cotacoes, tolerant tel match. Também quando mencionar: TMS Maná, planejamento entrega, cotação frete, SAVING, faixa km × R$/ton, schema tms, banco-mana, webhook-retorno, /api/enviar-cotacao, transportadora WhatsApp, ponto partida, Em Cotação, BITREM/BITRUCK/RODOTREM/LS.
---

# agente-tms — TMS Maná

> Planejamento de entregas + cotação de frete para a Sementes Maná LTDA.
> Esqueleto criado em 2026-05-25, persistência PostgreSQL em 2026-05-30.

## Quick reference

| Campo | Valor |
|---|---|
| Repo | `Sementesmana/agente-tms` |
| Railway | `agente-tms` (1 replica, workers=1) |
| URL | `https://agente-tms-production.up.railway.app` |
| Painel | `/painel?senha=…` |
| Stack | Python 3.11 + Flask 3.0 + Gunicorn + psycopg2 + Railway |
| Banco | PostgreSQL no `banco-mana`, **schema `tms`** (ADR 2026-05-30) |
| Workers | **1** (store em memória precisa ser cross-request; cron interno não duplica) |
| Local | `ORQUESTRADOR/agente-tms/` |
| Nota canônica | `ManaVault/06-Agentes-e-Skills/agente-tms.md` |

## Estrutura de arquivos

```
agente-tms/
├── app.py                 Flask routes (finas) + auth + rate-limit + /health
├── agente_tms.py          Logica de negocio (SA, WhatsApp, OSRM, persistencia, CRUD cadastros)
├── db.py                  Pool psycopg2 + DDL idempotente + search_path=tms,public
├── templates/painel.html  Painel (copia do mockup tms-mana-mockup.html)
├── requirements.txt       flask, gunicorn, requests, psycopg2-binary
├── Procfile + railway.toml  Start command com --workers 1
├── .env.example
└── README.md
```

## Arquitetura

```
SoftExpert/SA (nao bate direto — sao OUTROS agentes que escrevem)
    │
agente-tms (painel + backend)
    │  GET /api/agendamentos   → Simple Agro orders-scheduling (read)
    │  POST /api/enviar-cotacao ─────────► agente-whatsapp /send-whatsapp ─► Z-API ─► transportadora (DM)
    │  GET /api/cotacoes (polling 8s)                                       │
    │  CRUD /api/cad/* (cadastros)                                          │
    │                                                                       ▼
    │            transportadora responde no WhatsApp → Z-API → agente-router
    │            → relay_tms → POST /webhook-retorno (X-Router-Secret)
    │            → parse_valor + tolerant tel match (ultimos 8 digitos)
    │            → grava retorno + retorno_em → SAVING aparece no painel
    │
    └─ PostgreSQL (banco-mana, schema tms) — persiste cadastros, cotacoes, retornos
```

## Schema `tms` no banco-mana

| Tabela | Função |
|---|---|
| `veiculos` | Perfis (LS/BITREM/RODOTREM/BITRUCK): nome, capacidade_bags, tara_ton, bloqueado |
| `status_agendamento` | Status custom do TMS (Em planejamento, Aguardando motorista, etc.) |
| `transportadoras` | Fornecedoras de frete: nome, cnpj, contato, telefone |
| `transportadora_tarifas` | Faixas km × R$/ton por fornecedor (km_de, km_ate, valor_ton) |
| `pontos_referencia` | Início obrigatório de rota: nome + latitude + longitude |
| `cotacoes` | Pacote de cotação: veículo, partida, stops (JSONB), km, data_entrega, gmaps, idempotency_key |
| `cotacao_transportadora` | Uma linha por transportadora marcada na cotação: estimado, enviado, retorno, retorno_em, erro |

DDL idempotente em `db.py::_DDL` (`CREATE … IF NOT EXISTS`). `init_db()` roda no startup. `init_seed()` popula veículos/status/transportadora exemplo (com 42 faixas)/ponto exemplo **só se as tabelas estiverem vazias**.

## Endpoints

### Saúde / painel
| Método | Rota | Auth | Função |
|---|---|---|---|
| GET | `/health` | — | status + deps SA/whatsapp/OSRM + status DB |
| GET | `/painel?senha=` | PAINEL_SENHA | painel HTML (servido pelo Flask via templates/painel.html) |
| GET | `/` | — | info root |

### Operação
| Método | Rota | Auth | Função |
|---|---|---|---|
| GET | `/api/agendamentos?de=&ate=&frete=` | PAINEL_SENHA | agendamentos do SA (orders-scheduling) por safra + range |
| POST | `/api/enviar-cotacao` | PAINEL_SENHA | dispara cotação WhatsApp (idempotente por `Idempotency-Key`); persiste em `tms.cotacoes` |
| GET | `/api/cotacoes` | PAINEL_SENHA | lista cotações + transportadoras (JSON aggregation no SQL); painel faz polling 8s |
| POST | `/webhook-retorno` | ROUTER_SECRET | recebe relay do router; parse + match + grava retorno |

### Cadastros (CRUD genérico)
| Recurso | Endpoints |
|---|---|
| Veículos | `GET POST /api/cad/veiculos`, `PUT DELETE /api/cad/veiculos/<id>` |
| Status | `GET POST /api/cad/status`, `PUT DELETE /api/cad/status/<id>` |
| Transportadoras | `GET POST /api/cad/transportadoras`, `PUT DELETE /api/cad/transportadoras/<id>` |
| Tarifas (sob transportadora) | `GET POST /api/cad/transportadoras/<transp_id>/tarifas`, `PUT DELETE /api/cad/tarifas/<id>` |
| Pontos de referência | `GET POST /api/cad/pontos`, `PUT DELETE /api/cad/pontos/<id>` |

Padrão: `GET` retorna `{items: [...]}`. `POST` retorna o registro criado (com id). `PUT` aceita campos parciais (só atualiza o que vier no body) e retorna o registro. `DELETE` retorna `{ok: true}`.

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `PAINEL_SENHA` | sim | auth painel/api (default `mana2026`) |
| `AGENTE_WHATSAPP_URL` | sim | URL do hub outbound (`agente-whatsapp-production-eac3.up.railway.app`) |
| `AGENTE_WHATSAPP_API_KEY` | sim | header `X-API-Key` — **deve ser o `WEBHOOK_SECRET` do agente-whatsapp** |
| `ROUTER_SECRET` | sim | valida o relay do agente-router no `/webhook-retorno` (header `X-Router-Secret`); **mesmo valor** do `TMS_BOT_SECRET` no router |
| `SA_BASE_URL` | sim | `https://sementesmana.api.simpleagro.com.br:3333` |
| `SA_USERNAME` / `SA_PASSWORD` | sim | mesma conta de automação dos outros agentes Maná (ver agente-pedidos) |
| `SA_SAFRA_ID` | sim | id da safra (25/26 = `679135f95feb17003584dc27`, 26/27 = `69a5d85cae03f50036ee2531`) |
| `SA_GRUPO_ID` | sim | grupo soja `610a8b743829fd00385c48c9` |
| `BANCO_MANA_URL` | sim (opcional pra dev) | URL pública do banco-mana. Ausente = modo memória |
| `OSRM_URL` | opcional | default `router.project-osrm.org` |
| `TMS_STRICT_ENV` | opcional | `1` em produção: aborta se faltar variável obrigatória |
| `RATE_MAX_POR_MIN` | opcional | rate limit por IP, default 60 |

## Integrações

- **[agente-whatsapp]** — *outbound*: `POST /send-whatsapp` com `{telefone, mensagem}`, header `X-API-Key`. Disparado em `_enviar_whatsapp()` dentro de `enviar_cotacao()`. Falha por transportadora não derruba a cotação (graceful degradation, `erro: "falha_envio"`).
- **[agente-router]** — *inbound*: a partir do **ADR 2026-05-25-router-relay-tms-retorno-cotacao** o router faz claim por número (chama `/webhook-retorno`; se TMS retorna `status: ok` intercepta, senão segue fluxo normal pros 3 outros bots — PA/Comercial/Agronomo). No router as envs são `TMS_BOT_URL` + `TMS_BOT_SECRET`. **Aditivo e seguro:** sem `TMS_BOT_URL` o router não muda nada.
- **Simple Agro** — login `/api/auth/login` (login, senha + Origin/Referer); orders-scheduling com `Authorization` direto (o token do SA **já vem com `Bearer ` embutido**, NÃO duplicar). Mesma conta de automação dos outros agentes.
- **OSRM** — `/trip/v1/driving/{lon,lat;...}?source=first&roundtrip=false&overview=full&geometries=geojson` (usado pelo painel direto, JS); backend tem helper `osrm_trip(coords)` com fallback gracioso.
- **banco-mana** — schema dedicado `tms` (ADR 2026-05-30). `db.get_conn()` faz `SET search_path TO tms, public` em cada conexão.

## Padrões/cuidados importantes

### Casamento de telefone (tolerant match)
Critério: **últimos 8 dígitos**. Função `_tel_match(a, b)` em `agente_tms.py`. Tolera variações `55`/DDD/9º dígito que o Z-API às vezes entrega diferente do cadastrado. No SQL é `RIGHT(REGEXP_REPLACE(telefone, '\D', '', 'g'), 8)`. Histórico: o match exato falhou em produção (a transportadora cadastrada como `5562994331331` recebeu reply como `556294331331` sem o 9 → quebrava).

### Workers=1
**Crítico.** O `Procfile` e `railway.toml` rodam com `--workers 1`. Não aumentar sem antes garantir que tudo que importa está no banco (idempotência, sem cache cross-request). Com `workers=2` em produção o webhook caía num worker e a cotação no outro → match falhava.

### Idempotência
`enviar_cotacao()` aceita `Idempotency-Key` (header ou body). Se igual ao de uma cotação anterior, retorna `{status: "duplicado", id}` sem reenviar. No banco: UNIQUE em `cotacoes.idempotency_key`. Front-end usa `cot-<timestamp>-<i>` como key.

### Modo memória (fallback)
Se `BANCO_MANA_URL` ausente, o agente boota em modo memória com warning — útil pra dev local. `_use_db()` retorna False, e enviar_cotacao/processar_retorno_whatsapp/listar_cotacoes caem no caminho in-memory. **Não usar em produção.**

### Seed inicial
`init_seed()` popula com os exemplos do mockup **apenas se as tabelas estiverem vazias**. Idempotente em redeploys. Inclui: 4 veículos (LS 40/32, BITREM 45/38, RODOTREM 60/50, BITRUCK 20/20), 2 statuses, 1 transportadora exemplo + 42 faixas (0–50 km a 2051–2100 km), 1 ponto de referência.

### Auth no `/webhook-retorno`
Header **`X-Router-Secret`** OU query param `?token=`. Valida contra `ROUTER_SECRET` env. Se falhar, retorna 401. **NÃO** usa PAINEL_SENHA (router é origem confiável, não o usuário).

### SA 401 intermitente (pendente)
Em produção o login SA retorna 401 esporadicamente — token expira e o re-login dá Bad Request. Workaround atual: o painel cai pro fallback de exemplo. Investigação pendente.

## Painel (mockup HTML)

Fonte de verdade: `ORQUESTRADOR/tms-mana-mockup.html`. Cópia servida: `agente-tms/templates/painel.html`.

**Gotcha de cópia:** o mount do sandbox às vezes serve leitura truncada de arquivos grandes recém-editados. **Copiar via Git Bash do Xayer** (FS real do Windows), nunca `cp` no sandbox. Comando padrão:

```bash
cp "/c/Users/Sementes Mana/Desktop/ORQUESTRADOR/tms-mana-mockup.html" templates/painel.html
grep -c "</html>" templates/painel.html  # tem que dar 1
```

**Estado client-side relevante** (vive no JS do painel):
- `dados` — agendamentos por lane de data (carregados de `/api/agendamentos` com fallback p/ exemplo)
- `cotacoes` — cotações abertas no painel (carregadas de `/api/cotacoes` no boot via `carregarCotacoes()`)
- `veiculos`, `statuses`, `fornecedores` (com tarifas inline), `pontos` — cadastros carregados de `/api/cad/*` no boot

**Polling:** `setInterval(pollRetornos, 8000)` — atualiza retornos das cotações ativas (com `backendId`) sem sobrescrever valores digitados à mão.

**Helpers JS:**
- `_normTel(t)` — strip não-dígitos
- `_DBMAP` — mapeia campos JS curtos (`cap`, `ton`, `lat`, `lng`, `bloq`, `de`, `ate`, `valor`) para nomes do banco (`capacidade_bags`, `tara_ton`, etc.)
- `_getCad/_postCad/_putCad/_delCad` — wrappers fetch pra `/api/cad/*` com senha embutida

## Fluxo da cotação E2E (referência)

1. Usuário abre painel `/painel?senha=…`. Painel carrega cadastros + cotações pendentes do banco.
2. Vai em **Programação de Entrega**, seleciona N cards (com shift pra range), escolhe Ponto de partida, clica **Gerar Rota**.
3. Front chama OSRM trip; mostra mapa Leaflet + caminhão ideal (menor capacidade que cabe a carga total).
4. Usuário define data de entrega, clica **Enviar para cotação**. Cards saem do board e viram card em **Em Cotação** (client-side primeiro).
5. No card, marca N transportadoras (estimado calculado por `tarifa(km) × tara`) e clica **Enviar cotação**.
6. POST `/api/enviar-cotacao` → backend persiste em `cotacoes` + `cotacao_transportadora`, envia DM via `agente-whatsapp` por transportadora.
7. Transportadora responde no WhatsApp → Z-API → `agente-router/webhook` → `relay_tms` chama `agente-tms/webhook-retorno` → casa por últimos-8-dígitos → grava `retorno` + `retorno_em`.
8. Painel (aberto ou reaberto depois) chama `/api/cotacoes` no boot e a cada 8s → mostra **Retorno (API)** e calcula **SAVING** = estimado − retornado (verde se positivo, vermelho se negativo).

## ADRs relacionadas (imutáveis)

- **`08-Decisoes/2026-05-25-router-relay-tms-retorno-cotacao`** — claim pattern no router (aditivo). Sem `TMS_BOT_URL` é no-op.
- **`08-Decisoes/2026-05-30-schema-por-agente-banco-mana`** — schema-por-agente como padrão pós-incidente do Prisma.

## Pendências em aberto

- **SA 401 intermitente** — investigar cache/re-login do token no `_sa_login()`.
- **Rotacionar segredos** que apareceram em chat durante o setup: `WEBHOOK_SECRET` (agente-whatsapp) e `ROUTER_SECRET`/`TMS_BOT_SECRET` (`f789b8d2…`).
- **Política de backup** do schema `tms` no banco-mana (nenhum agente Maná tem hoje — ADR à parte).

## Comandos úteis (Git Bash do Xayer)

```bash
# Atualizar painel servido apos editar o mockup
cd "/c/Users/Sementes Mana/Desktop/ORQUESTRADOR/agente-tms"
cp "/c/Users/Sementes Mana/Desktop/ORQUESTRADOR/tms-mana-mockup.html" templates/painel.html
grep -c "</html>" templates/painel.html  # 1 = ok

# Deploy padrao Mana
git add . && git commit -m "..." && git push   # Railway auto-deploya em ~2 min

# Validar producao
curl -s "https://agente-tms-production.up.railway.app/health" | python -m json.tool
curl -s "https://agente-tms-production.up.railway.app/api/cotacoes?senha=mana2026" | python -m json.tool
```

## Quando esta skill NÃO se aplica

- Cadastro de imóveis CAR → `agente-agro`.
- Cotação/orçamento de **sementes** (não frete) → `agente-precificacao` (Maná Price).
- Cobrança/parcelas SA → `agente-financeiro-sa`.
- Envio de mensagens WhatsApp por outros motivos (notificação SE, etc.) → `agente-whatsapp` direto.
- Roteamento inbound de outros bots → `agente-router`.
                                                                                                                                                                                                                                                                                                                                                                                   