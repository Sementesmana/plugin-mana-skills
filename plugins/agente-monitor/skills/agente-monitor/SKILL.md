---
name: agente-monitor
description: Torre de controle de runtime + cockpit de governança IA-First da Sementes Maná LTDA. Flask + APScheduler no Railway. Três missões num só serviço — (1) loop health de 19+ agentes a cada 5min com alerta WhatsApp ao grupo TI quando algum cai 2x consecutivas (ALERT_AFTER_FAILURES=2, ALERT_COOLDOWN=30min, HISTORY_MAX=288 = 24h); (2) aba Consumos que lê custo de IA por agente do mana-llm-gateway (LLM_GATEWAY_MASTER_KEY server-side, resolve alias→modelo via /model/info) + custo de infra Railway via /api/railway-usage; (3) cockpit /portfolio (catálogo canônico de 36 soluções via catalogo_solucoes.py, abas Catálogo/Construtores/Saúde/Arquitetura/Custos/Vencimentos/WhatsApp, ADR 2026-06-13). Use SEMPRE em tarefas do agente-monitor — adicionar agente à lista de health, ajustar threshold de alerta, mexer no cockpit /portfolio, adicionar coluna na aba Custos, integrar consumo do gateway, popular catalogo_solucoes, embed no SoftExpert, depurar alerta falso, ou entender por que o monitor é considerado quase-N3. Também quando mencionar painel monitor, torre de controle, health check, cockpit portfolio IA-First, /api/consumo, /api/status, /api/catalogo, /api/railway-usage, catálogo canônico, AGENTES em monitor_engine, /portfolio, cockpit Maná, Reqs por agente, US$/req, gasto mês/ano por agente, total dos logs, gateway spend, master key, ALERT_COOLDOWN, CHECK_INTERVAL.
---

# agente-monitor (Painel Monitor)

> Torre de controle de RUNTIME + cockpit de GOVERNANÇA do portfólio IA-First Maná. Quase-N3 (loop autônomo + estado + decisão de alertar).

## URL produção

`https://painel-monitor-production.up.railway.app`
Repo: `Sementesmana/agente-monitor` (clone local `ORQUESTRADOR/agente-monitor/` — drift: a nota do vault ainda menciona `agente-monitor-git`, mas hoje o clone com `.git` é o `agente-monitor/` mesmo).

## Três missões num só serviço

### 1. Loop de health (monitor_engine.py)

Thread `_monitor_loop()` que checa `/health` de cada agente em `AGENTES` (lista canônica em `monitor_engine.py`, hoje 19 entradas) a cada `CHECK_INTERVAL` (default 300s = 5min). Classifica como `online`, `slow` (acima de `SLOW_THRESHOLD=3.0s`) ou `offline`. Mantém histórico de `HISTORY_MAX=288` checks (24h × 5min).

Quando um agente cai **`ALERT_AFTER_FAILURES=2` vezes consecutivas**, dispara alerta WhatsApp pra `WHATSAPP_GRUPO_ID` via [[agente-whatsapp]] (`WHATSAPP_ALERT_URL`). Respeita `ALERT_COOLDOWN=1800s` (30min) entre alertas iguais — não spam.

**Funções principais:**
- `_check_agent_health(agente)` — bate em `agente['url'] + agente['health']`, mede latência
- `_fetch_agent_stats(agente)` — opcional, bate em `agente['stats']` se existir
- `_send_whatsapp_alert(agente, status, error_msg)` — manda o alerta
- `_run_check_cycle()` — uma rodada completa
- `start_monitor()` — sobe a thread no boot do Flask
- `run_check_now()` — força check sob demanda (chamado pelo `/api/check-now`)

### 2. Aba Consumos — custo automático (desde 24/05)

`GET /api/consumo` retorna `{railway, zapi, gateway}` consolidado:

- **railway** — `_fetch_railway_usage()` consulta Railway GraphQL via `RAILWAY_API_TOKEN`. Custo por projeto.
- **zapi** — `_fetch_zapi_status()` puxa status da instância Z-API (`ZAPI_INSTANCE_ID/TOKEN/CLIENT_TOKEN`).
- **gateway** — `_fetch_gateway_spend()` lê do [[mana-llm-gateway]] via `LLM_GATEWAY_URL` + `LLM_GATEWAY_MASTER_KEY` (master key server-side, **nunca expor pro browser**). Resolve `alias → modelo real` via `/model/info` do gateway. Retorna por agente: `total_mes`, `total_ano`, `total_logs`, `reqs`, `usd_por_req`, `budget`, `ultimo_uso`, `modelos`.

Visualizado no cockpit `/portfolio` (aba Custos, função `renderConsumoLive()`), pré-carregada no boot (ver commit `15e0d44`). Tabela tem colunas: Agente · Modelos (alias) · Mês · Ano · Reqs · US$/req · Budget · Últ. uso. Subtotal mostra mês/ano/total em US$ com 4 casas decimais.

**Limitação real:** o gateway só vê os agentes **já migrados** pra ele. Hoje a migração ainda está incompleta (NF e agronomo migrados, comercial pendente — task #16). Por isso muitos agentes aparecem com US$ 0,0000 — não é bug, é cobertura.

### 3. Cockpit /portfolio (desde 2026-06-13)

Página embeddable em `/portfolio` que serve o `portfolio.html` (single-file, ~604 linhas, sem build). 7 abas:

| Aba | data-view | Conteúdo |
|---|---|---|
| Catálogo | `catalogo` | 36 soluções via `/api/catalogo` (canônico de `catalogo_solucoes.py`) |
| Construtores | `construtores` | Quem constrói/mantém cada solução |
| Saúde | `saude` | Lê `/api/status` same-origin (status do loop) |
| Arquitetura | `arquitetura` | Diagrama em camadas IA-First (gateway, observabilidade, evals, sandbox, dados governados) |
| Custos | `custos` | Cadastro manual (localStorage) + custo automático via `/api/consumo` |
| Vencimentos | `vencimentos` | Calendário de obrigações alimentado por "Dia venc." da aba Custos |
| WhatsApp | `whatsapp` | Lê fila/log do outbox do `agente-whatsapp` (`/api/outbox`) — Onda 1 do mana-whatsapp-gateway |

**Cadastro manual da aba Custos** (estrutura atual):

```
Serviço | Categoria | Valor/mês (R$) | Ciclo | Dia venc. | Pagador
```

Schema do array `DEFAULT_CUSTOS` em JS: `{serv, cat, val, ciclo, dia, pag}`. Salva no `localStorage` do browser (chave `mana_cockpit_v0`). Funções: `renderCustos()`, `updC(i,k,v)`, `addCusto()`, `delC(i)`.

ADR vinculado: [[2026-06-13-catalogo-solucoes-manifesto-por-solucao]]. `/painel` antigo segue intacto pra não quebrar embed do SE.

## catalogo_solucoes.py — fonte canônica

86 linhas, dicionário `CATALOGO` com 1 entrada por solução. Campos: `id`, `com` (nome comercial), `tipo` (agente/app/painel/atividade-se/plataforma), `nivel` (N1/N2/N3), `status`, `owner`, `url`, `repo`, `cadeia` (apoio/negocio/gestao), `area`, `con` (conectores), `mem` (memória), `obs`. Duas funções:

- `catalogo_completo()` — todas as soluções pra governança
- `agentes_para_health()` — só as com URL pública, formato do `monitor_engine.AGENTES`

**Pendente deliberado** (passo 2): trocar `monitor_engine.AGENTES` pra vir de `catalogo_solucoes.agentes_para_health()`. Não feito por causa do risco de alerta falso (soluções sem `/health`). Fazer com `WHATSAPP_GRUPO_ID` mutado, validar na aba Saúde, corrigir, religar.

## Endpoints Flask (app.py — 1496 linhas)

| Método | Path | Função |
|---|---|---|
| GET | `/health` | Liveness do próprio monitor + métrica `agentes_online: "X/Y"` |
| GET | `/api/status` | Status atual de cada agente (online/slow/offline + latência) |
| GET | `/api/history` | Histórico de 24h (até `HISTORY_MAX` checks) |
| GET | `/api/logs` | Logs de erro recentes |
| GET | `/api/stats` | Estatísticas (uptime/latência média) |
| POST | `/api/check-now` | Força um ciclo de check imediato |
| GET | `/api/consumo` | Custo consolidado (railway + zapi + gateway) |
| GET | `/api/catalogo` | Catálogo canônico (`catalogo_completo()`) |
| GET | `/api/outbox` | Fila do `agente-whatsapp` (proxy pra `/api/outbox` do hub) |
| GET | `/portfolio` | Cockpit IA-First (serve `portfolio.html`) |
| GET | `/painel` | Painel antigo (embed legacy SE) |

## Variáveis de ambiente

**Obrigatórias:**
- `RAILWAY_API_TOKEN` — Railway GraphQL (custo/uso por projeto)
- `ZAPI_INSTANCE_ID`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN` — alertas WhatsApp
- `LLM_GATEWAY_URL`, `LLM_GATEWAY_MASTER_KEY` — leitura de gasto de IA por agente (master key NUNCA vai pro browser)
- `WHATSAPP_GRUPO_ID` — destinatário dos alertas (mutar pra silenciar em validação)
- `WHATSAPP_ALERT_URL` — default aponta pro [[agente-whatsapp]]

**Opcionais (com defaults):**
- `CHECK_INTERVAL=300`, `HEALTH_TIMEOUT=10`, `SLOW_THRESHOLD=3.0`
- `ALERT_AFTER_FAILURES=2`, `HISTORY_MAX=288`, `ALERT_COOLDOWN=1800`
- `PAINEL_SENHA=mana2026`
- `ANTHROPIC_API_KEY` (uso futuro)
- `WHATSAPP_OUTBOX_URL`, `WHATSAPP_OUTBOX_TOKEN` — pra aba WhatsApp ler fila do hub

## Como adicionar agente novo à lista de health

Editar `monitor_engine.py`, array `AGENTES` (linha 35). Item:

```python
{
    "id": "agente-xxx",                # kebab-case
    "nome": "Agente XXX",              # legível
    "url": "https://agente-xxx-production.up.railway.app",
    "health": "/health",                # endpoint
    "stats": None,                      # ou "/status" se tiver
    "descricao": "O que faz em 1 linha",
},
```

`git add monitor_engine.py && git commit -m "feat: add agente-xxx ao monitor" && git push`. Railway redeploya em ~1min. Atualizar a nota do vault no mesmo PR (ou commit subsequente, mas sem deixar pra depois).

## Como adicionar coluna na aba Custos (cockpit)

Quatro edits em `portfolio.html`:

1. **Header da tabela** (`<thead>` em `<table id="tblCustos">`) — adicionar `<th>NomeNovo</th>` na posição certa.
2. **renderCustos()** — adicionar `<td><input ... 'campo' ...></td>` correspondente no template literal.
3. **addCusto()** — adicionar `campo:''` no objeto novo.
4. **DEFAULT_CUSTOS** (opcional) — adicionar `campo:''` em cada item se quiser que linhas existentes carreguem com o campo.

Não precisa migração de localStorage — `${c.campo||''}` lida com undefined. Verificar integridade antes de commit: `</script>=1`, `</body>=1`, `</html>=1` (bash do mount pode bugar na leitura; usar Read tool se duvidar).

## Como popular catalogo_solucoes.py

Adicionar dicionário no array `CATALOGO`. Campos obrigatórios: `id`, `com`, `tipo`, `nivel`, `status`, `owner`, `url`, `repo`, `cadeia`, `area`. Opcionais: `con` (lista), `mem`, `obs`. Reflete imediatamente em `/api/catalogo` e em todas as abas do cockpit que consomem o catálogo.

## Disciplina vault — quando atualizar a nota

`ManaVault/06-Agentes-e-Skills/agente-monitor.md` (`ultima-revisao` no frontmatter). Atualizar sempre que mudar:

- `AGENTES` (lista de health)
- `CATALOGO` (catálogo canônico)
- Endpoints (add/remove/rename)
- Env vars
- Aba do cockpit (add/remove/rename)
- Threshold de alerta

**Drift conhecido (2026-06-15):** a nota cita `agente-monitor-git` como clone real, mas hoje o clone com `.git` é o `agente-monitor/` mesmo (consolidado). Atualizar a nota na próxima oportunidade que mexer nela.

## Decisões relacionadas (ADRs)

- [[2026-05-02-saneamento-monorepo-9-migracoes]] — agente-monitor migrado pra repo isolado
- [[2026-05-23-mana-llm-gateway-litellm]] — gateway que alimenta a aba Consumos
- [[2026-06-13-catalogo-solucoes-manifesto-por-solucao]] — cockpit `/portfolio` + `catalogo_solucoes.py` como fonte canônica
- [[2026-05-13-skill-md-vive-no-repo]] — esta skill canônica vive aqui (raiz do repo)
- [[2026-06-15-portabilidade-cowork-code-pacote-autocontido-por-agente]] — cópia em `.claude/skills/agente-monitor/SKILL.md` carrega no Code automaticamente

## Padrões críticos a respeitar

1. **Master key do gateway é server-side.** `LLM_GATEWAY_MASTER_KEY` nunca pode vazar pro HTML/JS. Já tá certo no `_fetch_gateway_spend()`, manter assim.
2. **Aba Custos é localStorage do browser do operador.** Não tem persistência server-side — é por design (cada dono cadastra os custos que enxerga). Não migrar pra banco sem ADR.
3. **`WHATSAPP_GRUPO_ID` é o gatilho de tráfego de alertas.** Pra testar mudança de threshold/lista, **mutar a env primeiro** (`WHATSAPP_GRUPO_ID=""`) — senão TI recebe disparo falso.
4. **Cockpit é embed no SE.** Manter `/portfolio` em rota fixa, manter `/painel` antigo intacto (legacy embed).
5. **Loop é robusto a falha individual.** `_check_agent_health` deve sempre retornar status, nunca raise — se um agente bate em SSL erro, marca offline, segue ciclo.

## Smoke test pós-deploy

1. `curl https://painel-monitor-production.up.railway.app/health` → JSON com `agentes_online: "X/Y"`
2. `curl .../api/status` → lista com cada agente
3. Abrir `/portfolio?senha=mana2026` no browser, conferir 7 abas funcionando
4. Aba Custos → "Carregando consumo ao vivo…" → tabela com gasto por agente (Mês/Ano/Reqs/US$/req)
5. Aba Saúde → mesmo dado do `/api/status` renderizado

Se aba Custos mostrar "Não consegui ler /api/consumo": ver se `LLM_GATEWAY_URL` e `LLM_GATEWAY_MASTER_KEY` estão no Railway env do monitor.
