---
name: agente-pedidos
description: Ponte de LEITURA SoftExpert ↔ Simple Agro da Sementes Maná LTDA + painel-reais da carteira de crédito. Flask no Railway, somente leitura no SE (nada é gravado no formulário). O SE chama /pedidos-venda como Fonte de Dados REST na atividade de crédito — o agente lê o cpf_cnpj do scred via SOAP fm_ws, autentica no SA com usuário dedicado, busca pedidos Soja/safra 26/27, expande grupo econômico pelos CNPJs do campo grupoeconomico e mapeia SA→grid SE via CAMPO_MAP (lista de fallbacks por campo, porque o SA renomeia campo sem aviso). Primeiro consumidor do banco-mana com schema dedicado agente_pedidos — data lake lake-first (workflows, detalhe, detalhe-cnpj, totais, usos, atividades, tempos, gaps) com fallback ao vivo, atualizado por /api/atualizar-data-lake. Use SEMPRE em tarefas do agente-pedidos — Fonte de Dados REST do SE, CAMPO_MAP, grupo econômico, data lake, painel-reais, situação de crédito, tempos de atividade, gaps sem CRE. Também quando mencionar: /pedidos-venda, /painel-reais, /api/atualizar-data-lake, /api/data-lake-status, /api/situacao-credito, /api/tempos, /api/gaps-sem-cre, lake-first, SA_SAFRA_ID, SA_GRUPO_ID, usuário dedicado SA, 452 single-session, bridge SE-SA somente leitura.
---

# agente-pedidos — ponte de leitura SE ↔ Simple Agro

> **Somente leitura no SoftExpert.** Nada é gravado em formulário. O SE consome dados ao vivo (ou do lake) via Fonte de Dados REST.

## O que é

Duas funções no mesmo serviço:

1. **Fonte de Dados REST do SE** — quando alguém abre a atividade de crédito, o SE chama `/pedidos-venda?idprocess=XXX` e recebe a tabela de pedidos do Simple Agro daquele cliente.
2. **Painel de carteira (`/painel-reais`)** — visão consolidada dos processos de crédito abertos × pedidos SA, com situação de crédito, tempos de atividade e gaps.

Stack: Python 3.11 + Flask + Gunicorn no Railway · `requests` (SA REST + XSRF) · SE SOAP (`fm_ws`/`wf_ws`) · PostgreSQL (`banco-mana`, schema `agente_pedidos`).

## Pipeline do /pedidos-venda

```
SoftExpert (Fonte de Dados REST)
   │  GET /pedidos-venda?idprocess=XXX
   ├── 1. SE SOAP fm_ws    → lê cpf_cnpj do formulário scred
   ├── 2. SA Auth          → login com usuário DEDICADO à automação
   ├── 3. SA API           → pedidos SOJA / SAFRA 26/27 por CNPJ
   ├── 4. Grupo econômico  → soma os CNPJs do campo `grupoeconomico` (separados por vírgula)
   ├── 5. CAMPO_MAP        → JSON SA → campos da grid SE
   └── JSON → SE renderiza a tabela na atividade
```

`/pedidos-venda` **não exige senha** — quem chama é o SE, que já tem a própria autenticação. As rotas de painel exigem `X-Painel-Senha` ou `?senha=`.

## Por que somente leitura (decisão que não deve ser revertida)

As versões v1/v2 **gravavam** os pedidos no formulário do SE. Resultado: pedido cancelado ficava vivo no SE e pedido novo não entrava — estado intermediário para sincronizar é dívida garantida. A Fonte de Dados REST elimina o sync: o SE sempre lê o retrato atual.

## CAMPO_MAP — fallback por campo

O Simple Agro **não tem API versionada**: campo muda de nome sem aviso. Cada campo do SE aponta para uma lista de nomes possíveis:

```python
"nomecliente": ["cliente_nome", "cliente.nome"],
"produto":     ["produto_nome", "produto.nome"],
```

Monitorar `[WARN] campo X não mapeado` no log — é o detector de drift do ERP. Ao adicionar campo novo, **sempre** com lista de fallbacks, nunca com nome único.

## Data lake (schema `agente_pedidos` no banco-mana)

Primeiro consumidor do `banco-mana` pelo agente (ADR `mana-data-gateway`, 2026-06-30). Schema **dedicado — nunca `public`**; fail-soft se `BANCO_MANA_URL` não estiver configurado (o serviço continua servindo ao vivo).

Padrão **lake-first** em todas as leituras caras: se existe snapshot, serve do lake com `"fonte": "lake"`; senão calcula ao vivo. Chaves: `workflows`, `detalhe:<idprocess>`, `detalhe-cnpj:<digits>`, `totais`, `usos`, `atividades`, `tempos`, `gaps`.

- `POST|GET /api/atualizar-data-lake` — recalcula os snapshots (cron + botão)
- `GET /api/data-lake-status` — quando cada bloco foi atualizado
- `GET /api/tempos?live=1` — força cálculo ao vivo, ignorando o lake

## Endpoints

| Rota | Auth | O que faz |
|---|---|---|
| `GET /health` | — | status + variáveis de ambiente |
| `GET /pedidos-venda` | — | **Fonte de Dados REST do SE** (a razão de existir) |
| `GET /sa-readonly-by-cnpj` | senha | pedidos SA por CNPJ (lake-first) |
| `GET /listar-workflows`, `/api/workflows` | senha | processos de crédito abertos no SE |
| `GET /consultar-sa`, `/consultar-sa-grupo`, `/api/pedidos-sa` | senha | detalhe SE+SA de 1 workflow (lupa), com grupo econômico |
| `GET /api/painel-bundle` | senha | payload consolidado do painel |
| `GET/POST /api/situacao-credito` | senha | lê/grava a situação por `idprocess` (estado do agente, no banco-mana) |
| `GET /api/totais-financeiro`, `/api/usos-semente`, `/api/atividades`, `/api/tempos`, `/api/gaps-sem-cre` | senha | agregados do painel (lake-first) |
| `GET /painel`, `/painel-reais` | `?senha=` | painéis HTML (somente leitura / carteira consolidada) |

## Variáveis de ambiente

`SE_URL`, `SE_API_KEY` (JWT) · `SA_BASE_URL`, `SA_USERNAME`, `SA_PASSWORD`, `SA_SAFRA_ID`, `SA_GRUPO_ID` · `BANCO_MANA_URL` · `PAINEL_SENHA`.

IDs fixos SA: safra 26/27 `69a5d85cae03f50036ee2531` · grupo Soja `610a8b743829fd00385c48c9`.

## ⚠️ Usuário dedicado no Simple Agro

O SA é **single-session**: quando o mesmo login entra em outro lugar, a sessão ativa cai (HTTP 452) e os requests em andamento morrem. O agente **precisa** de usuário/senha exclusivos da automação — um login manual de alguém durante o dia derruba a integração inteira. A cura estrutural desse problema é justamente o data lake.

## Deploy

`git push` → Railway auto-deploya em ~2 min. **Nunca `railway up`.** Validar por `/health` + log + teste funcional no painel.

## Cuidados ao mexer

- **Não voltar a gravar no SE.** Se pedirem "salva os pedidos no formulário", é a v2 de novo — leia a seção acima antes.
- **Falha não vira dado:** erro de transporte levanta exceção; lista vazia significa "não há pedidos", nunca "o SA recusou". Não persistir vazio no lake nem sobrescrever snapshot bom com falha.
- **Payload diz de quando é:** as respostas carregam `fonte` (lake/ao vivo) e timestamp — manter isso ao criar endpoint novo.
- O `README.md` do repo está **defasado** (descreve só o `/pedidos-venda`; o app tem 21 rotas, painel-reais e o data lake). Ao mexer, atualizar o README junto.
