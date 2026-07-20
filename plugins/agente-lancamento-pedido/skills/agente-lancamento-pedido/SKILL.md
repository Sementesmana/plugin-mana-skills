---
name: agente-lancamento-pedido
description: Bot WhatsApp que lança pedidos de venda no Simple Agro com conversação multi-turno, checagem/cadastro de cliente, e confirmação obrigatória
tags: [whatsapp, pedido, simple-agro, lancamento, assistente-comercial, n2]
author: Sementes Maná LTDA
version: "1.0"
status: production
---

# agente-lancamento-pedido — Skill de Lançamento de Pedido via WhatsApp

**Bot de lançamento de pedido no Simple Agro por áudio/texto.**

## O que faz

Lança pedidos de venda completos no Simple Agro (cliente, propriedade, itens, frete, pagamento, parcelas) via WhatsApp com conversação em múltiplos turnos.

**Fluxo:**
1. Identifica cliente (busca/cria)
2. Seleciona propriedade e vendedor associado
3. Define frete (CIF/FOB) e garantia
4. Escolhe tipo de venda e forma de pagamento
5. Especifica uso e tabela de preço
6. Adiciona itens (múltiplos) com preço chumbado + TSI
7. Define parcelas (à vista ou prazo)
8. Confirma com a palavra exata **"confirmo"**
9. Gera PDF do espelho e envia via WhatsApp
10. Suporta cancelamento em qualquer estado

## Onde usar

- Entrada: Keyword no agente-router: **"assistente comercial"** (sticky 30min)
- Saída: Usa agente-whatsapp para enviar PDF
- Banco: schema `lancamento_pedido` no banco-mana (PostgreSQL)
- Operadores: cadastrados via painel admin (`/painel-admin`) com senha

## Decisões técnicas críticas

### Preço CHUMBADO (não tabela)
Valor falado entra direto como `preco_item` — **sem engine de juros, sem consulta à tabela**. O preço inteiro vai em `preco_germoplasma` (royalties=0) porque o SA exibe `total = royalties + germoplasma`.

### Bookmarklet de Sync
14 tabelas sincronizadas com produtos filtrados por **grupo_produto[].produtos** (não produtos na raiz). Bookmarklet no painel admin permite sincronizar de novos quando publicar tabela no SA — sem conta de serviço dedicada, usa o catálogo completo como fallback.

### Single-session mitigado
SA permite 1 sessão por usuário (`device_token`). O agente já re-loga automaticamente em 401. Solução definitiva: conta de serviço (`bot.comercial`) no SA.

## Variáveis de ambiente (Railway)

```
ROUTER_SECRET              # Bearer token do agente-router
BANCO_MANA_URL            # PostgreSQL connection string
ANTHROPIC_API_KEY         # Claude API
SA_USERNAME               # Credencial Simple Agro
SA_PASSWORD               # Senha SA
SA_SAFRA_ID               # SAFRA 26/27: 69a5d85cae03f50036ee2531
SA_GRUPO_ID               # Grupo Soja: 610a8b743829fd00385c48c9
AGENTE_WHATSAPP_URL       # URL do agente-whatsapp
AGENTE_WHATSAPP_API_KEY   # Token ZAPI do hub
PAINEL_SENHA              # Senha do painel admin (default: mana2026)
DRY_RUN                   # true/false (default true)
SA_FILIAL_ID              # ID da filial padrão
SA_TABELA_PRECO_ID        # ID tabela de preço padrão
CONVERSA_TTL_MIN          # TTL da sessão em minutos (default 60)
CLAUDE_MODEL              # claude-opus-4-6 ou haiku (default opus)
ZAPI_INSTANCE_ID          # Instância Z-API própria (se não usar hub)
ZAPI_TOKEN                # Token Z-API própria
ZAPI_CLIENT_TOKEN         # Client token Z-API própria
```

## Stack

- **Backend:** Python 3.11 + Flask + Gunicorn
- **Banco:** PostgreSQL (banco-mana, schema lancamento_pedido)
- **Deploy:** Railway (projeto isolado)
- **LLM:** Claude Opus 4.6 (extração) + Haiku (respostas)
- **Integração:** Simple Agro REST API + agente-router/whatsapp

## Endpoints

- `POST /webhook` — entrada do agente-router (Bearer token)
- `GET /painel-admin` — painel de operadores (PAINEL_SENHA)
- `GET|POST /api/operadores` — CRUD operadores (PAINEL_SENHA)
- `DELETE /api/operadores/<id>` — remove operador
- `GET /api/sessoes` — lista conversas ativas (PAINEL_SENHA)
- `GET /api/audit` — trilha de ações (PAINEL_SENHA)
- `GET|POST /api/sync-tabelas` — sincroniza tabelas de preço
- `GET /api/tabelas-status` — status do cache (PAINEL_SENHA)
- `GET /health` — status do serviço

## Fluxo no painel admin

1. **Cadastrar operadores:** WhatsApp + nome (vai na observação do pedido)
2. **Sincronizar tabelas:** Clica bookmarklet no painel SA → cria/atualiza cache
3. **Monitorar conversas:** Vê estado+dados da sessão por telefone
4. **Audit log:** Vê pedidos criados/cancelados, clientes cadastrados

## Regras de negócio

1. Cliente precisa estar **na carteira do vendedor** antes de ter pedido (read-modify-write PUT)
2. Frete incluso → dedução = frete ÷ bags, subtrai do preço (germoplasma absorve)
3. Confirmação dura: só a palavra exata **"confirmo"** (código puro, sem LLM)
4. Nome do operador gravado na observação (rastreabilidade)
5. Allowlist: só operador cadastrado no painel usa o bot

## Gotchas (não re-investigar)

⚠️ **price-table.mobile magro:** API nunca devolve `produtos` fora do app rodando — mesmo token/headers/IP via curl/requests/fetch-console recebem versão vazia. Solução: bookmarklet ou não depender de preços de tabela (arquitetura chumbado resolveu isso).

⚠️ **Single-session:** Login do agente derruba painel do mesmo usuário. Mitigado com re-login automático em 401. Solução real: conta de serviço.

## Pendências pós-lancamento

- [ ] Repo `Sementesmana/agente-lancamento-pedido` + projeto Railway isolado
- [ ] Keyword "assistente comercial" no agente-router + env vars
- [ ] Validar `observacao` no POST /api/orders (capturado só em cancelamento)
- [ ] Parcelas à prazo no PUT /payment (à vista validado ✅)
- [ ] Conta de serviço SA (bot.comercial) — resolve single-session e sync
- [ ] ADR consolidando decisões 2026-06-04

## Suporte

**Em produção desde:** 2026-06-04 (pedido real #260000040078 validado E2E)
**Última revisão:** 2026-06-04 (sync de tabelas + atualização vault)
**Estado:** ✅ Produção (com catálogo completo — sync opcional)
