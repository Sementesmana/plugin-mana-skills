---
name: agente-comercial
description: Bot WhatsApp dual-mode da Sementes Maná LTDA (N1, produção) — porta de entrada comercial no WhatsApp. Flask no Railway, sem banco próprio além do cadastro de usuários no banco-mana. Modo COMERCIAL: consulta preço, catálogo, frete e filtros no agente-precificacao por tools determinísticas + Claude rápido. Modo AGRÔNOMO: consultoria de soja sobre knowledge_base_agronomo.md com estratificação de modelos (classificação rápida, recomendação equilibrada, dúvida técnica no modelo forte). Recebe payload raw Z-API do agente-router (POST /webhook), responde texto e áudio TTS, e envia pela porta única do hub agente-whatsapp com classe conversacional + idempotency_key. Use SEMPRE no agente-comercial — modos, tools de precificação, knowledge base do agrônomo, estratificação de modelos, TTS, cadastro de usuários, /check-user, webhook do router. Também quando mencionar: bot comercial, dual-mode, mana-rapido/mana-equilibrio/mana-juridico, LLM_MODEL_AGRO_*, painel /admin, PRECIFICACAO_URL.
---

# agente-comercial — Bot WhatsApp dual-mode (preços + agrônomo)

> **N1, produção** · `https://agente-comercial-production.up.railway.app` · dono Xayer · comportamento **H (Harness)** no cockpit.

## O que é

Bot de WhatsApp para gestores e vendedores consultarem, em linguagem natural, **preço de semente** e **recomendação agronômica**. Um serviço, **dois modos**, escolhidos por detecção de palavra-chave normalizada (sem acento, porque o Whisper transcreve com acentuação correta e o texto digitado nem sempre).

- **Modo comercial** — Claude com *tools determinísticas* sobre a API do `agente-precificacao`: catálogo, preço, frete, filtros. O número nunca é inventado: vem da tool.
- **Modo agrônomo** — consultoria de soja usando `knowledge_base_agronomo.md` (393 linhas) como base.

## Estratificação de modelos (Harness, 19/06/2026)

Cada intenção paga o preço do seu julgamento — alias do `mana-llm-gateway`:

| Uso | Alias | Variável |
|---|---|---|
| Modo comercial | `mana-rapido` | `LLM_MODEL_COMERCIAL` |
| Agrônomo — classificar intenção | `mana-rapido` | `LLM_MODEL_AGRO_CLASSIF` |
| Agrônomo — recomendar variedade | `mana-equilibrio` | `LLM_MODEL_AGRO_RECOMENDA` |
| Agrônomo — dúvida técnica | `mana-juridico` | `LLM_MODEL_AGRO_DUVIDA` |

LLM roteado pelo **gateway** (`LLM_GATEWAY_URL` + `LLM_GATEWAY_KEY`), com fallback Anthropic direto se o gateway não estiver configurado. Ao mexer em modelo, mexer no alias — não em nome de modelo hardcoded.

## Áudio (ADR voz-whatsapp, 06/05/2026)

Quando a mensagem chega por áudio, o agente **prepend** uma instrução de formato: responder em 2–3 frases curtas, texto corrido, **sem markdown, tabela, bullet ou emoji** — porque a pessoa vai *ouvir*, não ler. Saída por TTS OpenAI (`TTS_VOZ`, `TTS_SPEED`, `TTS_LIMITE_CARACTERES`).

## Endpoints

| Rota | Auth | O que faz |
|---|---|---|
| `POST /webhook` | `WEBHOOK_SECRET` · rate limit 60/min | recebe payload **raw Z-API** repassado pelo `agente-router` |
| `GET /check-user?phone=` | — | o router pergunta se o número é cadastrado antes de rotear o DM |
| `GET /admin` | `?senha=` | painel de cadastro de usuários (HTML inline) |
| `GET/POST /api/usuarios`, `DELETE /api/usuarios/<phone>` | `PAINEL_SENHA` | CRUD de usuários autorizados |
| `GET /health` | — | status + checagem do banco |

## Variáveis de ambiente

Obrigatórias (fail-fast no startup): `BANCO_MANA_URL`, `PRECIFICACAO_URL`, `ANTHROPIC_API_KEY`, `ZAPI_BASE_URL`.
Demais: `PRECIFICACAO_USER`/`PASS` (conta de serviço), `AGENTE_WHATSAPP_URL` + `AGENTE_WHATSAPP_API_KEY` (porta única), `ZAPI_TOKEN`/`ZAPI_CLIENT_TOKEN` (fallback), `OPENAI_API_KEY` + `TTS_*`, `LLM_GATEWAY_*` + `LLM_MODEL*`, `PAINEL_SENHA`, `WEBHOOK_SECRET`.

## ⚠️ Dívida conhecida — fallback Z-API direto

O envio prioriza a **porta única** (`POST {AGENTE_WHATSAPP_URL}/send-whatsapp` com `X-API-Key` e payload `classe: conversacional` + `idempotency_key` + `agente: agente-comercial`), mas ainda existe **fallback chamando a Z-API direto** (`/send-text`, `/send-audio`), marcado como transição "Onda 1.5" (ADR 13/06). Isso **contraria** a regra do `mana-arquitetura-padrao` (proibido Z-API direto). Ao mexer no envio, tratar a remoção do fallback como o caminho — não estendê-lo.

## Sobreposição com o agente-agronomo

O modo agrônomo daqui e o `agente-agronomo` (bot dedicado, com TTS onyx e portfólio de 20 cultivares) cobrem terreno parecido. **Antes de evoluir a knowledge base daqui, confirmar com o Xayer qual é o canônico** — duplicar conhecimento agronômico em dois repos é drift garantido.

## Deploy

`git push` → Railway (~2 min). Nunca `railway up`. Gunicorn 1 worker, timeout 60. Validar por `/health` (traz `db_ok`) + teste real no WhatsApp.
