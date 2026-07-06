---
name: mana-habilidade-notificacao-whatsapp
description: >-
  Habilidade Maná Builder Camada 2C. Cadastro de contatos + agendamento cron +
  envio de notificações WhatsApp (texto, áudio TTS, PDF, imagem) via hub
  agente-whatsapp. Substitui código inline replicado em ~4 agentes (gestor-comercial,
  gestor-estoque, premiacao, comercio-revendas). Consome POST /send-whatsapp,
  /send-whatsapp-lista, /send-document, /send-image do hub, com payload obrigatório
  (classe, idempotency_key, agente) inserido automaticamente. Use SEMPRE que um
  agente Maná precisar mandar WhatsApp automatizado pra lista de pessoas cadastradas,
  agendar cron de envio, ou fazer broadcast (texto/pdf/imagem). Também use quando
  criar app novo que precisa notificar usuários via WhatsApp com cadastro persistente.
categoria: habilidade
sub-categoria: notificacoes
owner: xayer-mana
versao-skill: 0.1.0
ultima-revisao: 2026-07-06
ativacao:
  - notificacao whatsapp
  - broadcast whatsapp
  - fan-out whatsapp
  - agendamento whatsapp
  - cron whatsapp
  - cadastro contatos whatsapp
  - enviar pdf whatsapp
  - enviar imagem whatsapp
  - mensagem programada whatsapp
  - notificar clientes
  - notificar vendedores
  - notificar revendedores
---

# mana-habilidade-notificacao-whatsapp — SKILL.md canônica

> Guia da habilidade pra o Claude do Cowork do dev consumidor. Cobre a **API completa**, os **gotchas** e o **padrão obrigatório** pra usar a habilidade sem chutar.

## O que ela é

**Habilidade Maná Builder Camada 2C** — primitiva reusável que consolida o padrão de "notificações WhatsApp agendadas com cadastro persistente" que estava replicado em 4 agentes.

Antes: cada agente tinha seu `mapa_vendedores.py` + `enviar_whatsapp.py` + `agendamentos.py` copiado.
Agora: `pip install` + 4 classes prontas.

## Filosofia (leia ANTES de compor)

**A habilidade dá PRIMITIVAS, não regras de negócio.**

Você (Cowork do dev consumidor) usa:

- `ContatoDDL` pra criar as tabelas no schema do agente consumidor
- `ContatoRepo` pra CRUD dos contatos
- `WhatsAppSender` pra mandar msg/pdf/imagem
- `NotificationScheduler` pra cron

E **compõe** a lógica específica do agente:
- O QUÊ mandar (template, formato)
- QUANDO mandar (cron expression escolhida pelo dev)
- QUEM cadastrar (tela de admin fica no agente consumidor)
- FILTROS específicos (`listar_ativos(tags=[...])` com tags que o agente define)

**Não faça:** copiar bloco de exemplo e trocar valores. Use as classes como referência da API e escreva código específico do caso.

## Instalação

```bash
pip install "git+https://github.com/Sementesmana/mana-habilidade-notificacao-whatsapp.git@v0.1.0"
```

Env vars esperadas no agente consumidor:

```bash
AGENTE_WHATSAPP_URL=https://agente-whatsapp-production.up.railway.app
AGENTE_WHATSAPP_API_KEY=<pedir pro Xayer — mesma X-API-Key do hub>
DATABASE_URL=<postgres do banco-mana>
```

## API — as 4 classes principais

### 1. `ContatoDDL` — cria tabelas no schema do agente

```python
from mana_habilidade_notificacao_whatsapp import ContatoDDL

ddl = ContatoDDL(db_url=DATABASE_URL, schema="comercializacao")
ddl.init_schema()  # idempotente — pode chamar todo startup
```

Cria 3 tabelas no schema:

- `contatos_notificacao` (id, nome, whatsapp UNIQUE, email, ativo, tags[], metadata jsonb, timestamps)
- `envios_notificacao` (idempotency_key UNIQUE, contato_id FK, telefone, tipo, sucesso, tentativa, hub_response jsonb)
- `jobs_notificacao` (id TEXT, nome, cron, ativo, ultimo_run, proximo_run, metadata jsonb)

### 2. `ContatoRepo` — CRUD

```python
from mana_habilidade_notificacao_whatsapp import ContatoRepo

repo = ContatoRepo(db_url=DATABASE_URL, schema="comercializacao")

# Create
c = repo.criar(
    nome="João da Silva",
    whatsapp="+5562999999999",    # normalização automática
    email="joao@revenda.com",
    tags=["revendedores", "sudeste"],
    metadata={"origem": "planilha_maio"},
)

# Read
contato = repo.buscar_por_id(42)
contato = repo.buscar_por_whatsapp("62999999999")   # normaliza antes de buscar
lista = repo.listar()                                # todos
lista_ativos = repo.listar_ativos()                  # ativos=true
lista_filtrada = repo.listar_ativos(tags=["revendedores"])   # && text[] no Postgres

# Update
repo.atualizar(42, nome="Novo Nome", tags=["premium"])
repo.desativar(42)
repo.ativar(42)

# Delete
repo.deletar(42)   # retorna True se deletou

# Bulk (em transação)
repo.criar_lote([
    {"nome": "A", "whatsapp": "62999999991"},
    {"nome": "B", "whatsapp": "62999999992", "tags": ["premium"]},
])
```

### 3. `WhatsAppSender` — cliente do hub

```python
from mana_habilidade_notificacao_whatsapp import WhatsAppSender

sender = WhatsAppSender(
    hub_url=AGENTE_WHATSAPP_URL,
    hub_key=AGENTE_WHATSAPP_API_KEY,
    agente_nome="comercio-revendas",     # aparece no whatsapp.outbox do hub
    classe_default="transacional",       # ou "conversacional"/"massa"
    timeout_s=30,
)

# Texto
r = sender.send_text("62999999999", "Olá!")
# r = {"sucesso": True, "hub_response": {...}, "idempotency_key": "text:abc123", "telefone": "5562..."}

# Áudio (TTS local no hub)
r = sender.send_audio("62999999999", "Bom dia!", voz="onyx")

# PDF
r = sender.send_pdf(
    "62999999999",
    pdf_bytes=open("relatorio.pdf", "rb").read(),
    filename="relatorio_2026_07.pdf",
    caption="Relatório de julho",
)

# Documento genérico
r = sender.send_document(
    "62999999999",
    binario=xlsx_bytes,
    filename="planilha.xlsx",
    extension="xlsx",       # png|jpg|jpeg|pdf|xlsx|docx|etc
    caption="Planilha Q3",
)

# Imagem inline (preview no chat)
r = sender.send_image(
    "62999999999",
    imagem_bytes=png_bytes,
    extension="png",         # png|jpg|jpeg
    caption="Ranking semanal",
)

# BROADCAST — texto usa /send-whatsapp-lista nativo (1 chamada só)
contatos = repo.listar_ativos(tags=["revendedores"])
resultados = sender.broadcast_text(
    contatos=contatos,
    template="Olá {nome}, sua meta é {meta} bags",
    variaveis_por_contato={
        1: {"meta": "50"},
        2: {"meta": "80"},
    },
    idempotency_prefix="meta-2026-07-06",
)
# resultados = [{"telefone": ..., "sucesso": True, "idempotency_key": ...}, ...]

# BROADCAST PDF/imagem — chamadas individuais (hub não tem lote pra doc)
resultados = sender.broadcast_pdf(contatos, pdf_bytes, filename="rel.pdf")
resultados = sender.broadcast_image(contatos, png_bytes, extension="png", caption="Ranking")
```

**Nunca joga exceção pra 4xx/5xx** — retorna `{"sucesso": False, "erro": "...", "erro_tipo": "HubXxx"}`. Isso libera o consumidor pra decidir o retry.

### 4. `NotificationScheduler` — cron

```python
from mana_habilidade_notificacao_whatsapp import NotificationScheduler

scheduler = NotificationScheduler(sender=sender, repo=repo)  # objetos opcionais

def enviar_meta_semanal():
    contatos = repo.listar_ativos(tags=["revendedores"])
    sender.broadcast_text(contatos, "Segunda! Meta desta semana...")

# Cron expression: 'min hora dia_do_mes mes dow'
scheduler.agendar_cron("meta-semanal", "0 8 * * MON", callback=enviar_meta_semanal)

# Ou intervalo
scheduler.agendar_intervalo("heartbeat", segundos=300, callback=enviar_heartbeat)

# Gerenciar
scheduler.listar_jobs()          # [{"id": ..., "trigger": ..., "proximo_run": ...}]
scheduler.pausar("meta-semanal")
scheduler.retomar("meta-semanal")
scheduler.remover("meta-semanal")

# Vida
scheduler.start()   # inicia APScheduler (chame no startup do agente)
scheduler.shutdown()
```

Timezone default: `America/Sao_Paulo`. Ajuste passando `timezone="UTC"` no construtor.

## Padrões OBRIGATÓRIOS que a habilidade força

1. **WhatsApp SÓ pelo hub** — ADR 2026-06-13. Nunca Z-API direto.
2. **Payload obrigatório** — `classe` + `idempotency_key` + `agente` sempre presentes.
3. **Classes válidas** — `conversacional` (síncrono, chat), `transacional` (fila, retry), `massa` (fila, throttle maior). Passar outra classe = `HubValidation`.
4. **Idempotency_key determinístico** — mesmo envio 2x = 1x. Evita duplicidade em retry.
5. **Base64 ≤12 MB** — limite do Z-API base64. Doc/imagem maior = `PayloadTooLarge`.

## Gotchas

### Normalização de telefone

Aceita QUALQUER formato brasileiro. Sempre normaliza:

| Input | Normalizado |
|---|---|
| `62999999999` | `5562999999999` |
| `5562999999999` | `5562999999999` |
| `+55 62 99999-9999` | `5562999999999` |
| `6299999999` (10 dig) | `556299999999` |
| `120363XYZ-group` | `120363XYZ-group` (grupo, passa direto) |
| `abc@g.us` | `abc@g.us` (grupo v2, passa direto) |

Idempotency é feito COM o telefone normalizado — 2 formatos do mesmo número = mesmo key.

### Broadcast text: `/send-whatsapp-lista` com fallback

Broadcast de texto usa endpoint em lote do hub (1 chamada, N mensagens). Se hub rejeitar com 400, cai automaticamente pra envios individuais. Não precisa tratar.

### Broadcast pdf/imagem: individual sempre

Hub não tem `/send-document-lista` nem `/send-image-lista`. Broadcast de doc/imagem chama N vezes o endpoint individual. Considere throttle no consumidor se lista for grande (>100 contatos).

### Templates com `{variavel}`

`broadcast_text` aceita template com `{chave}`. Substitui usando `variaveis_por_contato[contato.id]`. Se a chave não existir, o placeholder fica no texto (não crasha).

```python
sender.broadcast_text(
    contatos=[Contato(id=1, nome="A"), Contato(id=2, nome="B")],
    template="Olá {nome}, meta: {meta}",
    variaveis_por_contato={
        1: {"meta": "50"},
        # id=2 sem meta → texto vira "Olá B, meta: {meta}"
    },
)
```

Se quiser garantir presença, valide antes ou use `Contato.metadata` como fonte.

### Init_schema é idempotente

Pode chamar todo startup. `CREATE SCHEMA IF NOT EXISTS` + `CREATE TABLE IF NOT EXISTS`. Zero risco.

### Conexão Postgres

Cada operação abre conexão nova por padrão. Pra reusar (pool), passe `conn=meu_pool.getconn()` como último parâmetro. Aí o repo NÃO commita/rollback sozinho — controle fica com quem passou.

## LGPD

Trafega **PII** (nome + whatsapp + email dos contatos). Se for enviar dado do contato pra LLM depois, **pseudonimize antes** com `mana-habilidade-pseudonimizar-pii`.

## Testes

```bash
pytest tests/ --cov=mana_habilidade_notificacao_whatsapp
```

- 88 testes passando
- 85% cobertura (mínimo Maná: 70%)
- Mocks pra psycopg2 e requests — CI não precisa Postgres real

## Origem prática (padrão consolidado de 4 agentes)

- **agente-gestor-comercial** — mapa_vendedores + fan-out DM + agendamento editável
- **agente-gestor-estoque** — Pillow gera PNG do painel + `/send-image`
- **agente-agronomo** — TTS via hub (modo=audio + voz onyx)
- **agente-premiacao** — cron semanal (segunda 08h BRT)

## Estado

**v0.1.0 — alpha.** Publicada 2026-07-06.

- Consumidor real planejado: `agente-comercio-revendas` (Dayan, piloto).
- Vira `beta` quando ele migrar em produção sem regressão.
- Vira `producao` quando 2+ consumidores reais rodarem.

## Recursos

- **Repo:** https://github.com/Sementesmana/mana-habilidade-notificacao-whatsapp
- **README:** [README.md](./README.md)
- **Manifest:** [manifest.yaml](./manifest.yaml)
- **Nota vault:** `ManaVault/06-Agentes-e-Skills/habilidades/notificacao-whatsapp.md`
- **ADRs:** 2026-06-13 (hub WhatsApp), 2026-06-24 (Camada 2C), 2026-06-28 (gate consumidor)
