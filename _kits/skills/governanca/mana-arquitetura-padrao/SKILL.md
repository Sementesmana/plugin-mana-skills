---
name: mana-arquitetura-padrao
description: Padrão de arquitetura OBRIGATÓRIO da Sementes Maná para qualquer agente/app/solução que usa Claude e/ou manda WhatsApp. Use SEMPRE ao criar solução nova, fazer scaffold/boilerplate, ou migrar uma existente — garante (1) LLM roteado pelo mana-llm-gateway (custo por chave virtual no cockpit, com fallback), (2) WhatsApp pela porta única do hub agente-whatsapp (classe + idempotency_key + campo agente, proibido Z-API direto), (3) dedup por requisição e não por conteúdo. Também use quando mencionar: novo agente Maná, novo-agente-mana, scaffold, migrar custo LLM, colocar no gateway, contabilizar custo, entrar no painel/cockpit, origem na fila, coluna Agente, mana-llm-gateway, chave virtual, LLM_GATEWAY_URL/KEY/MODEL, porta única, outbox, /send-whatsapp, /send-document, classe conversacional/transacional/massa, idempotency_key, dedup, pool de números, Onda 2, prompt caching no gateway, web_search no gateway, aliases mana-rapido/mana-equilibrio/mana-juridico.
---

# Arquitetura padrão — soluções Maná (LLM pelo gateway + WhatsApp pela porta única)

Regra vinculante (ADR 2026-06-13). **Toda solução nova (agente, app, painel, atividade-SE) que usa Claude e/ou WhatsApp já nasce parametrizada assim**; ao migrar uma existente, aplicar o mesmo. Objetivo: **todo gasto de LLM e todo envio de WhatsApp entram no nosso cockpit** (custo por solução + fila com origem). **Confirmar sempre contra o repo GitHub** (folder local pode estar em drift — já nos enganou: agente-nf/cpr locais estavam stale).

## Princípios (inegociáveis)
1. **LLM sempre pelo `mana-llm-gateway`** — chave virtual própria (custo por solução no cockpit) + **fallback** pra Anthropic direto. Nunca `api.anthropic.com` direto em produção.
2. **WhatsApp sempre pelo hub `agente-whatsapp`** (porta única) — proibido Z-API direto como caminho principal. Sempre com o campo **`agente`** no payload (origem na fila).
3. **Dedup por REQUISIÇÃO** (`idempotency_key` explícito), **nunca por conteúdo** (texto igual = envios legítimos diferentes).

## A) Custo LLM — rotear pelo gateway

**1. Criar chave virtual** (Console Railway do `mana-llm-gateway`) — `key_alias` = **nome exato da solução** (é o que agrupa no cockpit) e SEMPRE com `models` (allowlist; sem isso o cockpit não mostra o modelo). O console **não tem `curl`** — usar Python:
```bash
python3 - <<'EOF'
import os,urllib.request,json
port=os.environ.get('PORT','4000'); mk=os.environ['LITELLM_MASTER_KEY']
body=json.dumps({"key_alias":"agente-XXXX","max_budget":50,
                 "models":["mana-rapido","mana-equilibrio"]}).encode()  # só os aliases que a solução usa
req=urllib.request.Request(f'http://localhost:{port}/key/generate',data=body,
    headers={'Authorization':f'Bearer {mk}','Content-Type':'application/json'})
print('KEY:', json.loads(urllib.request.urlopen(req,timeout=20).read()).get('key'))
EOF
```

**2. Env no Railway da solução:**
`LLM_GATEWAY_URL=https://mana-llm-gateway-production.up.railway.app` · `LLM_GATEWAY_KEY=<sk- da chave>` · `LLM_MODEL=<alias>`
Aliases: `mana-rapido`=haiku · `mana-equilibrio`=sonnet · `mana-juridico`=opus.

> ⚠️ **GOTCHA `LLM_GATEWAY_URL` (queimou o pesquisador em 2026-06-14):** tem que ser a **raiz https://** (o SDK Anthropic anexa `/v1/messages` sozinho — **NÃO** ponha `/v1` no fim). Se o valor não começar com `https://` (placeholder colado por engano, espaço, texto de instrução) → `anthropic.APIConnectionError: Request URL is missing an 'http://' or 'https://' protocol`. **Copie o valor EXATO de uma solução já migrada** (ex.: agente-agronomo) em vez de digitar.

**3. Código — SDK base_url (preferido), com fallback + validação:**
```python
import os, anthropic

_GW_URL = os.environ.get("LLM_GATEWAY_URL", "").rstrip("/")
_GW_KEY = os.environ.get("LLM_GATEWAY_KEY", "")
USAR_GATEWAY = bool(_GW_URL and _GW_KEY)
# fail-fast: se setou o gateway, a URL TEM que ser http(s) (pega o gotcha no startup)
if USAR_GATEWAY and not _GW_URL.startswith(("http://", "https://")):
    raise RuntimeError(f"LLM_GATEWAY_URL invalida (sem http/https): {_GW_URL!r}")

if USAR_GATEWAY:
    client = anthropic.Anthropic(base_url=_GW_URL, api_key=_GW_KEY)
    MODELO = os.environ.get("LLM_MODEL", "mana-rapido")          # alias virtual
else:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    MODELO = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
resp = client.messages.create(model=MODELO, ...)
```
Dica: deixar os modelos como atributos de Config que viram **alias quando `USAR_GATEWAY`** e **modelo bruto** caso contrário — assim os call-sites não mudam. Alternativas (também com fallback): **rota OpenAI** `POST {URL}/v1/chat/completions` (Bearer key); **HTTP cru** `POST {URL}/v1/messages` (header `x-api-key`=key).

**4. Testar:** dispara 1x → `/spend/logs` do gateway mostra a entrada da chave e a solução aparece no cockpit.

✅ **Features avançadas — CONFIRMADAS passando pelo gateway (testado 2026-06-14):**
- **web_search** (`web_search_20250305`): passa via SDK base_url e via `/v1/messages`. Retorna `server_tool_use` + `web_search_tool_result` e o `usage` traz `server_tool_use.web_search_requests` (contabilizado).
- **prompt caching** (`cache_control`): passa — `cache_creation_input_tokens` na 1ª chamada vira `cache_read_input_tokens` na seguinte.
- Ou seja: pode migrar soluções que usam essas features sem deixar a chamada direta. (Custo de web_search ~US$ 0,01/busca soma ao custo de tokens.)

## B) WhatsApp — porta única pelo hub

**Env:** `AGENTE_WHATSAPP_URL=https://agente-whatsapp-production-eac3.up.railway.app` · `AGENTE_WHATSAPP_API_KEY=<WEBHOOK_SECRET do hub>`.

```python
import uuid, requests, os
NOME = "agente-XXXX"   # = key_alias; aparece na coluna Agente da fila do cockpit

def enviar_texto(telefone, mensagem):
    url = os.environ.get("AGENTE_WHATSAPP_URL","").rstrip("/"); key = os.environ.get("AGENTE_WHATSAPP_API_KEY","")
    if url and key:
        try:
            r = requests.post(f"{url}/send-whatsapp",
                headers={"X-API-Key": key, "Content-Type":"application/json"},
                json={"telefone": telefone, "mensagem": mensagem,
                      "classe": "conversacional",            # chat = síncrono; alerta = "transacional"; campanha = "massa"
                      "idempotency_key": uuid.uuid4().hex,   # único por requisição
                      "agente": NOME},                       # ORIGEM na fila (sem isso aparece "—")
                timeout=15)
            if r.status_code == 200: return True
        except Exception: pass
    # fallback Z-API direto (legado) — NUNCA como caminho principal
    ...
```
- **agente:** nome da solução (= `key_alias`). **Obrigatório** — popula a coluna *Agente* na fila do cockpit; sem ele a origem fica `—`. (Envio de template via SoftExpert o hub infere como `softexpert`.)
- **classe:** `conversacional` (resposta de chat → hub envia na hora + loga) · `transacional` (notificação/alerta → fila do worker) · `massa` (campanha → throttled; pool de números na Onda 2).
- **idempotency_key:** único por requisição; só repetir de propósito p/ idempotência real (ex.: id da mensagem inbound).
- **Áudio/PDF:** hoje o outbox só governa `/send-whatsapp`. `/send-document` e áudio entram no outbox na **Onda 2** (mudança no hub, não na solução).

## Checklist final
```
[ ] Chave virtual no gateway (key_alias = nome da solução, com models)
[ ] LLM_GATEWAY_URL (https:// raiz, SEM /v1) / LLM_GATEWAY_KEY / LLM_MODEL no Railway
[ ] Validação fail-fast: LLM_GATEWAY_URL começa com http(s)
[ ] LLM roteado pelo gateway + fallback (sem api.anthropic.com direto)
[ ] WhatsApp via /send-whatsapp com classe + idempotency_key + "agente": "<nome>" + fallback
[ ] Teste: /spend/logs mostra a chave; solução no cockpit (custo) e mensagem na fila com a coluna Agente preenchida
[ ] Nota da solução em ManaVault/06-Agentes-e-Skills/
```

## Referências no vault
- ADR padrão: `08-Decisoes/2026-06-13-padrao-llm-gateway-e-porta-unica-whatsapp.md`
- Runbook: `09-Runbooks/novo-agente-zap-claude-checklist.md`
- ADR outbox/Onda 2: `08-Decisoes/2026-06-13-mana-whatsapp-gateway-outbox-pool-numeros.md`
- Backlog de migração: `00-Inbox/2026-06-13-migracao-custo-llm-gateway-backlog.md`
