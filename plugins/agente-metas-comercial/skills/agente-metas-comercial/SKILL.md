---
name: agente-metas-comercial
description: CPM Comercial (gestor Alex Matias) — app de gestão de metas por vendedor e cultivar da Sementes Maná LTDA. Substitui a planilha manual semanal: realizado automático do Simple Agro (funil-espelho do agente-estoque), metas versionadas com cascateamento (INICIAL/CASCATA/REALOCACAO/AJUSTE/VOLUME_NOVO), telas painel/consolidado/metas/timeline/config, multi-safra com seletor na sidebar, e (Fase 2 plugável) alimentação do SoftExpert CPM via DI014 + SOAP addMultipleMeasuresInAdinterface. Flask+PostgreSQL schema `metas` no banco-mana, gunicorn 1 worker gthread 8 threads, deploy Railway (público). Use SEMPRE em tarefas do agente-metas-comercial — metas, cascateamento, realizado SA, funil-espelho, ranking gauge, timeline, consolidado estoque×meta×vendido, ID vs idscmetric, DI014, safra 26/27. Também quando mencionar: CPM Comercial, gestor Alex Matias, metas comerciais, cascata de metas, meta_versoes, snapshot_pedidos, sync_runs, depara_se, banco-mana schema metas, ThreadedConnectionPool 1..8, ADR funil-espelho 2026-07-17, addMultipleMeasuresInAdinterface, viewScMetricData, ST007.
---

# Agente Metas Comercial (CPM Comercial) — Sementes Maná LTDA

App de gestão de metas da área comercial (gestor: **Alex Matias Jorge**), safra 26/27. Substitui a planilha manual semanal: realizado automático do Simple Agro, metas versionadas com cascateamento, e (Fase 2 plugável) alimentação do SoftExpert CPM/Desempenho.

- **Repo:** `Sementesmana/agente-metas-comercial` (público)
- **Produção:** https://agente-meta-comercial-production.up.railway.app
- **Nível:** N2 (autoridade = sugere; loop autônomo = false)
- **Status:** PROD desde 2026-07-17

## Arquitetura-triângulo

**Simple Agro** (realizado) → **APP** (fonte da verdade da meta) → **SoftExpert CPM** (retrato oficial).

- **Fase 1** (construída 2026-07-17): ingestão SA + painel + gestão/versionamento de metas + eventos.
- **Fase 2** (plugável, não construída): planilhas STR* via DI014 (estrutura) + SOAP `addMultipleMeasuresInAdinterface` (valores). Docs em `ORQUESTRADOR/Softexpert CPM/`.

## ⚠️ REGRA DE OURO — funil-espelho do agente-estoque

O VENDIDO deste app deve ser **o mesmo número** do `agente-estoque` (decisão do Xayer, 2026-07-17). O `sa_client.py` é cópia do modelo de leitura do SA de lá (sem tocar no repo do Dayan):

- `item.quantidade` **já é bags** — sem conversão
- Status contabilizados: `aguardando aprovacao` + `integrado` + `aprovado` (norm sem acento)
- `norm_nome` cultivar: uppercase + espaços colapsados
- `GET /api/orders` com `safra.id` + `itens.grupo_produto.id` + `deleted=false`
- Env `SA_SAFRA_ID` / `SA_GRUPO_ID` com os MESMOS valores do agente-estoque

**Se o funil mudar no agente-estoque → mudar aqui junto** (`sa_client.py` + `config.py`).

## Função

1. **Pipeline** (cron 08h BRT + botão "Atualizar agora", advisory lock 742601): (1) ingestão SA → (2) snapshot pedido×cultivar → (3) diff → eventos **NOVO / AJUSTE / SAIU_FUNIL / ENTROU_FUNIL / REMOVIDO** — o "por que mudou". Sequencial atômico: falhou a etapa 1, nada grava.
2. **Metas versionadas**: vigente única por safra×vendedor×cultivar; toda edição cria versão (tipo INICIAL/CASCATA/REALOCACAO/AJUSTE/VOLUME_NOVO + motivo + autor).
3. **Cascateamento**: modal com rateio igual/proporcional/manual, preview, motivo obrigatório; SOMA por cima das metas vigentes.
4. **Estoque inicial** do consolidado: lido do `/api/estoque` do agente-estoque (só leitura; graceful degradation se fora).
5. **Data de contratação** por vendedor (ramp-up/tempo de casa no ranking).

## Telas

- `/painel` — Visão geral (KPIs, ranking gauge, drill vendedor com pedidos)
- `/consolidado` — estoque×meta×vendido, saldos
- `/metas` — grade editável + cascata
- `/timeline` — feed realizado+metas
- `/config` — contratação, cultivares ocultas, histórico de sync
- `/login`

## Endpoints

- `GET /health`
- `POST /api/sync` (admin) · `GET /api/sync/status`
- `GET /api/dashboard` · `/api/vendedor/<id>` · `/api/consolidado` · `/api/timeline`
- `GET /api/metas/grade` · `POST /api/metas` · `POST /api/metas/cascata[/preview]` · `GET /api/metas/historico`
- `GET/POST /api/vendedores[/<id>]` · `POST /api/cultivares/<id>`

## Banco

**banco-mana**, schema `metas` (padrão schema-por-agente, ADR do tms):
`safras` (label, sa_safra_id, atual), `vendedores`, `cultivares`, `meta_versoes` (unique parcial vigente), `sync_runs` (c/ safra), `snapshot_pedidos`, `eventos`, `depara_se` (Fase 2), `audit_log`.

## Multi-safra (2026-07-17)

- Cadastro de safras na Config (label + ID da safra no SA); **uma marcada como atual** — é a que o sync (cron/botão) busca no SA.
- **Seletor de safra** na sidebar; `?safra=` propagado em links e APIs (junto com `?senha=`); metas/visões/grade/timeline isoladas por safra. Permite planejar a 27/28 (vendedores/cultivares novos) enquanto a 26/27 roda.
- Label corrente: **SAFRA 26/27** (migração automática dos registros "SAFRA 26").
- `depara_se` ganhou `safra` + `chave_app` + `id_indicador` (unique safra×vendedor×COALESCE(cultivar,0)).

### Modelo de 2 níveis do SE (Xayer 2026-07-17)

- `id_indicador` = código do CADASTRO (ST007; variedade XYZ é 1 indicador de catálogo compartilhado)
- `idscmetric` = identificador da AMARRAÇÃO no scorecard (XYZ nos 11 vendedores = 11 idscmetric)
- **A chave de escrita do `addMeasuresInAdinterface` é o `idscmetric` da amarração.**

Preenchimento (Fase 2):
(a) estrutura gerada pelo app → identificadores nossos `COM-<SAFRA>-<VEND>-<CULT>` (STRSCMETRIC pede os 2 níveis);
(b) estrutura manual no SE → ler via `viewScMetricData`/`viewScorecardMetricValuesData` e casar por nome, com tela de conferência.

## Variáveis de ambiente

`DATABASE_URL` (banco-mana) · `DB_SCHEMA=metas` · `SA_BASE_URL/SA_USERNAME/SA_PASSWORD` · `SA_SAFRA_ID/SA_GRUPO_ID` (= agente-estoque) · `ESTOQUE_API_URL` · `SAFRA_LABEL` · `PAINEL_SENHA` (leitura) · `ADMIN_SENHA` (edição) · `SECRET_KEY` · `CRON_HOUR=8` · `TZ=America/Sao_Paulo` · `DISABLE_CRON=1` (dev).

## Auth

Senha painel (leitura) + senha admin (edição). Cookie de sessão Flask; aceita `?senha=` na URL (padrão embed Página WEB do SE).

## Stack / Deploy

Flask + Jinja2 + Alpine-style vanilla JS · identidade Maná (verde/ouro, Playfair+DM Sans) · gunicorn 1 worker gthread 8 threads (receita perf 2026-07-11; 1 worker = 1 scheduler) · Railway via git push. Zero-LLM, zero-WhatsApp na Fase 1 (conformidade-por-ausência com o `mana-arquitetura-padrao`; ao entrar LLM/WhatsApp, seguir o checklist do ADR 2026-06-13).

## ⚡ Perf (banco-mana remoto — 2026-07-17)

Painel estava lento: conexão nova por request contra PG remoto (handshake 200-500ms + RTT/query). Correção em 3 pontos:

1. `db.py` — **ThreadedConnectionPool 1..8** (casa com as 8 threads) + keepalives + `search_path` via `options` na criação (zero roundtrip). Rotas usam `with db_conn()` (commit/rollback + devolve ao pool); pipeline usa `get_db()/put_db()`.
2. `pipeline.py` — upserts de vendedores/cultivares em **batch** (execute_values ON CONFLICT + 1 SELECT) em vez de ~55 INSERTs individuais.
3. `cache.py` — cache leve 60s dos payloads de leitura; **invalidação total** em qualquer escrita (meta/cadastro) e ao fim de cada sync — dado nunca fica velho pós-ação. (1 worker → sem problema de cache por-worker.)

## Testes

`tests/` — 17 unitários (funil espelho, diff, rateio) + integração end-to-end validada com Postgres local (2 runs com diff, versionamento, cascata, visões).

## Consumidores

- **Alex (gestor comercial)** — admin de metas
- **Diretoria/time comercial** — leitura; futuro embed no SE
- **Fase 2**: SoftExpert CPM (scorecard vendedor→cultivar)

## Decisões relacionadas

- Funil-espelho do agente-estoque (Xayer, 2026-07-17) — sem tocar no repo do Dayan
- Frequência SE: Mensal + acumulação Soma janela da safra + meta por período de acumulação + faixa do acumulado (validado nas telas ST007)
- Estrutura SE via DI014/planilhas (upload manual; RPA descartado no MVP)
- Cadência: cron 08h + botão manual; meta → push SE imediato (Fase 2)

## Pendências

- [x] Repo GitHub (público) + Railway + env vars — no ar 2026-07-17
- [ ] Janela da safra 26 (Xayer × Alex) — define config SE da Fase 2
- [ ] Cadastros básicos no SE (unidade Bags, scorecard, faixas) (Xayer)
- [ ] Datas de contratação dos vendedores (Alex)
- [ ] Carga inicial de metas (planilha do Alex → grade)
- [ ] Fase 2: gerador STR* + push SOAP + de-para
