---
name: softexpert-dataset-integration
description: Referência canônica da API REST de Conjuntos de Dados do SoftExpert (dataset-integration) — Sementes Maná. Lê o retorno de qualquer Conjunto de Dados (DI006) via REST, usando o SE como camada de leitura/ETL para dados nativos do SE (workflows, formulários, documentos, GRC, BSC). Use SEMPRE que precisar consumir um Conjunto de Dados do SE por HTTP, criar um Conjunto novo, ou montar integração REST de leitura com o SoftExpert. CRÍTICO: header Authorization SEM Bearer; só funciona com fonte SESUITE ("geral - SE"); fonte Protheus/externa dá 400. Também quando mencionar: dataset-integration, conjunto de dados, DI006, DI004, /apigateway/v1, SESUITE, idDataset, ETL SoftExpert, ler scred via REST, GatewayJWT, fonte de dados SE, API REST SoftExpert leitura, teste1, ProdutoxEstoque.
---

# SoftExpert Dataset Integration (API REST) — Base de Conhecimento

> Referência canônica do recurso REST **`dataset-integration`** do API Gateway do SoftExpert.
> Permite consumir, via HTTP, o retorno de um **Conjunto de Dados** cadastrado no SE (componente **DI006**).
> **Validado empiricamente na instância da Maná em 23/jun/2026** (conjunto `teste1` → `200 OK`).
> Fonte oficial: `https://developer.softexpert.com/en/docs/data-integration/`

## O que essa API faz (e o que NÃO faz)

O SE tem um componente **Conjunto de Dados** (DI006) onde se cadastra uma **query** sobre uma **fonte de dados**. Esse recurso REST **expõe o resultado dessa query por HTTP** — transformando o SE numa camada de leitura/ETL.

**Faz bem:** servir por REST qualquer dado **nativo do SE** (fonte `SESUITE`) — workflows, formulários (scred, formscpr, contapagar…), documentos, dados de GRC/BSC/Plano de Ação. É a **alternativa REST de leitura** ao SOAP `fm_ws`/`wf_ws`.

**NÃO faz:** servir direto um Conjunto cuja fonte é **externa** (ex: `protheus`). A API recusa com `400`. Pra dado do Protheus, ver a seção [Padrão SE-como-ETL para Protheus](#padrão-se-como-etl-para-fontes-externas-protheus).

## ⚠️ As 3 regras que quebram quem não sabe

1. **Header `Authorization` SEM `Bearer`.** É `Authorization: {token}`, token cru.
   A doc *geral* do SE manda usar `Bearer`, mas **este recurso específico rejeita o `Bearer` com `401`**. Confirmado na marra (com `Bearer` → 401; sem `Bearer` → passa).
2. **Só fonte `SESUITE` ("geral - SE").** Conjunto de fonte `protheus`/externa → `400 "Este recurso só pode ser integrado com conjuntos de dados usando a fonte de dados SESUITE"`.
3. **Tudo é case-sensitive** — o `idDataset` na URL e cada parâmetro do filtro no POST. `ProdutoxEstoque` ≠ `produtoxestoque`.

## Endpoint

```
# Sem filtro → GET
GET  {SE_URL}/apigateway/v1/dataset-integration/{idDataset}
Authorization: {SE_API_KEY}        ← SEM "Bearer"

# Com filtro → POST (corpo JSON; cada chave = um parâmetro da query)
POST {SE_URL}/apigateway/v1/dataset-integration/{idDataset}
Authorization: {SE_API_KEY}
Content-Type: application/json

{ "id_login": "coronado" }
```

- `{SE_URL}` = `https://sementesmana.softexpert.app` (produção Maná) — env var `SE_URL`
- `{idDataset}` = campo **Identificador** do Conjunto no DI006 (case-sensitive)
- `{SE_API_KEY}` = API key de **um usuário** do SE (env var `SE_API_KEY`) — ver [Usuário de integração](#usuário-de-integração-obrigatório-em-produção)

### GET vs POST — a regra do Antonio (especialista SE)

> Sem filtro → `GET` direto. Com filtro → `POST`, e **cada chave do JSON é um parâmetro (`lpa`) da query**. Cuidado: SE é case-sensitive, então maiúsculas no id e nos parâmetros têm que bater igualzinho.

## Exemplo real validado (Maná, 23/jun/2026)

```bash
curl -i 'https://sementesmana.softexpert.app/apigateway/v1/dataset-integration/teste1' \
  -H "Authorization: {SE_API_KEY}"
```

`teste1` é um Conjunto de fonte **`geral - SE`** com query sobre os workflows. Retorno (resumido, **PII mascarada aqui**):

```json
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8
[
  {
    "idprocess": "000004",
    "nmprocess": "FERNANDO M. DE C. | CAMPINA COM. E REPR. LTDA | ***.***.***-** | 2500000.00",
    "nmstatus": "Andamento",
    "nmrevisionstatus": "Em Aprovação de Crédito - Comitê",
    "nmprocessmodel": "Solicitação de Crédito",
    "dhstart": 1777461975000,
    "nmuserstart": "FERNANDO MOREIRA DE CASTRO",
    "total_records": 1
  }
]
```

Notas sobre o retorno:
- Cada linha da query vira um objeto JSON; a estrutura de campos é a que você mapeou na **etapa 3 (Campos)** do Conjunto.
- Campos nulos voltam como `""` (string vazia), não `null`.
- Datas vêm como **epoch em milissegundos** (`dhstart: 1777461975000`).
- Limite: **primeiros 10.000 registros**.

## Como criar/configurar um Conjunto de Dados (DI006)

Assistente de 4 etapas:

1. **Dados gerais** — escolher **Tipo de conjunto de dados** (a *fonte*: `geral - SE` p/ SESUITE, ou uma fonte externa), definir **Identificador** (vai na URL — escolha algo URL-safe e lembre do case) e **Nome**.
2. **Construção da Query** — a query. Para filtros via POST, declare parâmetros (`lpa`) na query; o nome de cada parâmetro é a chave que vai no corpo JSON.
3. **Campos** — mapear os campos que a query retorna (definem as chaves do JSON de saída).
4. **Segurança** — conceder ao **usuário/grupo** que vai consumir a API permissão de **visualização**. Sem isso → `404`/`401`, mesmo com token válido.

> **Credenciais de fonte (DI004) ≠ token da API.** O componente **Credenciais (DI004)** guarda como o SE **sai e se conecta nas fontes** (ex: credencial `Protheus` p/ o banco do Protheus) — é *outbound*. NÃO é o token que autentica sua chamada *entrando* no gateway. Não confunda os dois.

## Usuário de integração (obrigatório em produção)

A própria SoftExpert recomenda (e o especialista da Maná reforçou): **não use seu login pessoal**. Crie um **usuário dedicado de integração**:

- **um único grupo de acesso**, contendo o menu **Conjunto de Dados (DI006)**;
- associado a **uma licença MANAGER**;
- **não sincronizado com AD**;
- **não usado no dia a dia** (exclusivo de integração — facilita auditar o histórico).

A **API key desse usuário** é o `SE_API_KEY` que vai nas env vars dos agentes. A key vive na tela de **Conta de usuário** do SE (cada usuário tem **uma** key, que dá acesso só aos menus do grupo dele).

> Observação de campo: um login pessoal pode dar `401 "Valid GatewayJWT not found in the request or user is blocked!"` mesmo com token correto, se o usuário não estiver habilitado/autorizado no API Gateway. O usuário de integração com o grupo certo resolve.

## Códigos de retorno

| HTTP | Significado | O que checar |
|---|---|---|
| `200` | OK | Array JSON (até 10k linhas). |
| `400` | Conjunto inválido / não suportado | **Fonte não é SESUITE** (msg "...fonte de dados SESUITE"), ou características não suportadas. |
| `401` | `Valid GatewayJWT not found... or user is blocked` | Token ausente/vazio, **`Bearer` indevido**, ou usuário sem acesso ao API Gateway. |
| `404` | Identificador inválido **ou sem permissão** | Case do `idDataset` errado, ou etapa 4 (Segurança) não liberou o usuário. |
| `500` | Erro inesperado / **timeout** da query | Otimizar a query; ela pode estar estourando o tempo. |
| `503` | Serviço sobrecarregado (memória da JVM) | Repetir com backoff. |

Corpo de erro: `{ "message": "...", "status": <http> }`.

## Padrão SE-como-ETL para fontes externas (Protheus)

Como a API só serve `SESUITE`, **não dá pra apontar direto no Protheus**. Duas opções:

- **Opção A — ETL para dentro do SE:** um fluxo de **Integração de Dados** do SE lê do Protheus e **grava numa entidade/formulário do SE** (que é `SESUITE`). Aí um Conjunto `SESUITE` sobre essa entidade vira API REST normalmente. É o "SE como ETL" legítimo (dado materializado no SE, com histórico/auditoria).
- **Opção B — gateway dedicado:** continuar usando o **`agente-protheus`** (Flask + SQL Server direto), que já entrega dado Protheus por REST. Melhor quando o dado precisa ser *fresco* e não faz sentido materializar no SE.

Escolha por característica do dado: materializável e auditável no SE → A; volátil/volumoso → B.

## Segurança / LGPD (obrigatório)

- Conjuntos podem retornar **PII pesada** (ex: `scred`/CRE-001 traz CPF/CNPJ, nome, valor, parecer). Tratar todo retorno como **dado sensível**.
- **Pseudonimizar ANTES de qualquer chamada a LLM** (ADR Maná 2026-06-19). Mapa nome↔código em memória, nunca persiste.
- **Nunca logar** o corpo de retorno com PII. Logar só `idDataset`, status HTTP e contagem.
- Token (`SE_API_KEY`) **só via env var** no Railway — nunca hardcode, nunca em chat. Se vazar, **rotacionar** (gerar nova key do usuário no SE).
- Use o **usuário de integração** com o **mínimo** de menus no grupo de acesso.

## Helper Python

Cliente pronto em [`se_dataset.py`](se_dataset.py). Uso:

```python
from se_dataset import SEDataset

se = SEDataset()  # lê SE_URL e SE_API_KEY do ambiente

linhas = se.list_dataset("teste1")              # GET, sem filtro
um     = se.get_dataset("users", {"id_login": "coronado"})  # POST, com filtro
```

## Relação com outras skills / agentes

- **`softexpert-wf-ws`** — escrita e operações de workflow via SOAP (instanciar, avançar, popular grid). Esta skill aqui é o **complemento de leitura por REST**.
- **`agente-protheus`** — gateway SQL direto pro Protheus (Opção B acima).
- **`mana-arquitetura-padrao`** — qualquer agente novo que consuma esta API segue o padrão (LLM no gateway, WhatsApp na porta única, dedup por requisição).

## Pendências / a confirmar

- [ ] Testar o caminho **POST com filtro** (parâmetro `lpa`) num Conjunto SESUITE real e registrar o exemplo.
- [ ] Corrigir o drift em `03-Sistemas/SoftExpert/credenciais.md` (diz `Bearer`; é **sem Bearer** para este recurso).
- [ ] Decidir formalmente (ADR) a divisão SE-ETL (Opção A) × `agente-protheus` (Opção B) para dado externo.
