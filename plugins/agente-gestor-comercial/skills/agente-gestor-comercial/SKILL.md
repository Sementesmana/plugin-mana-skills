---
name: agente-gestor-comercial
description: Agente N3 da Sementes Mana (ex agente-gestor-credito, ADR-0009) - bot do grupo WhatsApp 'Gestor Comercial Mana'. Flask+PG+Railway: cruza pedidos a prazo do Simple Agro com scred (CRE-001) via SOAP fm_ws, classifica gaps, reconcilia state machine (schema gestor_credito), Claude Haiku gera relatorio, envia via agente-whatsapp. 3 categorias: Gap CRE (cliente), Divergencia cadastro PRAZO/VISTA (pedido), FALTA_COORDENADAS lat/lng (ADR-0010). Fan-out individual (DM) por vendedor (ADR-0008). Portal de ocorrencias (cockpit GRD, 2026-06-19): tabela ocorrencias, regua SLA, Pareto, cobrar 1-clique (PDF). UI 2026-06-21: layout app-shell com sidebar, botao Cobrar no card do vendedor, Pareto drill-down por nº de ocorrencias (vendedor->tipo->cliente->pedido). Use SEMPRE em agente-gestor-comercial OU nome antigo - regra a prazo (cutoff 30/ago), pipeline, painel/portal, fan-out, cobrar, pareto. Tambem gap CRE, scred, CRE-001, mapa_vendedores, cockpit GRD, /portal, /api/ocorrencias, ADR-0005/0008/0009/0010.
---

# Agente Gestor Comercial - Sementes Mana

> **2026-05-30:** Renomeado de `agente-gestor-credito` para `agente-gestor-comercial` (ADR-0009). Schema PG `gestor_credito` MANTIDO pra nao perder dados historicos. URL Railway antiga preservada.
>
> Primeiro agente N3 (Decisao Autonoma - nascente) da Mana. Em producao operacional desde **2026-05-16**. Observa pedidos a prazo no Simple Agro x CRE-001 no SoftExpert e alerta o grupo **"Gestor Comercial Mana"** sobre 3 categorias de problema (gaps de credito, divergencia de cadastro, coordenadas faltando). **2026-05-30:** ganhou fan-out individual (DM) por vendedor (ADR-0008) + checagem de lat/lng (ADR-0010).

## Infraestrutura

| Item | Valor |
|---|---|
| URL producao | `https://agente-gestor-credito-production.up.railway.app` (mantida) |
| Repositorio | `github.com/Sementesmana/agente-gestor-comercial` |
| Clone local | `ORQUESTRADOR/agente-gestor-comercial/` |
| Railway project | `agente-gestor-comercial` |
| Schema PG | `gestor_credito` (mantido por compat) |
| Workers | **1** (cron interno APScheduler) |
| Stack | Python 3.11 + Flask + Gunicorn + APScheduler + PostgreSQL |
| Envio WhatsApp | via **agente-whatsapp** (hub outbound) |
| Leitura SA financeiro | via **agente-financeiro-sa** (fonte unica) |
| Leitura SA orders | DIRETO `/api/orders` (exceção ADR-0010, igual TMS faz) |
| Leitura SE | SOAP `fm_ws.getTableRecord(scred)` paginado |
| Grupo destino | "Gestor Comercial Mana" - `120363407640929433-group` |

## Pipeline diario

```
CRON tabela agendamentos (editavel via /painel-config)
   v
[1] Coleta SA financeiro (agente-financeiro-sa /api/financeiro, cache 20min)
[2] Coleta SE (SOAP fm_ws.getTableRecord(scred) paginado)
[3] Filtra pedidos a prazo (qualquer parcela > cutoff safra 30/ago)
[4] Cruza por CNPJ, classifica severidade (4 motivos)
[4b] Detecta divergencias PRAZO_MAS_AVISTA / VISTA_MAS_APRAZO
[4b.2] Coleta SA orders (/api/orders), detecta FALTA_COORDENADAS  <-- NOVO ADR-0010
[5] Reconcilia state machine PG
[6] Claude Haiku gera relatorio
[7] POST /send-whatsapp -> grupo                  (alvo GRUPO ou AMBOS)
[8] Snapshot
[9] Auto-upsert mapa_vendedores do SA
[10] Fan-out individual:                          (alvo INDIVIDUAL ou AMBOS)
       - Pra cada vendedor ativo com whatsapp:
         filtra rec por vendedor -> monta msg -> DM -> throttle 4s
       - Vendedor sem gap hoje: silencio
       - 1 DM/dia/vendedor (UNIQUE em notificacoes)
```

## 3 categorias de alerta no relatorio/DM

| Categoria | Granularidade | Como detecta |
|---|---|---|
| **Gap CRE** (SEM_CRE / CRE_DIGITACAO / CRE_INSUFICIENTE / ...) | por CLIENTE (CNPJ) | soma pedidos a prazo do cliente vs CRE-001 cobrindo |
| **Divergencia cadastro** (PRAZO_MAS_AVISTA / VISTA_MAS_APRAZO) | por PEDIDO | tipo_pagamento SA vs realidade pelas parcelas |
| **FALTA_COORDENADAS** (ADR-0010) | por PEDIDO | geolocalizacao_entrega.latitude/longitude ausente ou ~0 |

Mesmo pedido pode aparecer em multiplas categorias se tiver multiplos problemas.

## Schema PostgreSQL (`gestor_credito` - nome legado)

| Tabela | Funcao |
|---|---|
| `gaps` | Registro central - status, dias_em_aberto, valores |
| `notificacoes` | Historico (ALERTA_NOVO/PERSISTENTE/RESOLUCAO/INDIVIDUAL/LOTE) |
| `snapshots` | Agregado diario |
| `mapa_vendedores` | nome_canonico + whatsapp_numero + ativo (ADR-0008) |
| `agendamentos` | nome + cron_expr + alvo (GRUPO/INDIVIDUAL/AMBOS) (ADR-0008) |
| `ocorrencias` | Modelo unico `tipo`+`payload` das 3 categorias - aging, ciclo sanou/nao, reincidencia, ultima_notificacao (portal 2026-06-19) |
| `config` | Regua SLA (`sla_pouco_ate`/`sla_medio_ate`/`sla_critico_ate`, default 2/5/10) + parametros do portal |

## Endpoints

| Metodo | Rota | Auth |
|---|---|---|
| GET | `/health` / `/health/deep` | publico |
| POST | `/executar-analise` / `/executar-fan-out?dry_run=1` | Bearer |
| GET | `/gaps` / `/gaps/cliente/<cnpj>` | Bearer |
| GET | `/painel?senha=` / `/painel-config?senha=` | PAINEL_SENHA |
| GET/POST/PUT/DELETE | `/api/vendedores[/<id>]`, `/api/agendamentos[/<id>]` | senha |
| POST | `/api/vendedores/sincronizar`, `/api/agendamentos/recarregar` | senha |
| POST | `/api/vendedores/<id>/smoke-test` | senha |
| POST | `/webhook-router` | ROUTER_SHARED_SECRET |
| POST | `/notificar-grupo` | Bearer |
| GET | `/portal?senha=` (cockpit GRD de ocorrencias) | PAINEL_SENHA |
| GET | `/api/ocorrencias?senha=` (abertas + regua SLA + balanca 7d) | senha |
| POST | `/api/cobrar/<id>` / `/api/cobrar-cliente/<cnpj>` / `/api/cobrar-vendedor/<id>` (gera PDF + dispara grupo/DM) | senha |

## Variaveis de ambiente

| Variavel | Default |
|---|---|
| `BANCO_MANA_URL` / `SE_URL` / `SE_API_KEY` / `FINANCEIRO_SA_URL` | - |
| `ANTHROPIC_API_KEY` / `CLAUDE_MODEL` | claude-haiku-4-5 |
| `WHATSAPP_URL` / `WHATSAPP_API_KEY` | - |
| `GRUPO_GESTOR_CREDITO_ID` (legado, mantido) | id do grupo |
| `ROUTER_SHARED_SECRET` / `BEARER_TOKEN` / `PAINEL_SENHA` | mana2026 |
| `THROTTLE_DM_S` / `MAX_DMS_POR_EXECUCAO` | 4 / 50 |
| `SA_USERNAME` / `SA_PASSWORD` / `SA_SAFRA_ID` / `SA_GRUPO_ID` (ADR-0010) | mesmos valores do agente-tms |

## Modulos principais

- `app/integrations/financeiro_sa.py` - cliente do agente-financeiro-sa
- `app/integrations/softexpert.py` - SOAP fm_ws scred
- `app/integrations/enrich_pedidos.py` - via agente-pedidos /sa-readonly-by-cnpj
- `app/integrations/coordenadas_sa.py` (ADR-0010) - direto SA /api/orders, reusa _coord do TMS
- `app/integrations/whatsapp.py` - enviar_grupo + enviar_dm
- `app/integrations/claude.py` - Haiku
- `app/services/classificador.py` - severidade 4 motivos
- `app/services/matcher.py` - cruzament