---
name: agente-premiacao
description: >
  Bot semanal de premiação I2X da Sementes Maná LTDA. Flask + APScheduler no
  Railway que lê pedidos do Simple Agro (safra 26/27, grupo soja), aplica 2
  campanhas de ranking de consultores e envia 2 mensagens ao grupo de WhatsApp
  via agente-whatsapp, toda segunda 08h BRT. Use SEMPRE que precisar trabalhar
  com o agente-premiacao — ajustar regras das campanhas, filtros de venda/status,
  conversão de embalagem (scs200mil), lista de exclusão de pódium, cron, painel
  de conferência, ou enrichment do SA. Também quando mencionar: premiação,
  campanha I2X, mix I2X, ranking de consultores, 761I2X, scs200mil, BG 5.0M,
  gate 50%, meta global I2X, /api/ranking, /api/debug-distinct, /cron/disparar,
  VENDEDORES_EXCLUI_PODIUM, enrichment tecnologia/terceiro Simple Agro.
---

# Agente Premiação — Sementes Maná

Bot semanal que lê pedidos do Simple Agro, aplica 2 campanhas de premiação I2X
e envia 2 mensagens ao grupo de WhatsApp via agente-whatsapp (segunda 08h BRT).

## Infraestrutura

| Item | Valor |
|---|---|
| URL produção | `https://agente-premiacao-production.up.railway.app` |
| Repositório | `github.com/Sementesmana/agente-premiacao` (isolado) |
| Branch | `main` |
| Workers | **1** (cron interno APScheduler não pode duplicar) |
| Stack | Python 3.11 + Flask + Gunicorn + APScheduler + (PostgreSQL opcional) |
| Envio | via **agente-whatsapp** `/send-whatsapp` (NÃO Z-API direto) |

## Arquivos

```
agente-premiacao/
├── app.py               Flask + APScheduler + rotas + rate limit + token
├── agente_premiacao.py  Regras das 2 campanhas + formatadores das mensagens
├── sa_client.py         Cliente SA: login + get_orders + enrichment catálogo
├── whatsapp_client.py   Wrapper /send-whatsapp (payload {telefone, mensagem})
├── config.py            Carrega/valida env (não derruba processo; reporta faltas)
├── db.py                banco-mana opcional (schema premiacao: log de disparo)
├── migrations/001_init.sql
├── tests/test_regras.py Smoke test offline das regras
├── requirements.txt · Procfile · railway.json · .env.example · .gitignore
```

## Regras das 2 campanhas (validadas com dado real 2026-05-21)

**Filtros (ambas):** `tipo_venda ∈ {VENDA NORMAL, VENDA AGENCIADA}` e
`status ∈ {aguardando aprovação, integrado, aprovado, faturado, aguardando faturamento}`.
Itens com flag `terceiro` não contam (não filtrar por obtentora). Vendedores em
`VENDEDORES_EXCLUI_PODIUM` (default `SEMENTES MANA, GOAGRO`) ficam fora do pódium
mas somam na meta global.

**Conversão:** unidade `5.0 MIL S` → scs200mil `× 25`; já-scs `× 1`.
Embalagem desconhecida é sinalizada (não some silenciosamente).

**Meta global** (não trava, exibida no topo das 2 msgs): soma de I2X (toda a Maná)
vs `META_GLOBAL_SCS` (200.000). CONKESTA fica fora do mix e da meta.

- **Campanha 1 — Mix I2X:** `mix = I2X/(I2X+IPRO)` por vendedor. Pódium = `mix ≥ 50%`,
  ordenado por % desc (volume desempata). Abaixo de 50% não entra, mas mostra
  "mais próximos" (qtd + %).
- **Campanha 2 — Volume 761I2X:** ranking por volume vendido do cultivar `761I2X`
  (scs200mil), mesmos filtros, sem gate.

ATENÇÃO: O `/api/orders` do SA **não traz tecnologia/terceiro inline** — vêm do catálogo
(`/api/productgroups/{grupo}`). O `sa_client.enriquecer()` cruza os itens com o
catálogo. Sem isso, as campanhas zeram.

## Variáveis de ambiente

| Variável | Descrição | Default |
|---|---|---|
| `SA_USERNAME` / `SA_PASSWORD` | conta dedicada SA | — |
| `SA_SAFRA_ID` / `SA_GRUPO_ID` | safra 26/27 / grupo soja | no código |
| `AGENTE_WHATSAPP_URL` | hub outbound | — |
| `AGENTE_WHATSAPP_API_KEY` | = WEBHOOK_SECRET do agente-whatsapp | — |
| `PREMIACAO_GRUPO_ID` | groupId do grupo (vai no campo `telefone`) | — |
| `CRON_TOKEN` | auth de /cron/disparar e /admin/migrate | — |
| `PAINEL_SENHA` | auth /painel e /api/* | `mana2026` |
| `CRON_DIA`/`CRON_HORA`/`CRON_TIMEZONE` | mon / 08:00 / America/Sao_Paulo | default |
| `CRON_INTERNO_HABILITADO` | 1 liga o cron interno | `1` |
| `META_GLOBAL_SCS` | meta global I2X | `200000` |
| `TECH_I2X`/`TECH_IPRO`/`CULTIVAR_C2` | I2X / IPRO / 761I2X | default |
| `VENDEDORES_EXCLUI_PODIUM` | lista (vírgula), substring | `SEMENTES MANA, GOAGRO` |
| `GATE_MIX_PCT`/`TOP_N`/`PROXIMOS_N` | 0.50 / 0 (todos) / 5 | default |
| `FATOR_POR_EMBALAGEM` | override JSON conversão | — |
| `BANCO_MANA_URL` | log opcional | — |
| `DRY_RUN` | 1 = calcula sem enviar | `0` |

## Endpoints

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| GET | `/` | público | info |
| GET | `/health` | público | sempre 200; reporta `pode_enviar` e `faltando` |
| GET/POST | `/cron/disparar?token=` | CRON_TOKEN | calcula + envia (ou preview com `?enviar=0`) |
| GET | `/api/ranking?senha=` | PAINEL_SENHA | preview JSON das 2 campanhas (nunca envia) |
| GET | `/api/debug-distinct?senha=` | PAINEL_SENHA | valores distintos do SA (confirmar strings) |
| POST | `/admin/migrate?token=` | CRON_TOKEN | aplica schema premiacao |
| GET | `/painel?senha=` | PAINEL_SENHA | conferência (preview + botão disparar) |

## Operação

- **Testar sem enviar:** `DRY_RUN=1` + `/api/ranking` (ou `/cron/disparar?enviar=0`).
- **Conferir strings do SA:** `/api/debug-distinct?senha=` antes de mudar filtros.
- **Deploy:** `git push origin main` → Railway auto-deploya. Root Directory VAZIO.
- Decisão de origem: [[ManaVault/08-Decisoes/2026-05-21-agente-premiacao-drift-consciente]]
  (enrichment portado do agente-pedidos = drift consciente, migrar p/ endpoint depois).
