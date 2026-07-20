---
name: agente-agronomo
description: Bot WhatsApp agronomo especialista em soja da Sementes Mana LTDA. Flask + Railway que recebe relay do agente-router em grupos de agronomia, interpreta com Claude (claude-opus-4-6 via mana-llm-gateway) e responde com consultoria tecnica do portfolio Mana (20 cultivares de 4 obtentoras parceiras Neogen/SoyTech/Genetica Soy/Stine). Recomendacao assertiva de 1 variedade, posicionamento por microrregiao, resistencia a nematoides (cisto, galha), tecnologias Bt (IPRO, I2X, CE/Conkesta). TTS local com voz onyx + cadencia de codigos no audio (preparar_para_audio + TTS_SPEED=0.90). Use SEMPRE em tarefas do agente-agronomo - system prompt, knowledge base, comportamento do bot, regras de recomendacao, portfolio, TTS, voz, cadencia, arquitetura. Tambem quando mencionar bot agronomo, agronomo Mana, variedade soja, cultivar, knowledge_base.md, nematoide, GM, IPRO, I2X, CONKESTA, NEO, ST, GNS, 76KA, 78KA, 80KA, 84KA, safrinha, cisto, galha, microrregiao M3 M4 M5 MATOPIBA, onyx, preparar_para_audio.
---

# agente-agronomo - Bot WhatsApp Agronomo Sementes Mana

Bot WhatsApp que atende vendedores internos com consultoria tecnica sobre variedades de soja.
Recebe mensagens via agente-router -> Claude interpreta e responde como "Agronomo Mana".

## Producao

| Item | Valor |
|------|-------|
| URL Railway | `https://agente-agronomo-production.up.railway.app` |
| Endpoint webhook | `POST /webhook` (recebe raw Z-API do agente-router) |
| GitHub | `github.com/Sementesmana/agente-agronomo` |
| Branch | `main` |
| Modelo Claude | `claude-opus-4-6` (via mana-llm-gateway, alias `mana-juridico`) |
| Health | `https://agente-agronomo-production.up.railway.app/health` |

## Variaveis de ambiente (Railway)

| Variavel | Descricao |
|----------|-----------|
| ANTHROPIC_API_KEY | Chave Claude AI (fallback se LLM_GATEWAY_URL nao setado) |
| LLM_GATEWAY_URL | URL do mana-llm-gateway (ADR-0006) |
| LLM_GATEWAY_KEY | Chave virtual `agente-agronomo` no gateway |
| LLM_MODEL | Alias do modelo no gateway (default `mana-juridico` = claude-opus-4-6) |
| ZAPI_INSTANCE_ID | ID da instancia Z-API |
| ZAPI_TOKEN | Token da instancia Z-API |
| ZAPI_CLIENT_TOKEN | Security token da conta Z-API |
| GRUPO_AGRONOMO_IDS | IDs dos grupos agronomo (separados por virgula) |
| BOT_PHONE | Numero do bot (para nao responder a si mesmo) |
| OPENAI_API_KEY | TTS-1 outbound (voz). Sem chave -> fallback texto. |
| TTS_VOZ | Voz padrao. Default `onyx` (masculina grave). |
| TTS_LIMITE_CARACTERES | Threshold pra forcar texto. Default `800`. |
| TTS_SPEED | Velocidade TTS (0.25-4.0). Default `0.90`. Tunar 0.85/0.95 sem deploy. |

## Arquitetura

```
agente-router -> POST /webhook (raw Z-API payload, com origem_audio flag)
    |
    v
agente_agronomo.py
    |- processar_webhook(payload)
    |   |- fromMe=True em grupo -> ignora
    |   |- Grupo nao mapeado -> ignora
    |   `- Grupo mapeado -> _ask_claude(origem_audio) -> _send_message(origem_audio) -> Z-API
    |
    |- Claude API (claude-opus-4-6 via mana-llm-gateway)
    |   |- System prompt: identidade + regras de recomendacao
    |   `- Knowledge base: portfolio + microrregioes + nematoides + tecnologias
    |
    `- TTS local (OpenAI tts-1 -> Z-API /send-audio)
        |- _preparar_para_audio: regex cadencia de codigos
        `- speed=TTS_SPEED no payload
```

## Arquivos principais

| Arquivo | Funcao |
|---------|--------|
| `app.py` | Flask + endpoint /webhook + /health + /status + rate limiting |
| `agente_agronomo.py` | Logica: processar webhook, Claude, Z-API send, historico, TTS, cadencia |
| `data/knowledge_base.md` | Base de conhecimento: portfolio, microrregioes, nematoides, tecnologias |

## Voz no WhatsApp (ADR 2026-05-06 + cadencia 2026-06-02)

- Recebe `origem_audio` do payload do agente-router em `processar_webhook`
- TTS local via Z-API direto: `_send_text`, `_send_audio`, `_send_message(phone, msg, origem_audio)`
- Voz: `TTS_VOZ=onyx` (masculina grave, casa com tom tecnico de soja)
- Quando `origem_audio=True`, prepend `INSTRUCAO_AUDIO` ao user message -> Claude responde curto e narrativel
- Historico salvo SEM a INSTRUCAO_AUDIO -> evita contaminar turnos futuros
- Espelho condicional: texto -> texto sempre, audio + len<800 -> audio, audio + len>=800 -> fallback texto

### Cadencia de codigos no audio (2026-06-02)

`tts-1` nao suporta SSML, entao a cadencia depende de pontuacao e do parametro `speed`. Pra evitar que o audio atropele codigos (NEO761, ST711, 76KA72, etc):

- **`_preparar_para_audio(texto)`** aplica 3 regexes SO no payload TTS (texto WhatsApp continua intacto):
  - `_RE_NUM_ESPACO_TECH = r"(\d)\s+([A-Z]\d)"` - `761 I2X` -> `761, I2X`
  - `_RE_LETRA_DIGITO    = r"([A-Za-z])(\d)"`  - `NEO761` -> `NEO, 761`
  - `_RE_DIGITO_LETRA    = r"(\d)([A-Za-z])"`  - `I2X`    -> `I, 2, X`
- Resultado: `NEO761 I2X` -> audio "NEO, setecentos e sessenta e um, I, dois, X"
- **`TTS_SPEED=0.90`** (env) - global ~10% mais lento. Tunar `0.85`/`0.95` sem deploy.
- Nao toca em prosa: "400 mil sacas", "safra 23/24", "GM 7.6" passam intactos.

> ⚠️ TTS DESLIGADO em **agente-comercial** desde 2026-06-02 (DM modo-agronomo agora responde texto). Apenas o agronomo de GRUPO mantem voz.

## Portfolio de Variedades (20 cultivares)

| Variedade | GM | Tecnologia | NCisto | NGalha | Destaque |
|-----------|-----|-----------|--------|--------|----------|
| NEO680 IPRO | 6.8 | IPRO | S | S | Safrinha garantida |
| NEO690 I2X | 6.9 | I2X | R | S | Alto potencial I2X |
| NEO700 I2X | 7.0 | I2X/STS | R | S | Safrinha + STS |
| ST711 I2X | 7.1 | I2X | R | S | Campea Liga I2X |
| 76KA72 | 7.4 | CE | R | S | Conkesta E3 |
| ST745 I2X | 7.4 | I2X | R | S | Abertura de plantio |
| NEO780 CE | 7.5 | CE | R | S | Ampla adaptacao |
| NEO760 CE | 7.6 | CE/STS | R | - | STS tolerante |
| NEO761 I2X | 7.6 | I2X | R | - | Maior PMG M3 |
| NEO771 I2X | 7.7 | I2X | R | S | Alto potencial |
| 78KA42 | 7.8 | CE | R | S | Acamamento R |
| NEO790 IPRO | 7.8 | IPRO | S | S | Plantio cedo |
| NEO791 CE | 7.9 | CE | R | S | Pacote sanitario |
| GNS 7901 IPRO | 7.9 | IPRO | R | MR | Galha MR |
| NEO800 I2X | 8.0 | I2X | S | - | Alta tecnologia |
| NEO802 I2X | 8.0 | I2X | S | S | Excelente arquitetura |
| 80KA72 | 8.0 | CE | R | S | Raiz agressiva |
| NEO821 I2X | 8.2 | I2X | S | S | Alto potencial |
| ST828 I2X | 8.2 | I2X | S | S | Ampla adaptacao |
| 84KA92 | 8.4 | CE | R | MR | Ambientes restritos |

> ⚠️ REGRA ABSOLUTA: bot recomenda SOMENTE variedades desta lista.
> Nunca inventar nomes. NCisto S = Suscetivel, R = Resistente, MR = Mod. Resistente.

## Regras do System Prompt (comportamento do bot)

- **Maximo 1 variedade** por recomendacao. So 2 se perfis claramente distintos.
- **Perguntar antes** se nao tiver: estado/municipio, maior desafio, GM preferido.
- **Nunca comparar** com cultivares de outras empresas.
- Respostas curtas (max 250 palavras), formato WhatsApp (*negrito*, bullet).
- Nunca usar # ou ## (WhatsApp nao renderiza).

## Historico de conversas (memoria)

- Armazenado em memoria (dict `_conversations`) - TTL 1h, max 20 mensagens.
- Chave: `phone` do remetente (por remetente, mesmo em grupo).
- Sem persistencia em banco - LGPD compliant.

## Rate limiting

- 20 mensagens/hora por remetente (`_check_rate_limit`)
- 120 req/min por IP via flask-limiter (global)

## Como atualizar a knowledge base

1. Editar `data/knowledge_base.md` no ORQUESTRADOR
2. `git add data/knowledge_base.md && git commit -m "kb: atualizacao" && git push origin main`
3. Railway redeploya -> bot recarrega KB no proximo startup

## Como ajustar o comportamento do bot

Editar `agente_agronomo.py` -> constante `SYSTEM_PROMPT`. Partes editaveis:
- Regras de recomendacao (secao REGRA DE RECOMENDACAO)
- Estilo de resposta (secao Estilo de resposta)
- Informacoes que deve coletar antes de recomendar

## Como ajustar cadencia/velocidade do audio

Sem mexer em codigo - so env no Railway:
- `TTS_SPEED=0.85` - mais lento
- `TTS_SPEED=0.95` - mais rapido
- `TTS_VOZ=alloy|onyx|nova|echo|fable|shimmer` - trocar voz

## Erros conhecidos e solucoes

| Sintoma | Causa | Solucao |
|---------|-------|---------|
| Bot inventa variedades | KB desatualizada ou system prompt fraco | Atualizar knowledge_base.md + reforcar regra |
| Bot recomenda 2+ variedades quando 1 basta | System prompt permissivo | Reforcar "maximo 1 variedade" no SYSTEM_PROMPT |
| Bot nao responde no grupo | GRUPO_AGRONOMO_IDS errado | Verificar ID nos logs: "grupo nao mapeado: phone=..." |
| Bot nao responde em DM | DM modo-agronomo cai no agente-comercial (dual-mode), responde em texto | Pra mudar DM, mexer no agente-comercial |
| TypeError proxies no startup | anthropic versao antiga | requirements.txt: anthropic==0.49.0 |
| Mensagens duplicadas | Z-API retry por timeout | Fix esta no agente-router (fire-and-forget) |
| Audio atropela numeros do codigo | tts-1 sem SSML le digitos colados rapido | Verificar TTS_SPEED=0.90; `_preparar_para_audio` ja cadencia |
| Audio muito lento | TTS_SPEED muito baixo | Subir pra 0.95 ou 1.0 |
| TTS nao envia, so texto | OPENAI_API_KEY ausente ou invalida | Ver logs `[TTS] OPENAI_API_KEY ausente - fallback texto` |

## Deploy

```bash
cd ORQUESTRADOR/agente-agronomo
git add .
git commit -m "descricao"
git push origin main
# Railway auto-deploya em ~2 min
```
