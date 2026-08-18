---
name: agente-recebimento-pedidos
description: >-
  Bot WhatsApp da Sementes Maná que gera relatórios visuais do Painel Comercial
  SA no DM. Flask + Pillow no Railway, sem IA. Lê o /api/dataset do
  agente-financeiro-sa (read-only) e tem 2 modos: (5) Recebimentos — infográfico
  PNG da safra (Visão Geral, por Mês com donut de %, por Período, Foco e Ação);
  (6) Vendedores — lista ranqueada por receita e, escolhido o número, um PDF
  paginado drill-down do vendedor (KPIs + por Cliente → por Pedido com status,
  bags, receita, parcelas, total parc). Envia pela porta única do hub
  agente-whatsapp (/send-image PNG, /send-document PDF). Acionado pelas op 5 e 6 do menu do
  agente-router (ou keywords recebimentos/vendedores). Use SEMPRE em tarefas do
  agente-recebimento-pedidos — render PNG, agregação por mês/período/vendedor,
  /api/dataset, drill-down, opção 5 e 6 do menu, fonte embutida, status pills.
  Também: painel de recebimentos, relatório por vendedor, ranking de vendedores,
  drill-down cliente pedido, safra 26/27.
---

# agente-recebimento-pedidos

Bot WhatsApp que devolve no DM um **infográfico de recebimentos da safra** (PNG),
réplica do "Painel de Recebimentos" da Maná. Acionado pela **opção 5 do menu** do
`agente-router`. Sem IA.

## Produção

| Item | Valor |
|------|-------|
| URL Railway | `https://agente-recebimento-pedidos-production.up.railway.app` |
| GitHub | `Sementesmana/agente-recebimento-pedidos` |
| Health | `/health` |
| Disparo manual | `GET /gerar?token=<ROUTER_SECRET>&telefone=<num>` |

## Fluxo

```
DM "opções" → 5  → agente-router (pin + relay) → POST /webhook (Bearer)
   → lê /api/dataset do agente-financeiro-sa (READ-ONLY) [safra 26/27]
   → filtra status (aguardando aprovação / aprovado / integrado)
   → agrega parcela.valor por mês de vencimento + por período
   → render PNG (Pillow) → envia pela porta única do hub (/send-image)
```

Processa em background (responde 200 já — o router é fire-and-forget).

## Modos

- **Recebimentos (opção 5 / keyword "recebimentos"):** PNG do painel da safra
  (filtro de status `RECEB_STATUS`). `recebimentos.montar()` → `render.gerar_png()`.
- **Vendedores (opção 6 / keyword "vendedores"):** manda a **lista numerada** de
  vendedores (texto, ranqueada por receita, **todos os status**) e guarda a lista
  em estado in-memory (TTL 600s); o usuário responde o **número** → **PDF paginado**
  drill-down daquele vendedor (vendedor grande tem muitos pedidos → PNG ficaria
  gigante, por isso PDF). `montar_vendedores()` / `montar_relatorio_vendedor(nome)`
  → `pdf_vendedor.gerar_pdf_vendedor()` → hub `/send-document`. Status colorido
  (INTEGRADO/APROVADO/AGUARDANDO). Requer `reportlab`.

## Arquivos

```
app.py            Flask: /health, /webhook (Bearer), /gerar (teste)
recebimentos.py   cliente /api/dataset + /api/safras + agregador
render.py         PNG (Pillow) — layout do painel; fonte/logo de static/
whatsapp.py       envio via hub (/send-image)
config.py         env + fail-fast (akita)
static/logo.png   logo Maná
static/fonts/     DejaVuSans.ttf + Bold (EMBUTIDA — Railway não traz fontes)
```

## Dados / regras

- Fonte: `GET {FINANCEIRO_SA_URL}/api/dataset?safra_id=` → `pedidos[{numero, cliente,
  vendedor, status, parcelas[{data_vencimento, valor}]}]`. Safra resolvida por nome
  em `/api/safras`.
- Valor = `parcela.valor` (frete embutido, regra do financeiro-sa). `status` já vem
  normalizado sem acento (`aguardando aprovacao` = `aguardando aprovação`).
- Visão Geral (Total Geral, Até Ago, Pedidos, Clientes, Parcelas), Recebimentos por
  Mês (valor + % + donut), por Período (3 blocos = 100%), Foco e Ação (texto fixo via
  `FOCO_ACAO_TEXTO`, negrito com `**...**`), rodapé.

## Variáveis de ambiente

`ROUTER_SECRET` (Bearer; = `RECEBIMENTOS_BOT_SECRET` no router) ·
`FINANCEIRO_SA_URL` · `RECEB_SAFRA_NOME` (26/27) ·
`RECEB_STATUS` (CSV) · `AGENTE_WHATSAPP_URL` (**hub `-eac3`**) +
`AGENTE_WHATSAPP_API_KEY` (= `WEBHOOK_SECRET` do hub) · `FOCO_ACAO_TEXTO` (opcional).

## Gotchas (do smoke test 2026-06-24)

- **`/send-image` deu 404** → `AGENTE_WHATSAPP_URL` tem que ser a do hub
  `https://agente-whatsapp-production-eac3.up.railway.app` (com `-eac3`).
- **Acentos/ícones viravam tofu** no Railway → a fonte DejaVu precisa estar
  **embutida** em `static/fonts/` (o ambiente não traz fontes do sistema).

## Roteamento no agente-router

Envs no router: `RECEBIMENTOS_BOT_URL` + `RECEBIMENTOS_BOT_SECRET`. Opção 5 do menu
(`_menu_escolher`) + keyword "recebimentos" → `_relay_recebimentos` → este `/webhook`.

## Segurança (akita) + LGPD

Bearer no `/webhook`, rate limit por remetente, dedup por `messageId`. **Sem PII**:
imagem só com totais agregados; logs sem nome de cliente. Sem LLM. **Não modifica**
o agente-financeiro-sa (dono: Dayan) — só consome read-only.

## Decisões

ADR `ManaVault/08-Decisoes/2026-06-24-agente-recebimento-pedidos.md`. Nota
`ManaVault/06-Agentes-e-Skills/agente-recebimento-pedidos.md`.
