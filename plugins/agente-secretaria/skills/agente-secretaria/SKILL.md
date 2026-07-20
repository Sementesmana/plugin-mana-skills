---
name: agente-secretaria
description: >
  Assistente executiva de agenda por áudio/texto no WhatsApp — Sementes Maná LTDA.
  Serviço Flask no Railway que recebe relay do agente-router (keyword secretaria/agenda/reunião),
  interpreta o pedido com Claude, consulta a agenda compartilhada do Google Calendar (conta
  smana.comercial via OAuth2 refresh token) e agenda direto se livre / sugere horários se ocupado;
  responde sempre em texto. Tem cadastro de contatos (nome+email+WhatsApp+pode_comandar) que amarra
  autorização (allowlist), participantes dos eventos e o resumo diário individual.
  Use esta skill SEMPRE que precisar trabalhar com o agente-secretaria — ajustar interpretação NLP,
  integração Google Calendar (criar/editar/cancelar/free-busy), CRUD de contatos, allowlist, lembrete
  diário, ou roteamento da keyword no router. Também quando mencionar: secretária, agenda por voz,
  Google Calendar Maná, agendar reunião WhatsApp, pode_comandar, seed_contatos, resumo diário, OAuth
  refresh token smana.comercial, painel-contatos.
---

# agente-secretaria — Assistente de Agenda por WhatsApp

Serviço Flask no Railway. Você manda áudio/texto começando com "Secretária/Agenda/Reunião"; o
agente-router transcreve (Whisper) e relaya; este serviço interpreta com Claude e mexe na agenda
compartilhada do Google da conta `smana.comercial`. Resposta sempre em texto.

## Produção

| Item | Valor |
|------|-------|
| URL Railway | `https://agente-secretaria-production.up.railway.app` |
| GitHub | `github.com/Sementesmana/agente-secretaria` |
| Health | `https://agente-secretaria-production.up.railway.app/health` |
| Painel contatos | `https://agente-secretaria-production.up.railway.app/painel-contatos` |

## Fluxo

```
Áudio/texto WhatsApp → Z-API → agente-router (transcreve + relay keyword "Secretária/Agenda/Reunião")
   → agente-secretaria /webhook (allowlist por cadastro → Claude NLP → Google Calendar)
   → agente-whatsapp /send-whatsapp (resposta em TEXTO)
```

## Capacidades

- **Agendar**: cria evento; se horário ocupado, sugere próximos livres (free/busy). Inclui o
  solicitante como participante. Não duplica (idempotência por título+início).
- **Cancelar / Remarcar**: busca por texto numa janela e age.
- **Consultar/Listar**: agenda do dia, filtrada pelo e-mail de quem perguntou.
- **Lembrete diário** (APScheduler, 06:30 BRT): resumo individual aos contatos `pode_comandar`.

## Cadastro de contatos (amarra tudo)

Tabela `contatos` (schema `secretaria` no banco-mana): `nome, email, telefone, cargo, pode_comandar`.
- `pode_comandar=True` → comanda pelo zap (allowlist) + recebe lembrete diário.
- `email` → participante dos eventos (convite Google) + filtro do resumo individual.
- Match de telefone tolerante: últimos 8 dígitos (resolve DDI e o "9" extra dos celulares BR).
- Seed inicial: `seed_contatos.json` (auto-load se tabela vazia). Painel `/painel-contatos`.

## Estrutura de arquivos

```
agente-secretaria/
├── app.py                  Flask: /webhook, /painel-contatos, /api/contatos, /cron/lembrete, /health
├── agente_secretaria.py    Orquestração (agendar/cancelar/remarcar/listar) + resumo por pessoa
├── nlp.py                  Claude interpreta intenção+dados (temperature=0)
├── google_calendar.py      Cliente Calendar (OAuth2 refresh token)
├── contatos.py             CRUD + allowlist + match de telefone tolerante + seed
├── whatsapp.py             Envio via hub agente-whatsapp
├── scheduler.py            Lembrete diário
├── seguranca.py            Mascaramento PII, rate limit, validação de entrada
├── config.py               Env vars + validação no startup (fail fast)
├── templates/painel_contatos.html
├── tests/test_basico.py
├── requirements.txt        (httpx fixado em 0.27.2!)  railway.json  Procfile  .env.example
└── seed_contatos.json
```

## Segurança (akita) + LGPD

- Bearer no `/webhook`; allowlist por `pode_comandar`; senha no painel/api (header, constant-time);
  rate limit por remetente e por IP; validação de entrada; `DB_SCHEMA` validado.
- Logs mascaram PII. Dados pessoais: e-mail, telefone, conteúdo de compromissos.
- Detalhes e decisões: ver nota `ManaVault/06-Agentes-e-Skills/agente-secretaria.md` e ADR
  `2026-05-26-agente-secretaria-assistente-agenda`.

## Roteamento no agente-router

Envs no router: `SECRETARIA_BOT_URL=<url>` + `SECRETARIA_BOT_SECRET=<= ROUTER_SECRET da secretária>`.
Keyword no início da mensagem: secretaria / secretária / agenda / reunião / reuniao.
