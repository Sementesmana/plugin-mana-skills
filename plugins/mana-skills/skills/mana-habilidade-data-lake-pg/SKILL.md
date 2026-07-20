---
name: data-lake-pg
description: >-
  Habilidade Maná pra cache durável de fontes lentas usando JSONB no Postgres.
  Padrão lake-first com fallback ao-vivo + advisory_lock pra concorrência
  Gunicorn N workers. Use SEMPRE que um agente/painel depende de fonte lenta
  (SOAP SE, REST de terceiros, agregação cara) e quer cobrir essa latência
  com cache durável que sobreviva a deploy + funcione com múltiplos workers.
  Cobre os padrões "atualiza no cron + botão", "lê do banco se tiver, senão
  compute_fn ao vivo", "se compute falhar, serve dado velho do lake (não
  morre)". Irmã da habilidade se-dataset-reader (juntas formam o stack de
  dados Maná Builder, sub-categoria "dados").
---

# Habilidade — Data Lake JSONB no Postgres (cache durável com fallback ao-vivo)

> **Lógica:** todo painel Maná que depende de fonte lenta tem o mesmo problema:
> latência somada no carregamento. Solução: cachear snapshots em JSONB no
> Postgres com chave logical (`workflows`, `totais`, etc), atualizar via cron
> ou botão, e ler **lake-first com fallback ao-vivo**. Quando a fonte cai,
> pipeline não morre — serve o lake mesmo velho.

## Quando usar

- Painel/dashboard chama `/listar-X` no load e isso demora segundos
- Função pesada (SOAP SE, agregação cara) chamada várias vezes ao dia
- Cron periódico que computa snapshot agregado
- Múltiplos workers Gunicorn precisam coordenar 1 ingestão só
- Quer ter botão "Atualizar agora" no painel pra forçar refresh

## Quando NÃO usar

- Cache curto em memória (use `functools.lru_cache` ou Redis)
- Dados que mudam a cada chamada (não vale cachear)
- Datasets gigantes (>10MB) — JSONB começa a pesar; considere tabela
  estruturada própria

## Receita — passo a passo

### 1. Setup (1× no boot do agente)

```python
import os
from mana_habilidade_data_lake_pg import DataLake

lake = DataLake(
    db_url=os.environ["DATABASE_URL"],
    schema="agente_nome",            # cada agente tem seu schema
    advisory_lock_id=778900,         # único por agente — evita colisão
)
lake.init_schema()                    # idempotente
```

### 2. Endpoint /api/atualizar-data-lake (botão + cron)

```python
@app.route("/api/atualizar-data-lake", methods=["POST", "GET"])
def atualizar_lake():
    with lake.lock() as got:
        if not got:
            return jsonify({"status": "ja em andamento"}), 200
        lake.upsert("workflows", get_workflows_from_se())
        lake.upsert("totais", get_totais_financeiro())
    return jsonify({"status": "ok"}), 200
```

### 3. Leituras (substituir SOAP/REST por lake-first)

```python
@app.route("/listar-workflows")
def listar_workflows():
    dados = lake.read_or_compute(
        chave="workflows",
        compute_fn=get_workflows_from_se,
        max_age_hours=24,
    )
    return jsonify(dados)
```

### 4. Status pro painel ("Atualizado em N min atrás")

```python
@app.route("/api/data-lake-status")
def data_lake_status():
    return jsonify({"chaves": lake.status()})
```

## Chave lógica — convenções recomendadas

| Padrão | Exemplo | Quando |
|---|---|---|
| Singular agregado | `workflows`, `totais`, `gaps` | Snapshots agregados (a fatia inteira) |
| Com namespace | `detalhe:<id>` | Snapshots por entidade (1 chave por workflow) |
| Com hash | `query:<sha256>` | Cache de queries dinâmicas |

## Concorrência (advisory lock)

`pg_try_advisory_lock(id)` é não-bloqueante: retorna `True` se pegou, `False` se outro worker já tem. Use no cron pra garantir 1 ingestão:

```python
with lake.lock() as got:
    if not got:
        log.info("[CRON] já em andamento; pula")
        return
    # ... ingestão ...
```

Escolha `advisory_lock_id` único por agente (ex: hash do nome → int). Documente no manifest.yaml do agente.

## Checklist de validação

- [ ] `lake.init_schema()` no boot (idempotente, pode rodar todo deploy)
- [ ] `advisory_lock_id` único por agente (documentar)
- [ ] Schema dedicado por agente (não `public`)
- [ ] `compute_fn` no `read_or_compute` é fail-safe (não pode dar `print()` que polui log)
- [ ] Cron com `lake.lock()` (1× mesmo com N workers)
- [ ] Endpoint `/api/atualizar-data-lake` pro botão manual
- [ ] Endpoint `/api/data-lake-status` pro painel mostrar idade

## Validado em produção

- `agente-pedidos` (ADR 2026-06-30) — 4 fontes do `/painel-reais` no lake.
  Leitura **204ms** vs live **~2s** (10x). Painel 100% no banco-mana.

## Gotchas

- **JSONB encoding:** `json.dumps(dados, ensure_ascii=False, default=str)` é
  o que a habilidade faz internamente. Pega `datetime` automaticamente.
- **Schema injection:** o construtor valida que `schema` e `table_name` são
  identificadores SQL válidos (alfanuméricos + underscore). Não passe input
  de usuário direto.
- **Advisory lock fica preso?** Se um worker morrer durante o lock, o Postgres
  libera automaticamente quando a conexão fecha. Não precisa cleanup manual.
- **`max_age_hours=None` (default)** = qualquer dado serve, sem expirar. Use
  `max_age_hours=24` se quer recomputar diariamente.
