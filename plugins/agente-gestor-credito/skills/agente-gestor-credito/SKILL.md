---
name: agente-gestor-credito
description: Primeiro agente N3 da Sementes Mana, bot do grupo WhatsApp "Gestor Comercial Mana" (id 120363407640929433-group). Flask no Railway: cruza pedidos a prazo do Simple Agro com scred (CRE-001) via SOAP fm_ws.getTableRecord, classifica gaps (SEM_CRE, CRE_DIGITACAO, CRE_NAO_APROVADA, PEDIDO_MAIOR_QUE_APROVADO), reconcilia state machine PG (schema gestor_credito), Claude Haiku gera relatorio e envia via agente-whatsapp. Desde 2026-05-30 (ADR-0008) faz tambem fan-out individual (DM) a cada vendedor com gap, cadastro em mapa_vendedores via /painel-config, agendamentos cron editaveis (alvo GRUPO|INDIVIDUAL|AMBOS), throttle 4s. Use SEMPRE em agente-gestor-credito - regra a prazo (cutoff 30/ago), severidade, pipeline, endpoints, painel, reconciliacao, integracoes, fan-out, agendamentos. Tambem bot gestor comercial, gap CRE, scred, CRE-001, painel-config, mapa_vendedores, ALERTA_INDIVIDUAL, fan-out, ADR-0005, ADR-0008.
---

# Agente Gestor de Crédito — Sementes Maná

> Primeiro agente N3 (Decisão Autônoma — nascente) da Maná. Em produção operacional desde **2026-05-16**. Observa pedidos a prazo no Simple Agro × CRE-001 no SoftExpert e alerta o grupo **"Gestor Comercial Maná"** sobre gaps. **2026-05-30:** ganhou fan-out individual (DM) por vendedor + agendamentos editáveis no painel (ADR-0008).

## Infraestrutura

| Item | Valor |
|---|---|
| URL produção | `https://agente-gestor-credito-production.up.railway.app` |
| Repositório | `github.com/Sementesmana/agente-gestor-credito` (isolado) |
| Clone local | `ORQUESTRADOR/agente-gestor-credito/` |
| Railway project | `agente-gestor-credito` |
| Workers | **1** (cron interno APScheduler) |
| Stack | Python 3.11 + Flask + Gunicorn + APScheduler + PostgreSQL (banco-mana, schema `gestor_credito`) |
| Envio WhatsApp | via **agente-whatsapp** `/send-whatsapp` (hub outbound) |
| Leitura SA | via **agente-financeiro-sa** `/api/financeiro` (fonte única) |
| Leitura SE | SOAP `fm_ws.getTableRecord(scred)` paginado |
| Grupo destino | "Gestor Comercial Maná" — `120363407640929433-group` |

## Arquivos (clone local)

```
agente-gestor-credito/
├── Procfile · railway.toml · requirements.txt · README.md
├── migrations/
│   ├── 001_init.sql                       gaps, notificacoes, snapshots, cache, v_gaps_abertos
│   ├── 002_motivos_novos.sql              novos motivos + responsavel (vendedor|credito)
│   └── 003_envio_individual.sql           mapa_vendedores + agendamentos + ALERTA_INDIVIDUAL [NOVO 2026-05-30]
├── static/css/mana.css · templates/painel.html · templates/painel-config.html [NOVO]
└── app/
    ├── main.py                            Flask + rotas (inclui /painel-config, /api/vendedores, /api/agendamentos)
    ├── config.py                          env validation (LGPD header)
    ├── auth/bearer.py                     decorators de auth
    ├── models/db.py                       pool psycopg2 + run_migrations
    ├── integrations/
    │   ├── financeiro_sa.py               cliente agente-financeiro-sa
    │   ├── softexpert.py                  SOAP fm_ws.getTableRecord(scred)
    │   ├── enrich_pedidos.py              enrich via agente-pedidos /sa-readonly-by-cnpj
    │   ├── whatsapp.py                    enviar_grupo + enviar_dm [NOVO]
    │   └── claude.py                      Haiku
    ├── services/
    │   ├── classificador.py               severidade SEM_CRE / CRE_DIGITACAO / NAO_APROVADA / PEDIDO_MAIOR
    │   ├── matcher.py                     SA × SE por CNPJ normalizado
    │   ├── reconciliador.py               state machine PG + registrar_notificacao_individual [NOVO]
    │   ├── orchestrator.py                pipeline + executar_fan_out_individual [NOVO]
    │   ├── relatorio.py                   formatar grupo + montar_mensagem_individual [NOVO]
    │   ├── vendedores.py                  CRUD mapa_vendedores + auto-upsert do SA [NOVO]
    │   └── agendamentos.py                CRUD + validar cron [NOVO]
    └── workers/
        ├── cron.py                        APScheduler lê tabela agendamentos (REFAC 2026-05-30)
        └── webhook_router.py              inbound NLP do agente-router
```

## Pipeline diário (default seed: 08h GRUPO + 08h15 INDIVIDUAL)

```
CRON tabela agendamentos
   │
   ▼
[1] Coleta SA (agente-financeiro-sa /api/financeiro, cache 20min)
[2] Coleta SE (SOAP fm_ws.getTableRecord(scred) paginado 50/pág)
[3] Filtra pedidos a prazo (qualquer parcela > cutoff safra 30/ago)
[4] Cruza por CNPJ
[5] Classifica severidade
[6] Reconcilia state machine PG
[7] Claude Haiku gera relatório (NOVOS / PERSISTENTES / RESOLVIDOS)
[8] POST /send-whatsapp → grupo                  (alvo GRUPO ou AMBOS)
[9] Auto-upsert mapa_vendedores do SA            (silencioso)
[10] Fan-out individual:                          (alvo INDIVIDUAL ou AMBOS)
       - Pra cada vendedor ativo com whatsapp:
         filtra rec por vendedor → monta msg → DM → throttle 4s
       - Vendedor sem gap hoje: silêncio
       - 1 DM/dia/vendedor (UNIQUE em notificacoes)
       - Cap MAX_DMS_POR_EXECUCAO (default 50)
```

## Schema PostgreSQL (`gestor_credito` no banco-mana)

| Tabela | Função |
|---|---|
| `gaps` | Registro central — status, dias_em_aberto, valores |
| `notificacoes` | Histórico (ALERTA_NOVO / PERSISTENTE / RESOLUCAO / INDIVIDUAL / LOTE) |
| `snapshots` | Agregado diário |
| `cache` | Cache simples (sessões/webhook) |
| `mapa_vendedores` [NOVO] | nome_canonico + whatsapp_numero + ativo |
| `agendamentos` [NOVO] | nome + cron_expr + alvo (GRUPO/INDIVIDUAL/AMBOS) + ativo |

**Idempotência:**
```sql
-- 1 gap ABERTO por cliente
CREATE UNIQUE INDEX idx_gaps_um_aberto_por_cliente
  ON gestor_credito.gaps(cnpj_cliente) WHERE status = 'ABERTO';

-- 1 DM individual por vendedor por dia
CREATE UNIQUE INDEX idx_notif_individual_unico_por_dia
  ON gestor_credito.notificacoes (vendedor_id, (enviado_em::date))
  WHERE tipo = 'ALERTA_INDIVIDUAL';
```

## Endpoints

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/health` | público | leve |
| GET | `/health/deep` | público | PG + SA + SE + WA + Claude + scheduler |
| POST | `/executar-analise` | Bearer | pipeline on-demand |
| POST | `/executar-fan-out?dry_run=1` | Bearer | fan-out individual on-demand |
| GET | `/gaps`, `/gaps/cliente/<cnpj>` | Bearer | JSON dos gaps |
| GET | `/painel?senha=` | PAINEL_SENHA | dashboard principal |
| GET | `/painel-config?senha=` | PAINEL_SENHA | **2 abas: Vendedores + Agendamentos** |
| GET | `/api/vendedores` | senha | listar vendedores |
| POST | `/api/vendedores/sincronizar` | senha | force upsert SA |
| PUT | `/api/vendedores/<id>` | senha | atualiza whatsapp/ativo |
| POST | `/api/vendedores/<id>/smoke-test` | senha | DM teste |
| GET\|POST\|PUT\|DELETE | `/api/agendamentos[/<id>]` | senha | CRUD horários |
| POST | `/api/agendamentos/recarregar` | senha | re-sync APScheduler |
| POST | `/webhook-router` | ROUTER_SHARED_SECRET | inbound NLP |
| POST | `/notificar-grupo` | Bearer | envio manual emergencial |

## Variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| `BANCO_MANA_URL` | — | PG centralizado |
| `FINANCEIRO_SA_URL` | — | painel-comercial-sa Railway |
| `PEDIDOS_URL` | https://agente-pedidos-sm.up.railway.app | enrich opcional |
| `SE_URL` / `SE_API_KEY` | — | SOAP fm_ws |
| `ANTHROPIC_API_KEY` / `CLAUDE_MODEL` | — / claude-haiku-4-5 | Haiku |
| `WHATSAPP_URL` / `WHATSAPP_API_KEY` | — | hub outbound |
| `GRUPO_GESTOR_CREDITO_ID` | — | id do grupo WhatsApp |
| `ROUTER_SHARED_SECRET` | — | inbound do router |
| `PAINEL_SENHA` | mana2026 | senha do painel |
| `BEARER_TOKEN` | — | endpoints internos |
| `THROTTLE_DM_S` [NOVO] | 4 | segundos entre DMs (evita flag Z-API) |
| `MAX_DMS_POR_EXECUCAO` [NOVO] | 50 | cap defensivo |

## Mensagem individual (DM) — comportamento

- **Conteúdo idêntico ao bloco do grupo daquele vendedor** (reusa `_bloco_vendedor`)
- **Cabeçalho personalizado** ("👋 Olá [Nome]" + data + exposição total)
- **Rodapé direto** indicando que é mensagem individual (o gestor também recebe consolidado no grupo)
- **Silêncio quando vendedor sem gap** (decisão Xayer 2026-05-30 — sem reforço positivo)
- **Idempotência:** 1 DM por vendedor por dia
- **Filtro:** só `responsavel='vendedor'` (gaps de crédito não vão pra vendedor)

## Selo agente (3 de 4 critérios)

| Critério | Atende? |
|---|---|
| Loop autônomo | ✅ cron diário (editável no painel) |
| Estado persistente | ✅ schema PG com state machine |
| Decisão de próxima ação | ✅ classifica severidade + sugere ação + filtra alvo |
| Multi-step planning | ❌ (futuro, Fase 3) |

## Crivos akita aplicados

- ✅ Validação de entrada whitelist (CNPJ regex, whatsapp regex `^55\d{10,11}$`, cron POSIX)
- ✅ Bearer obrigatório em endpoints internos
- ✅ Rate limit + throttle entre DMs
- ✅ Fallback: SA cair → cron pula com WARN; whatsapp cair → loga e segue
- ✅ Idempotência via UNIQUE parcial (gaps + notificacoes)
- ✅ Logs com CNPJ + número mascarado (LGPD)
- ✅ Finalidade documentada no header de `app/config.py`

## LGPD

- **Dado pessoal novo (2026-05-30):** whatsapp_numero do vendedor
- **Base legal:** execução de contrato de trabalho (LGPD art. 7º, V)
- **Retenção:** enquanto vendedor ativo
- **Opt-out:** gestor seta `ativo=FALSE` no painel
- **Logs:** sempre mascarado (`***%s` últimos 4 dígitos)
- **NÃO** envia dados a terceiros — fica entre SE / SA / banco-mana / agente-whatsapp

## Documentação canônica (ManaVault)

- **Nota do agente:** `ManaVault/06-Agentes-e-Skills/agente-gestor-credito.md`
- **ADR-0005 (fundador):** `ManaVault/08-Decisoes/2026-05-16-agente-gestor-credito-primeiro-N3.md`
- **ADR-0008 (fan-out):** `ManaVault/08-Decisoes/2026-05-30-agente-gestor-credito-envio-individual.md`
- **Modelo 3 níveis:** `ManaVault/05-Hiperautomacao/modelo-3-niveis.md`
- **Sinônimo no roadmap:** `agente-compliance-credito`
