---
name: agente-secretaria
description: >
  Assistente executiva de agenda por áudio/texto no WhatsApp — Sementes Maná. Flask no Railway:
  agente-router relaya (keywords secretaria/secretário/agenda/reunião) → Claude interpreta com
  memória de conversa de 10 min (resolve follow-ups) → Google Calendar via OAuth2 da conta
  smana.comercial (agenda/cancela/remarca/lista) → responde em texto. Notifica o resumo do dia
  às 7h (silencia em dia vazio) + 1h antes de cada evento aos participantes cadastrados.
  Cadastro de contatos (nome+email+WhatsApp+pode_comandar) amarra autorização (allowlist),
  participantes dos eventos e o resumo diário individual. Use SEMPRE que trabalhar com o
  agente-secretaria — NLP, Google Calendar, CRUD de contatos, allowlist, memória de conversa,
  notificações matinal+pré-evento, roteamento da keyword no router. Também quando mencionar:
  secretária, secretário, agenda por voz, agendar reunião WhatsApp, pode_comandar, seed_contatos,
  lembrete pré-evento, OAuth refresh token smana.comercial, painel-contatos.
---

# agente-secretaria — Assistente de Agenda por WhatsApp (v1.6)

Serviço Flask no Railway. Você manda áudio/texto começando com "Secretária/Secretário/Agenda/
Reunião"; o agente-router transcreve (Whisper) e relaya; este serviço interpreta com Claude
(usando memória de conversa de curta duração) e mexe na agenda compartilhada do Google da conta
`smana.comercial`. Resposta sempre em texto. Avisa a agenda do dia de manhã (só se tiver evento)
e ~1h antes de cada compromisso.

## Produção

| Item | Valor |
|------|-------|
| URL Railway | `https://agente-secretaria-production.up.railway.app` |
| GitHub | `github.com/Sementesmana/agente-secretaria` |
| Health | `https://agente-secretaria-production.up.railway.app/health` |
| Painel contatos | `https://agente-secretaria-production.up.railway.app/painel-contatos` |

## Fluxo

```
Áudio/texto WhatsApp → Z-API → agente-router (transcreve + relay keyword)
   → agente-secretaria /webhook (allowlist por cadastro → carrega histórico de conversa
       → Claude NLP → Google Calendar) → agente-whatsapp /send-whatsapp (TEXTO)
```

## Capacidades

- **Agendar** — cria evento; se ocupado, sugere próximos livres (free/busy). Inclui o solicitante
  como participante (resolvido pelo número WhatsApp → cadastro). Idempotência por título+início.
- **Cancelar / Remarcar** — busca por texto numa janela e age.
- **Consultar/Listar** — agenda do dia, filtrada pelo e-mail de quem perguntou.
- **Memória de conversa** (v2, desde 2026-06-01) — in-memory por remetente, TTL 600s, cap 6 turnos.
  Permite follow-ups naturais: "Secretária, agenda reunião com Dayan" → bot sugere → "Secretária,
  pode ser às 15h" → bot fecha o agendamento com 15h. Router segue stateless: follow-ups precisam
  começar com a keyword.
- **Notificação matinal** (`LEMBRETE_HORARIO`, default 07:00) — resumo da agenda do dia, por
  pessoa (filtrado por e-mail). **Silenciosa em dia vazio** — silêncio sinaliza dia livre.
- **Lembrete pré-evento** (cron interval `VERIFICAR_PROXIMOS_MIN`, default 5 min) — avisa
  ~`LEMBRETE_ANTES_MIN` min antes (default 60) cada commander cujo e-mail é participante:
  *"⏰ Em ~60 min (HH:MM): título"*. Idempotência por event_id (cleanup > 2h).

## Cadastro de contatos (amarra tudo)

Tabela `contatos` (schema `secretaria` no banco-mana): `nome, email, telefone, cargo, pode_comandar`.
- `pode_comandar=True` → comanda pelo zap (allowlist) + recebe matinal e pré-evento.
- `email` → participante dos eventos (convite Google) + filtro do resumo individual + filtro do pré-evento.
- Match de telefone tolerante: igualdade, sufixo, ou últimos 8 dígitos (resolve DDI + "9" extra BR).
- Seed inicial: `seed_contatos.json` (auto-load se tabela vazia). Painel `/painel-contatos`
  (tela de login; senha via header X-Painel-Senha).

## Submenu numérico (URA) — desde 2026-06-23

Espelha o padrão do `agente-whatsapp-pa`. Disparado pela palavra `menu`/`opções` (o
agente-router manda `"menu"` quando o usuário escolhe "Secretária" no menu de topo).
**Tem prioridade sobre o NLP** em `processar_mensagem`:

- `1 Agendar` → **instrui** ("me diga com quem, dia e hora") e devolve ao fluxo livre (o NLP agenda).
- `2 Consultar agenda da semana` → **executa**: próximos 7 dias, filtrados pelo e-mail do solicitante.
- `3 Cancelar` → **lista numerada** dos compromissos da semana → usuário escolhe o número →
  **confirma** (sim/não) → cancela via `gcal.cancelar_evento`.
- Voltar ao menu de topo: **`opções`** (interceptado pelo router). `menu` reabre este submenu.
  O `0` saiu dos textos (decisão 2026-06-23).

Estado **in-memory** por remetente (`_menu_estado`, TTL 600s) — seguro porque o gunicorn roda
`workers=1`. **LGPD:** durante o fluxo de cancelar guarda só `id`+`título`+`horário`, nunca persiste.
Funções em `agente_secretaria.py`: `_tratar_menu`, `_menu_get/_set/_clear`, `_eventos_semana`,
`_fmt_semana`, `_strip_acentos`. Texto livre que não é número nem gatilho cai no NLP de sempre.

⚠️ **Ordem importa:** o submenu é avaliado ANTES do NLP. Ao mexer em `processar_mensagem`,
não inverta — senão "1" vira pedido de agendamento em linguagem natural.

## Estrutura de arquivos

```
agente-secretaria/
├── app.py                  Flask: /webhook, /painel-contatos, /api/contatos, /cron/lembrete, /health
├── agente_secretaria.py    Orquestração + submenu URA (_tratar_menu, _menu_get/_set/_clear,
│                           _eventos_semana, _fmt_semana) + helpers (_eventos_do_dia,
│                           _formatar_dia, resumo_para_lembrete, eventos_proximos,
│                           emails_de_evento, horario_evento)
├── nlp.py                  Claude interpreta intenção+dados (temperature=0, recebe histórico)
├── google_calendar.py      Cliente Calendar (OAuth2 refresh token)
├── contatos.py             CRUD + allowlist + match telefone + seed + destinatarios_lembrete
├── whatsapp.py             Envio via hub agente-whatsapp
├── scheduler.py            2 jobs APScheduler: matinal + pré-evento; idempotência in-memory
├── conversa.py             Memória de conversa in-memory por remetente (TTL+cap)
├── seguranca.py            Mascaramento PII, rate limit, validação de entrada
├── config.py               Env vars + validação no startup (fail fast)
├── templates/painel_contatos.html
├── tests/test_basico.py
├── requirements.txt        (⚠️ httpx fixado em 0.27.2 — compat anthropic 0.39)
└── seed_contatos.json
```

## Roteamento no agente-router

Envs no router: `SECRETARIA_BOT_URL=<url>` + `SECRETARIA_BOT_SECRET=<= ROUTER_SECRET da secretária>`.
Keywords (case-insensitive, no início da mensagem):
`secretaria / secretária / secretario / secretário / agenda / reunião / reuniao`.

## Segurança (akita) + LGPD

- Bearer no `/webhook`; allowlist por `pode_comandar`; senha no painel/api (header, constant-time);
  rate limit por remetente e por IP; validação de entrada; `DB_SCHEMA` validado.
- Logs mascaram PII. Dados pessoais: e-mail, telefone, conteúdo de compromissos, **conteúdo de
  conversa** (memória in-memory, TTL 600s, nada em disco/log).
- Decisões e detalhes nas notas:
  - ADR `2026-05-26-agente-secretaria-assistente-agenda` (v1 — desenho original)
  - ADR `2026-06-01-agente-secretaria-memoria-conversa` (v2 — memória de conversa)
  - ADR `2026-06-01-agente-secretaria-notificacoes-refinadas` (matinal silenciosa + pré-evento)
  - ADR `2026-06-23-router-menu-opcoes-dm` (submenu numérico URA + `opções` volta ao topo)
  - Nota `ManaVault/06-Agentes-e-Skills/agente-secretaria.md`
