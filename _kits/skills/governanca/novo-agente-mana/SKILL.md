---
name: novo-agente-mana
description: "Gerador de novos agentes/apps para Sementes Maná LTDA — Flask + Jinja2 + HTMX + Alpine.js + PostgreSQL + Railway, com integrações pré-prontas para SoftExpert (SOAP via softexpert-orchestrator), Simple Agro (REST), Claude (LLM) e Z-API (WhatsApp). Use SEMPRE que for criar agente novo, app, serviço, painel ou microsserviço no ecossistema Maná. Também use quando mencionar 'criar agente', 'novo app', 'novo serviço', 'scaffold', 'boilerplate', 'template de agente', 'começar do zero', ou ao perguntar qual linguagem/framework usar. Garante: identidade visual Maná (verde #1D6B3E + ouro #B8860B), autenticação JWT, deploy Railway, integração SoftExpert, defense-in-depth (padrão akita), testes e HTMX sem React."
---

# Novo Agente Maná — Gerador de Stack Padrão

Skill para criar **novos agentes/apps** no ecossistema Sementes Maná LTDA seguindo o stack consolidado, sem replicar decisões arquiteturais a cada novo projeto.

## Quando usar

- "Vou criar um novo agente para X" → use
- "Quero um app/serviço que faça Y" → use
- "Qual a estrutura inicial pra um novo microsserviço?" → use
- "Monta um scaffold/boilerplate pra…" → use
- "Qual linguagem/framework pra esse app novo?" → use (responda: Python + Flask/FastAPI + Jinja2 + HTMX)

## Filosofia do stack

**Princípio central:** todo agente Maná usa o MESMO stack para evitar fragmentação. Isso significa:

- **Backend:** Python 3.11+ (Flask ou FastAPI)
- **Templates UI:** Jinja2 (nunca HTML estático)
- **Interatividade:** HTMX + Alpine.js (nunca React/Vue/Angular, exceto casos muito específicos)
- **Banco:** PostgreSQL no Railway
- **ORM:** SQLAlchemy
- **LLM:** Anthropic SDK (Claude)
- **Deploy:** Railway com `railway.json` + Dockerfile
- **SoftExpert:** via `softexpert-orchestrator` (skill existente)
- **Simple Agro:** via client REST padronizado (`integrations/simple_agro.py`)
- **Navegação unificada:** via iframe no SoftExpert (não reinventar hub)

Por que NÃO PHP: fragmenta stack, ecossistema de IA/geoespacial pobre.
Por que NÃO Node.js: perde vantagem Python em IA/ML/geoespacial.
Por que NÃO React/Next.js por padrão: overkill; HTMX+Alpine resolvem 95% dos casos com 10% da complexidade.
Por que NÃO HTML estático: não escala, dados hardcoded, sem integração.

## Flask vs FastAPI — como escolher

| Critério | Escolha |
|---|---|
| Agente novo focado em **APIs REST** para outros sistemas consumirem | **FastAPI** |
| Agente com **muita UI** (painel rico, formulários, dashboards) | **Flask** |
| Agente que **processa assíncrono pesado** (Sentinel-2, OCR em lote) | **FastAPI** (async nativo) |
| Agente pequeno, CRUD simples | **Flask** (mais rápido de começar) |
| Quando em dúvida | **Flask** (consistência com agentes existentes) |

Todos os agentes atuais (estoque, financeiro-sa, agro, whatsapp, integracoes, nf, precificacao) usam Flask — escolha Flask para manter consistência, a menos que haja razão forte para FastAPI.

## Fluxo de criação

### Passo 1 — Levantar requisitos (pergunte ao usuário)

Antes de gerar arquivos, confirme:

1. **Nome do agente** (ex: `agente-contratos`, `agente-relatorios`)
2. **Propósito em 1 frase** (vai no README e no SKILL.md futuro)
3. **Integrações necessárias** — marque as aplicáveis:
   - [ ] SoftExpert (SOAP) — usa `softexpert-orchestrator`
   - [ ] Simple Agro (REST)
   - [ ] Anthropic Claude (LLM)
   - [ ] Z-API (WhatsApp)
   - [ ] PostgreSQL próprio
   - [ ] Outra API externa (qual?)
4. **Tem UI (painel web)?** [s/n] — se sim, Flask; se puramente API, considere FastAPI
5. **Framework:** Flask (default) ou FastAPI
6. **Tem webhook de entrada?** [s/n]
7. **Tem worker/cron?** [s/n] (se sim, adicionar APScheduler)

### Passo 2 — Gerar estrutura

Use o template em `templates/app/` como base. Copie para `/home/claude/<nome-agente>/` e substitua placeholders:

- `{{ AGENTE_NOME }}` — nome do agente (ex: `agente-contratos`)
- `{{ AGENTE_NOME_SNAKE }}` — snake_case (ex: `agente_contratos`)
- `{{ AGENTE_NOME_CAMEL }}` — CamelCase (ex: `AgenteContratos`)
- `{{ AGENTE_PROPOSITO }}` — frase de propósito
- `{{ AGENTE_TITULO }}` — título amigável do painel (ex: "Gestão de Contratos")

### Passo 3 — Customizar integrações

Remover módulos não usados. Se não tem WhatsApp, deletar `integrations/whatsapp.py`. Se não tem LLM, deletar `integrations/claude.py`. Menos código = menos superfície de ataque.

### Passo 4 — Entregar ao usuário

Use `present_files` para entregar um .zip ou os arquivos individuais. Dê instruções de:
1. Subir no GitHub (`Sementesmana/hiperautomacao-mana/<nome-agente>/`)
2. Criar projeto no Railway
3. Configurar variáveis de ambiente
4. Deploy automático no push

## Estrutura gerada

```
<nome-agente>/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Flask/FastAPI entrypoint
│   ├── config.py               # Carrega env vars
│   ├── api/                    # Endpoints REST (JSON)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── ui/                     # Rotas HTML (Jinja2)
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── services/               # Regras de negócio
│   │   ├── __init__.py
│   │   └── core.py
│   ├── integrations/           # Clients externos
│   │   ├── __init__.py
│   │   ├── softexpert.py       # SOAP via softexpert-orchestrator
│   │   ├── simple_agro.py      # REST Simple Agro
│   │   ├── claude.py           # Anthropic SDK
│   │   └── whatsapp.py         # Z-API
│   ├── models/                 # SQLAlchemy
│   │   ├── __init__.py
│   │   └── base.py
│   ├── auth/                   # JWT + SoftExpert SSO
│   │   ├── __init__.py
│   │   └── jwt_handler.py
│   └── workers/                # Tasks assíncronas (APScheduler)
│       ├── __init__.py
│       └── scheduler.py
├── templates/                  # Jinja2 templates
│   ├── base.html               # Layout Maná (verde/ouro)
│   ├── painel.html             # Painel principal
│   └── components/             # Componentes reutilizáveis
│       ├── kpi_card.html
│       ├── data_table.html
│       └── filter_bar.html
├── static/
│   ├── css/
│   │   └── mana.css            # Identidade visual
│   └── js/
│       └── mana.js             # HTMX + Alpine setup
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   └── test_integrations.py
├── Dockerfile
├── railway.json
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Padrões obrigatórios

### Segurança (defense-in-depth do akita)

- NUNCA commitar segredos; só via Railway env vars
- Validar TODO input com Pydantic (ou marshmallow se Flask)
- Rate limiting em endpoints públicos (flask-limiter)
- CORS restrito a domínios conhecidos
- Logs sem PII sensível (CPF/CNPJ mascarado: `***.***.***-45`)
- Auditoria de ações críticas em tabela `audit_log`

### Idempotência

- Endpoints POST críticos (criar workflow, enviar WhatsApp, gerar CPR) DEVEM ter `idempotency_key`
- Armazenar em tabela `idempotency_keys` com TTL 24h

### Graceful degradation

- Se SoftExpert cair → agente continua respondendo, retorna erro claro
- Se Simple Agro cair → usar cache stale com header `X-Cache-Stale: true`
- Nunca quebrar a UI por causa de integração offline

### Logs estruturados

Usar `structlog` ou JSON logging. Cada log tem: `timestamp`, `level`, `agente`, `request_id`, `user`, `action`, `duration_ms`, `status`.

## Identidade visual Maná

Definida em `static/css/mana.css`. Palette:

```css
:root {
  --verde: #1D6B3E;
  --verde-escuro: #134d2c;
  --verde-claro: #2a8a52;
  --ouro: #B8860B;
  --ouro-claro: #d4a017;
  --cinza-bg: #F5F3EF;
  --cinza-card: #FFFFFF;
  --texto: #1a1a1a;
  --texto-leve: #555;
  --vermelho: #C0392B;
  --azul: #1a5276;
  --border: #e0dbd0;
}
```

Tipografia: **Playfair Display** (títulos, 700/900) + **DM Sans** (corpo, 300/400/500/600).

Todo painel novo deve estender `templates/base.html` que já aplica header verde-escuro, tipografia, e reserva área para iframe do SoftExpert.

## Checklist antes de entregar

Antes de finalizar o scaffold para o usuário, verifique:

- [ ] `SKILL.md` do novo agente foi criado (pra depois adicionar em `/mnt/skills/user/`)
- [ ] `.env.example` lista todas as vars necessárias
- [ ] `requirements.txt` fixado com versões
- [ ] `railway.json` com start command correto
- [ ] `README.md` explica: propósito, arquitetura, deploy, env vars
- [ ] `Dockerfile` multi-stage (menor imagem)
- [ ] Endpoint `/health` retornando status das dependências
- [ ] Endpoint `/metrics` (Prometheus format) opcional
- [ ] Pelo menos 1 teste passa (`pytest`)
- [ ] `.gitignore` cobre `.env`, `__pycache__`, `*.pyc`, `.venv`

## Referências

Para templates dos arquivos gerados, consulte:

- `references/stack-decisions.md` — Justificativa completa das escolhas de stack
- `references/integrations-patterns.md` — Padrões para cada tipo de integração (SOAP, REST, LLM, webhook)
- `references/ui-patterns.md` — Padrões HTMX + Alpine.js + Jinja2 para interatividade rica sem React

Para os arquivos-template que serão copiados, consulte:

- `templates/app/` — Código Python padrão
- `templates/templates/` — HTML Jinja2
- `templates/static/` — CSS/JS
- `scripts/scaffold.py` — Script Python que gera o agente (use como referência de como substituir placeholders)

## Integração com skills existentes

Este skill trabalha em conjunto com:

- **softexpert-orchestrator** — TODO agente novo que fala com SoftExpert usa esta lib. Não reimplementar SOAP.
- **akita** — TODO agente novo segue os princípios de defense-in-depth, multi-model consensus (quando aplicável), idempotência, graceful degradation.
- **skill-creator** — Depois de criar o agente, criar um SKILL.md específico do novo agente usando skill-creator.

## Anti-patterns (não faça)

- ❌ Criar agente em PHP, Node, Ruby (fragmenta stack)
- ❌ Começar com Next.js/React "por via das dúvidas" (YAGNI)
- ❌ HTML estático com dados hardcoded (não escala)
- ❌ Criar painel sem estender `templates/base.html` (perde identidade visual)
- ❌ Chamar SoftExpert SOAP direto sem usar `softexpert-orchestrator`
- ❌ Commitar `.env` ou qualquer segredo
- ❌ Pular testes ("depois eu faço")
- ❌ Deploy fora do Railway "porque sim" (exceto se houver razão técnica documentada)
- ❌ Reinventar autenticação (use JWT + SSO SoftExpert padrão)
                                                                                                                                                                                                                                                                                                                                                                                           