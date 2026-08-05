---
name: agente-bartermanager
description: Barter Manager — app de gestão de barter (permuta insumo × grão) da Sementes Maná. Flask + SQLAlchemy no schema barter do banco-mana (Railway); 40 tabelas em 7 domínios, 224 rotas, 79 testes. Cobre parceiros (contas, propriedades, avalistas), contratos de compra/venda (locais de entrega, embarques, faturamentos, ocorrências, pagamentos, audit), pedidos com filhos polimórficos, cotações barter versionadas, lavoura (assessores, CPRs, visitas, fotos) e expedição. Migrado de Node/Express para Flask em 2026-08-03 via strangler pattern. Use SEMPRE em tarefas do agente-bartermanager — endpoints, blueprints, models, saldo de embarque/faturamento, cod sequencial, versionamento de cotação, schema barter, deploy. Também quando mencionar barter, permuta insumo por grão, CPR de lavoura, local de entrega, total_embarcado, total_transferido, pedido polimórfico, cotação barter, expedição de carga, filho_blueprint.
---

# Barter Manager (agente-bartermanager)

App de gestão de operações de **barter** — permuta de insumo por grão. Cobre o ciclo: cadastro do parceiro produtor, contrato de compra do grão, locais de entrega e embarques, faturamento (NF), pedidos, cotações barter, acompanhamento de lavoura (CPRs e visitas) e expedição de carga.

- **Repo:** `Sementesmana/agente-bartermanager` (privado)
- **Produção:** https://agente-bartermanager-production.up.railway.app
- **Tipo/nível:** `app` · N1 (sistema de registro) · autoridade: registra
- **Dono:** hub construiu; handoff **variação C** para Pablo Santana

## Origem — migração Node → Flask (strangler pattern)

App nasceu fora da estrutura Maná (Node/Express + front `index.html` monolítico de 7.292 linhas) e foi trazido em **2026-08-03**.

A migração usa **strangler pattern**: Node e Flask rodam no mesmo banco, com o mesmo `JWT_SECRET` e HS256 — um token emitido por qualquer um é aceito pelo outro, e o front não precisa saber quem respondeu. Isso permitiu migrar domínio por domínio sem downtime.

**Estado atual:** núcleo de dados 100% migrado (7/7 domínios, 224 rotas, 79 testes). O Node legado segue em `legado/` como referência.

## Estrutura

```
agente-bartermanager/
├── app/
│   ├── __init__.py        app factory + /api/status + CLI
│   ├── config.py          fail-fast de JWT/banco + search_path do schema
│   ├── auth.py            JWT + bcrypt (compatível com o Node)
│   ├── crud.py            FÁBRICAS: crud_blueprint + filho_blueprint
│   ├── blueprints/        autenticacao · cadastros · parceiros · contratos
│   │                      pedidos · lavoura · cotacoes
│   └── models/            40 tabelas em 7 módulos de domínio
├── migrations/001_integridade.sql
├── tests/                 79 testes (SQLite in-memory)
├── docs/                  ANALISE_DADOS.md — auditoria do schema
├── legado/                Node + front antigo (referência)
└── wsgi.py · requirements.txt · Procfile · railway.json · .env.example
```

## As duas fábricas — leia antes de escrever endpoint novo

**`crud_blueprint(nome, model, permitidos, url_prefix=...)`** — CRUD de recurso raiz. Contrato idêntico ao `crudRouter()` do Node: `GET /` com filtro `?q=`, `GET /<id>` com 404, `POST` que preenche `cod` com o id quando vem vazio, `PUT` que devolve `{}` se o id não existe, `DELETE` que sempre devolve `{"deleted": true}`.

**`filho_blueprint(nome, model, permitidos, url_prefix=..., pai_campo=..., metodos=..., auditar_pai=...)`** — recurso aninhado `/api/<pai>/<pid>/<filho>`. Cobre o padrão que se repete em todo o app:

- lista filtrando por `pai_campo`
- cria já com o pai preenchido (**não dá pra sequestrar o pai pelo corpo** — vem da URL)
- `GET /<id>` e `PUT` respeitam o **escopo do pai** (filho de outro pai → 404 / `{}`)
- `metodos=(...)` recorta o que expõe (ex.: contas bancárias não têm PUT — fiel ao Node)
- `auditar_pai="contratos_compra"` grava no `audit_log` do pai quando o filho muda

Sempre que possível use as fábricas. Escreva à mão só quando houver **regra de negócio** (saldo, sequência, upsert).

## Regras de negócio que NÃO podem quebrar

### Saldo dos locais de entrega (contratos)

- **Embarque** soma em `locais_entrega.total_embarcado`; apagar reverte com **piso zero**
- **Faturamento** soma em `locais_entrega.total_transferido`; ao editar, **reverte do local antigo e aplica no novo** — se a NF trocar de local, o saldo se move
- Ambos gravam no `audit_log` do contrato

### Pedidos — filhos polimórficos

`pedido_locais`, `pedido_pagamentos`, `pedido_faturamentos` e `pedido_embarques` são **compartilhados** entre compra e venda: discriminados por `pedido_tipo` (`compra`|`venda`) + `pedido_id`, **sem FK** (não há como declarar FK para duas tabelas). Toda query filtra pelas duas colunas.

⚠️ O schema **não tem ON DELETE CASCADE** nesses filhos — o `DELETE` do pedido apaga os 4 manualmente. Se esquecer, ficam órfãos que voltam a aparecer quando um id novo reutilizar o número.

### Códigos sequenciais

`PC00001`/`PV00001` (pedidos), `CPR00001` (lavoura), `CT-00001` (cotações). Calculados extraindo os dígitos do maior `cod` existente — feito em Python, não em SQL, porque `regexp_replace` não existe no SQLite dos testes.

### Cotação — versão é o CÁLCULO, não snapshot

`cotacao_versoes` guarda a revisão do **cálculo barter** (`preco_grao`, `quantidade_grao`, `encargo`, `armazem`, `motivo_revisao`) — não um snapshot da cotação. Revisão nova só nasce quando vem a chave `versao` no corpo do POST/PUT.

⚠️ A rota `/api/cotacoes-barter/divergencias` é declarada **antes** de `/<int:id>` — senão o Flask casaria "divergencias" como id.

### Lavoura

- Assessores listam com `qtd_cprs` e `qtd_visitas` (subqueries)
- CPR traz `tem_barter`: EXISTS de contrato de compra do mesmo parceiro com `modalidade = barter`
- Propriedade da CPR é **1:1** — o POST faz upsert, não cria duplicata
- Visita resolve `assessor_nome` pelo id quando não vem no corpo; `cpr_id` é **obrigatório**
- Foto mantém o contador `qtd_fotos` da visita em dia

## Banco — schema `barter` no banco-mana

40 tabelas em 7 domínios: cadastros (10) · parceiros (4) · contratos (8) · pedidos (7) · cotações (3) · lavoura (5) · sistema (3, inclui `expedicao_ordens`).

⚠️ **Nunca escrever no `public`** — o banco-mana é compartilhado entre os agentes Maná (em 2026-05-24 um ORM apagou o `public` e derrubou vários). O comando `init-schema` **recusa** rodar com `DB_SCHEMA=public`.

**Dívida técnica conhecida** (em `docs/backend-ANALISE_DADOS.md`): campos `*_nome` duplicados que deveriam ser join. Normalização adiada para depois do desligamento do Node.

## Variáveis de ambiente

| Variável | Observação |
|---|---|
| `BANCO_MANA_URL` | **obrigatória** — aceita `DATABASE_URL` como alternativa |
| `DB_SCHEMA` | `barter` (default); recusa `public` |
| `JWT_SECRET` | **obrigatória** — sem ela o app **não sobe** (fail-fast proposital) |
| `JWT_EXPIRES_HOURS` | default 12 |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` | 5 / 10 |

## Provisionar num banco novo

```bash
FLASK_APP=wsgi:app /opt/venv/bin/python -m flask init-schema
FLASK_APP=wsgi:app /opt/venv/bin/python -m flask seed-admin
```

> ⚠️ **Gotcha do Console do Railway:** o binário `flask` não está no PATH e o `python` do Nix não enxerga as dependências. Use o interpretador do venv do Nixpacks: `/opt/venv/bin/python -m flask <comando>`.

Outros comandos: `check-schema` (compara models × banco real, coluna a coluna) · `rotas`.

## Testes

```bash
python -m pytest tests/ -q     # 79 passed
```

Rodam em SQLite in-memory, sem PostgreSQL. `config.py` detecta pytest por `sys.modules` e desliga o fail-fast — se detectasse por `PYTEST_CURRENT_TEST`, quebraria na coleta (a variável só existe durante o teste, não no import).

## Não portado do Node (geradores de saída)

`GET /cotacoes-barter/<id>/pdf-cliente` · `GET /lavoura/cprs/<id>/documento` · `GET /lavoura/visitas/<id>/laudo` · `GET /lavoura/dashboard` · export Excel de faturamentos e de entregas.

São features à parte — não bloqueiam o uso do app. O código-fonte delas está em `legado/server.js`.

## Conformidade `mana-arquitetura-padrao`

**Conformidade-por-ausência:** zero-LLM e zero-WhatsApp na v1. Ao entrar qualquer um dos dois, seguir o ADR `2026-06-13-padrao-llm-gateway-e-porta-unica-whatsapp` (chave virtual no `mana-llm-gateway` + porta única do hub `agente-whatsapp`).

⚠️ Se precisar falar com **Simple Agro** ou **SoftExpert**, usar os SDKs `mana-simpleagro` / `mana-softexpert` (Python) — foi um dos motivos de escolher Flask em vez de manter Node.

## Pendências

1. **Front** — `index.html` monolítico ainda no legado. É o que falta pro app ser usável ponta a ponta no Flask
2. Geradores de saída (lista acima)
3. Identidade visual Maná (verde #1D6B3E + ouro #B8860B)
4. Migração de dados do banco antigo, ao desligar o Node
5. Validar lado a lado com o Node antes do corte

## Skills relacionadas

- **`novo-agente-mana`** — padrão de scaffold e publicação
- **`mana-arquitetura-padrao`** — governança (aplicável se entrar LLM/WhatsApp)
- **`akita`** — segurança e testes
- **Não se aplica:** `mana-simpleagro`, `softexpert-*` — este app não fala com SA nem SE
