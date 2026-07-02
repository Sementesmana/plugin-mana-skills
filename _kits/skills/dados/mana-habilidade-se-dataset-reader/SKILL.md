---
name: se-dataset-reader
description: >-
  Habilidade Maná para COMPLEMENTAR o SoftExpert com artefatos de IA via Conjunto
  de Dados (dataset-integration). Receita aplicada para montar um Conjunto que
  cruza WFPROCESS (o processo) × GNASSOCFORMREG × dyn<formulário> (× WFHISTORY
  para histórico/comentário) e lê isso por REST — em vez do fm_ws.getTableRecord
  paginado que varre a tabela inteira. Inclui o reader Python (sem Bearer, UTF-8,
  epoch→data, fail-soft, mesmo shape pro consumidor). Use SEMPRE que um agente/app
  precisar LER dados do SE (workflow + formulário + histórico) de forma barata, ou
  quando alguém disser: criar Conjunto de Dados, ler scred/atividade/histórico do
  SE, substituir getTableRecord lento, dataset-integration, "ler o SE via REST",
  cruzar WFPROCESS com dynscred, pegar comentário/motivo de uma ação do workflow,
  SCSCRED, ATVSC, ponte de leitura do SoftExpert. Irmã da skill
  softexpert-dataset-integration (que é a referência da API); esta é a receita +
  reader prontos. Camada META da Maná Builder.
---

# Habilidade — Leitor de Conjunto de Dados do SoftExpert (ponte de leitura SE → IA)

> **Lógica:** o SoftExpert é o sistema-registro dos processos e formulários. Ler ele "cru" por SOAP `fm_ws.getTableRecord` é caro — não tem filtro, pagina a tabela inteira (todas as revisões). A solução é montar um **Conjunto de Dados** (DI006) que já faz o JOIN e o filtro **no servidor**, e ler por **REST `dataset-integration`**. Assim os artefatos de IA (agentes, painéis) consomem o SE limpo e barato. É o padrão "complementar o SE com IA".
>
> Depende da skill **`softexpert-dataset-integration`** (regras da API REST). Esta habilidade é a **receita aplicada** + o **reader Python**.

## Quando usar

- Um agente precisa ler **scred / atividades / histórico / qualquer formulário** do SE.
- Está usando `fm_ws.getTableRecord` e a leitura ficou lenta/pesada (varre tabela inteira).
- Precisa do **comentário/motivo** de uma ação específica do workflow (ex.: "Enviar Solicitação de Ajuste").

## Receita — passo a passo

### 1. Montar o Conjunto de Dados no SE (fonte SESUITE)

Escreva uma query SQL (Postgres) que cruza o processo com o formulário. Joins-chave:

| O que | Join |
|---|---|
| Atividades do processo | `WFSTRUCT.idProcess = WFPROCESS.idObject` |
| Histórico do processo | `WFHISTORY.idprocess = WFPROCESS.idObject` (é o **idObject**, NÃO o display "000001") |
| Dados do formulário | `GNASSOCFORMREG.cdAssoc = WFPROCESS.cdAssocreg` **e** `GNASSOCFORMREG.oidEntityreg = dyn<form>.oid` |
| Grid filha do formulário | `dyn<form>.oid<relação> = dyn<form>filha.oid` |

Filtros úteis no `WHERE`: `cdProcessModel = <id do processo>`, `fgWfGroup = 1`, `fgStatus <= 5` (ativos), `dtStart >= CAST(NOW() AS DATE) + (-N * INTERVAL '1 DAY')` (janela).

**Gotchas do wizard de Conjunto (DI006):**

- **Sem `;` no final.** O wizard envolve sua query (alias `SEBIQBUILDER`) e **appenda o próprio `LIMIT`** — `;` ou `ORDER BY`/scalar-subquery soltos quebram.
- `idObject` é tipo **`citext`** (texto case-insensitive). Compare direto (`a.idObject = b.idprocess`); **`CAST(... AS INTEGER) = citext` não existe** (erro "operator does not exist").
- Para pegar **um** registro do histórico (último/uma ação) sem `ORDER BY` problemático: use `DISTINCT ON (idprocess) ... ORDER BY idprocess, dhhistory DESC` num subquery, **ou** `MAX(CASE WHEN <cond> THEN dscomment END) ... GROUP BY idprocess`.
- Para identificar uma **ação** específica no `WFHISTORY`, prefira `fgactionicon = <N>` (ex.: 33 = "Enviar Solicitação de Ajuste") em vez do `nmaction` acentuado — literal com acento pode quebrar o parser do wizard.
- Na etapa **Campos**, exponha as colunas (o REST só devolve o que está lá).
- Permissão: o usuário do token precisa de **visualização** no Conjunto (etapa 4 do DI006).

Veja `examples/dataset_scscred.sql` (leitura de formulário) e `examples/dataset_atvsc.sql` (atividade + comentário do histórico).

### 2. Ler por REST no agente

`GET {SE_URL}/apigateway/v1/dataset-integration/{ID_DATASET}`

- Header **`Authorization` = token CRU, SEM `Bearer`** (o recurso rejeita Bearer com 401).
- Só funciona com fonte **SESUITE** (fonte Protheus/externa → 400).
- Retorno: **array JSON**; datas em **epoch ms**; campos nulos como `""`; **trunca em ~10k linhas** (filtre server-side).
- **Force UTF-8** na decodificação — o `requests` pode errar o charset no build (chardet/charset_normalizer incompatível) e devolver acento como mojibake ("CrÃ©dito"), zerando filtros: `json.loads(r.content.decode("utf-8"))`.

Veja `examples/reader.py` — reader genérico, fail-soft, com epoch→data e mesmo shape pro consumidor.

## Checklist de validação

- [ ] Preview do Conjunto no wizard traz as linhas esperadas (sem erro de `;`/citext/`SEBIQBUILDER`).
- [ ] `GET …/dataset-integration/{ID}` com token sem Bearer retorna 200 + array.
- [ ] Reader força UTF-8 e converte epoch→data.
- [ ] No log do agente: 1 chamada (`[{ID}] N linhas lidas`) em vez de paginação 50/50.

## Validado em produção

- `SCSCRED` (agente-gestor-comercial, 2026-06-29): substituiu `getTableRecord(scred)` — 2679+ linhas paginadas → **49 numa chamada**. ADR `2026-06-29-gestor-comercial-scred-via-dataset-integration`.
- `ATVSC` (agente-gestor-comercial, 2026-06-25/29): atividade "Ajustar Crédito" habilitada + **motivo** (dscomment via `fgactionicon=33`). ADR `2026-06-25-gestor-comercial-categoria-ajuste-credito`.
