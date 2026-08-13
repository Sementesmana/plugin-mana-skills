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
- `agente-comercio-revendas` (2026-07-03) — 1º consumidor real da habilidade.
- `agente-documentos` (2026-07-05) — 9 docs LAKE HIT em 0,4s; análise 108,9s → 57,8s.
- `agente-financeiro-sa` (ADR 2026-08-13) — o lake como **piso de
  disponibilidade**, não só de latência: Simple Agro fora do ar passa a servir o
  último snapshot bom em vez de tela vazia. Snapshot de 356 pedidos em produção.

> ⚠️ **Ao instalar: não pine `psycopg2-binary`.** A habilidade declara
> `psycopg2-binary>=2.9.10`. Um `==2.9.9` no `requirements.txt` do consumidor dá
> `ResolutionImpossible` no build. Use `>=2.9.10` ou simplesmente não declare —
> a habilidade resolve.

> 💡 **Para chamar o endpoint de ingestão sem expor a senha:** a env var já
> existe dentro do container. Pelo Console do Railway,
> `curl -X POST -H "X-API-Key: $PAINEL_SENHA" http://localhost:$PORT/api/atualizar-data-lake`.
> Ninguém revela, copia ou cola o segredo.

## O uso que quase ninguém pensa primeiro: disponibilidade

A leitura óbvia da habilidade é velocidade — esconder fonte lenta. O
`agente-financeiro-sa` expôs a outra: **o lake é o que sobra quando a fonte cai.**

O painel dele mostrava "Nenhum pedido encontrado." sempre que o Simple Agro
falhava, porque o cliente devolvia `[]` em qualquer erro de HTTP e esse `[]`
era gravado no cache. Quem lê `[]` não consegue distinguir "não há pedidos" de
"a fonte recusou". Duas correções, nesta ordem — a segunda não funciona sem a
primeira:

1. **Falha ganha tipo próprio.** Uma exceção (`SAIndisponivel`), não lista vazia.
2. **O lake vira o piso.** Ordem de leitura
   `memória → arquivo → lake → fonte ao vivo`; se a fonte cair, cai para o lake
   de **qualquer idade**, e só levanta erro quando não existe snapshot nenhum.

```python
try:
    dados = buscar_na_fonte()          # levanta se a fonte recusar
except FonteIndisponivel:
    velho, quando = lake.read(chave)   # TUPLA
    if velho:
        return velho, "lake:vencido", idade(quando)   # com aviso na tela
    raise                                             # erro explícito, nunca tela vazia
lake.upsert(chave, dados)
```

> ⚠️ **`upsert()` aceita payload vazio.** A habilidade não julga o conteúdo — de
> propósito, porque `[]` é legítimo em muitos domínios. **A guarda mora no
> consumidor.** Sem ela você troca "tela vazia por 20 minutos" por "tela vazia
> até alguém reparar", que é estritamente pior. Vale o mesmo para o caminho de
> erro: **nunca deixe uma falha escrever no lake.**

E quando servir dado velho, **diga na tela que é velho**. Número de ontem com
cara de número de agora é pior que a tela vazia que você acabou de consertar.

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
