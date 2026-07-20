---
name: agente-router
description: >
  Despachante central de webhooks Z-API para múltiplos bots WhatsApp — Sementes Maná LTDA.
  Serviço Flask no Railway que recebe todos os webhooks da Z-API, transcreve áudio inbound via
  Whisper (OpenAI) e roteia pra bot correto (agronomo, comercial dual-mode, plano-acao, secretaria,
  pesquisador, multiplicacao, financeiro, estoque) com base em grupos (GRUPO_IDS) e keywords em DM.
  Use esta skill SEMPRE que precisar: adicionar bot/grupo, depurar mensagens não entregues,
  entender fluxo de roteamento, ajustar keywords DM, modificar router.py/app.py, ou verificar por
  que um grupo/DM não foi roteado corretamente.
  Também use quando mencionar: router, webhook Z-API, relay, despachante WhatsApp, roteamento de
  grupos, agente-router, fromMe, isGroup, AGRONOMO_GRUPO_IDS, COMERCIAL_BOT_URL, SECRETARIA_BOT_URL,
  TMS_BOT_URL, Whisper inbound, keyword DM, agronomo curto, comercial curto.
---

# agente-router — Despachante de Webhooks WhatsApp

Serviço Flask no Railway. Recebe TODOS os webhooks Z-API em um único endpoint, transcreve áudio
via Whisper (OpenAI) e despacha pra bot correto com base em (grupo) ou (keyword DM).

## Produção

| Item | Valor |
|------|-------|
| URL Railway | `https://agente-router-production.up.railway.app` |
| Webhook Z-API | `https://agente-router-production.up.railway.app/webhook?token=mana-router-2026` |
| GitHub | `github.com/Sementesmana/agente-router` |
| Health | `https://agente-router-production.up.railway.app/health` |

## Por que existe

Z-API suporta apenas UMA URL no campo "Ao receber". Com múltiplos bots precisamos de um
despachante central. Antes do router, o agente-plano-acao fazia relay manual via `/webhook-incoming`
— não escalava. Hoje o router também centraliza Whisper inbound (todos os bots recebem texto).

## Arquitetura

```
WhatsApp → Z-API → POST /webhook?token=ROUTER_SECRET
                       │
                       ├── Tem audio? → Whisper API (OpenAI) → injeta texto + origem_audio=true
                       │
                       ├── fromMe=True → ignorado (eco)
                       │
                       ├── isGroup=True:
                       │     ├── AGRONOMO_GRUPO_IDS   → agente-agronomo /webhook
                       │     ├── FINANCEIRO_GRUPO_IDS → agente-financeiro-sa /webhook (preparado)
                       │     ├── ESTOQUE_GRUPO_IDS    → agente-estoque /webhook (preparado)
                       │     ├── PESQUISADOR_GRUPO_IDS→ agente-pesquisador-genetica /webhook
                       │     ├── MULTIPLICACAO_GRUPO_IDS → agente-bot-multiplicacao /webhook
                       │     └── não mapeado → ignorado (log)
                       │
                       └── isGroup=False (DM):
                             ├── 1) Tenta TMS /webhook-retorno (transportadora respondendo cotação)
                             │     └── TMS reclamou? entrega lá. Senão segue.
                             ├── 2) Detecta keyword (startswith case-insensitive):
                             │     ├── _KW_PA         → agente-plano-acao /processar-mensagem
                             │     ├── _KW_COMERCIAL  → agente-comercial /webhook (tem dual-mode interno)
                             │     └── _KW_SECRETARIA → agente-secretaria /webhook (se configurado)
                             └── 3) Default → agente-plano-acao
```

## Keywords DM (router.py linhas 66-90)

| Lista | Keywords reconhecidas (startswith, case-insensitive) | Destino |
|---|---|---|
| `_KW_PA` | "agente plano de acao", "agente plano de ação", "agente plano", "plano de acao", "plano de ação" | agente-plano-acao |
| `_KW_COMERCIAL` | "agente precificacao", "agente precificação", "agente comercial", "agente agronomo", "agente agrônomo", **"comercial"**, **"agronomo"**, **"agrônomo"** (curtas desde 2026-05-29) | agente-comercial (dual-mode escolhe modo internamente) |
| `_KW_SECRETARIA` | "secretaria", "secretária", "secretario", "secretário", "agenda", "reunião", "reuniao" | agente-secretaria (se SECRETARIA_BOT_URL setado) |

⚠️ **Importante:** "agronomo" em DM **NÃO vai pro agente-agronomo (Railway próprio)** — vai pro agente-comercial em modo agronomo (dual-mode). O agente-agronomo só dispara em GRUPO via `AGRONOMO_GRUPO_IDS`.

## Modelo de autorização (por bot a jusante)

| Bot | Tem painel próprio? | Modelo |
|---|---|---|
| agente-plano-acao | `/admin` (tabela `pa_colaboradores`) | Cadastro por número + relação líder→liderado |
| agente-comercial | `/admin` + `/api/usuarios` | Cadastro por número (gateia DM tanto modo comercial quanto modo agronomo) |
| agente-secretaria | `/painel-contatos` (com `pode_comandar`) | Cadastro por número |
| **agente-agronomo** | ❌ Nenhum | Estar no grupo do WhatsApp `AGRONOMO_GRUPO_IDS` |

Implicação: bot agronomo "puro" não auditável por painel — gate é membership no grupo do WA.
Quem manda "Agronomo" em DM passa pelo `/admin` do **comercial**.

## Transcrição inbound (Whisper) — desde 2026-05-06

Antes de qualquer roteamento, se payload tem `audio.audioUrl`:

1. Baixa `.ogg` do CDN Z-API em memória (LGPD: nunca toca disco)
2. POST `https://api.openai.com/v1/audio/transcriptions` (`whisper-1`, language `pt`)
3. Injeta texto em `payload.text.message`
4. Seta `payload.origem_audio=true` (bots a jusante usam pra escolher TTS espelho)
5. Limpa `payload.audio` (evita re-detecção)
6. Roteia normal

**Fallback gracioso:** sem `OPENAI_API_KEY` ou falha → `ignorado: audio_nao_transcrito`. Nunca crasha.
**Custo:** ~US$ 0,006/min (~R$ 0,03/min). Áudio típico de 30s ≈ R$ 0,015.

## Estrutura de arquivos

```
agente-router/
├── app.py                     Flask + /webhook + /health + rate limiting + auth ROUTER_SECRET
├── router.py                  Lógica isolada (sem Flask — testável)
├── requirements.txt           flask==3.0.3, gunicorn==22.0.0, requests==2.32.3, flask-limiter==3.7.0
├── railway.toml
├── Procfile
└── .env.example
```

## Endpoints

| Método | Path | Auth | Descrição |
|--------|------|------|-----------|
| `GET`  | `/health` | público | Status + rotas ativas |
| `POST` | `/webhook` | `?token=ROUTER_SECRET` | Recebe webhook Z-API e roteia |

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `ROUTER_SECRET` | Token Z-API webhook |
| `OPENAI_API_KEY` | Whisper inbound. Ausente = áudio ignorado. |
| `AGRONOMO_BOT_URL` + `AGRONOMO_BOT_SECRET` | Relay agente-agronomo |
| `PA_BOT_URL` + `PA_BOT_SECRET` | Relay agente-plano-acao |
| `COMERCIAL_BOT_URL` + `COMERCIAL_BOT_SECRET` | Relay agente-comercial |
| `SECRETARIA_BOT_URL` + `SECRETARIA_BOT_SECRET` | Relay agente-secretaria (no-op se ausente) |
| `TMS_BOT_URL` + `TMS_BOT_SECRET` | Relay agente-tms `/webhook-retorno` (no-op se ausente) |
| `PESQUISADOR_BOT_URL` + `PESQUISADOR_BOT_SECRET` | Relay agente-pesquisador-genetica |
| `MULTIPLICACAO_BOT_URL` + `MULTIPLICACAO_BOT_SECRET` | Relay agente-bot-multiplicacao |
| `FINANCEIRO_BOT_URL` + `FINANCEIRO_BOT_SECRET` | Relay agente-financeiro-sa (preparado) |
| `ESTOQUE_BOT_URL` + `ESTOQUE_BOT_SECRET` | Relay agente-estoque (preparado) |
| `AGRONOMO_GRUPO_IDS` | Lista CSV de IDs de grupo roteados pro agronomo |
| `FINANCEIRO_GRUPO_IDS` / `ESTOQUE_GRUPO_IDS` / `PESQUISADOR_GRUPO_IDS` / `MULTIPLICACAO_GRUPO_IDS` | Idem |

## Como adicionar novo bot/grupo

1. Railway → Variables: setar `<NOME>_BOT_URL`, `<NOME>_BOT_SECRET` e (se for por grupo) `<NOME>_GRUPO_IDS`
2. `router.py` → `_carregar_rotas()` → adicionar bloco análogo (se for por grupo)
3. Pra keyword DM, editar `_KW_*` no `router.py`
4. `git push origin main` → Railway redeploya ~2 min

## Como descobrir ID de um grupo novo

1. Mande uma msg no grupo
2. Logs Railway: `grupo não mapeado: ...XXXX`
3. Copie e mapeie na variável

## Payload Z-API recebido

```json
{
  "isGroup": true,
  "phone": "120363407442457622-group",
  "participantPhone": "5564996261541",
  "fromMe": false,
  "text": { "message": "mensagem aqui" },
  "audio": null
}
```

## Payload adaptado pra agente-plano-acao (DMs)

```json
POST /processar-mensagem
X-API-Key: {PA_BOT_SECRET}

{"numero_zap": "5564996261541", "texto": "mensagem", "audio_url": null, "origem_audio": false}
```

Grupos e comercial/secretaria recebem **payload raw Z-API** (com `text`, `phone`, `origem_audio`).

## Segurança

- `ROUTER_SECRET` via `?token=` na URL Z-API
- Rate limiting: 120 req/min por IP (flask-limiter)
- Fail fast: serviço não sobe sem PA/COMERCIAL/AGRONOMO URL+SECRET
- Graceful degradation: erro em bot destino → loga e retorna 200 pro Z-API (não causa retry)
- LGPD: phone mascarado nos logs, áudio nunca persiste, zero gravação de payload pessoal

## Debug — Railway Logs

```
audio detectado | phone=***1541                  ← entrou Whisper
whisper: 12345 bytes -> 'preciso de uma cotação...'
relay_grupo -> agente-agronomo (200)             ← grupo roteado OK
relay_dm -> agente-plano-acao (200)              ← DM PA OK
relay_dm -> agente-comercial (200)               ← DM keyword comercial/agronomo OK
relay_dm -> agente-secretaria (200)              ← DM keyword agenda/reunião OK
relay_tms | phone=***1541 | RECLAMADO            ← transportadora respondendo cotação
ignorado: from_me                                ← eco do bot (normal)
ignorado: grupo_nao_mapeado                      ← grupo sem rota
ignorado: audio_nao_transcrito                   ← Whisper falhou (sem key ou timeout)
ignorado: dm_sem_conteudo                        ← DM vazia
```

## Histórico

- **2026-05-29** — keywords curtas aditivas em `_KW_COMERCIAL`: "comercial", "agronomo", "agrônomo"
- **2026-05-26** — relay TMS + relay secretaria (aditivos, no-op se URL ausente)
- **2026-05-12** — relay agente-bot-multiplicacao (grupo "Trigger pedidos")
- **2026-05-06** — Whisper inbound centralizado (ADR voz). Todos os bots passam a receber texto.
- **2026-05-02** — saneamento monorepo: router migrou pra repo isolado.

## Bug conhecido

**Fluxo CAR / Localização inbound**: router não tem relay pro `/webhook-incoming` do agente-whatsapp.
LocationMessage e códigos CAR (regex `[A-Z]{2}-\d{7}-[A-F0-9]{32}`) caem no PA por default.
Solução planejada: detectar location/regex CAR e relay pra `WHATSAPP_BOT_URL/webhook-incoming`.

## Decisões relacionadas

- ADR 2026-05-02 — saneamento monorepo 9 migrações
- ADR 2026-05-06 — voz WhatsApp inbound/outbound (Whisper centralizado aqui)
- ADR 2026-05-25 — router relay TMS retorno cotação
- ADR 2026-05-26 — agente-secretaria assistente de agenda
