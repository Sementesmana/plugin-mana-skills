---
name: agente-protheus
description: Gateway REST de LEITURA do Protheus da Sementes Maná LTDA (plataforma N1, produção). Flask no Railway que conecta DIRETO no SQL Server do Protheus via pymssql (não é via SE dataset — o docstring do repo está desatualizado) e expõe datasets catalogados por HTTP: cliente (SA1010), vendedorcliente1 (SA1010+SA3010), baixas_pagar (SE5010+SE2010+SA2010) e baixas_receber (SE5010+SE1010+SA1010) — os dois de baixas alimentam o poller do agente-financeiro-gestao, com janela e corte em D-1; estoque/pedidos/titulos em aberto seguem como TODO. Consumido pelo SoftExpert (CORS restrito aos domínios do SE, Atividade Sistêmica) e por painéis Maná via X-API-Key ou cookie de sessão de 8h. Cache em memória por dataset+filtros com invalidação por endpoint, validação anti-injection dos códigos Protheus, headers de segurança e erro sanitizado que não expõe host nem base. Use SEMPRE no agente-protheus — adicionar dataset, cache, auth do painel, CORS do SE, conexão pymssql/FreeTDS, timeouts. Também quando mencionar: SA1010, SA3010, P12_PROD, PROTHEUS_DB_HOST, /query/<dataset>, /datasets, /vendedores, /clientes-por-vendedor, /cache/invalidar, gateway Protheus, IP shared Railway.
---

# agente-protheus — gateway REST → Protheus (SQL Server)

> **Plataforma N1, produção** · `https://agente-protheus-production.up.railway.app` · dono Xayer · comportamento **D (determinístico)**.

## O que é

Ponte HTTP entre o Protheus (TOTVS) e o resto do ecossistema. **Somente leitura.** Quem precisa de dado do Protheus — SoftExpert, painéis, outros agentes — chama este gateway em vez de abrir conexão com o ERP.

## ⚠️ Drift documental importante

O docstring do `app.py` descreve "gateway via SE Conjunto de Dados (DI006)" e lista `SE_URL`/`SE_API_KEY`. **Isso é história antiga**: o código real (`agente_protheus.py`) conecta **direto no SQL Server via `pymssql`**, e essas duas variáveis não são lidas em lugar nenhum. O cockpit (`catalogo_solucoes.py`) repete a descrição velha. Ao documentar ou explicar este agente, valer o código — e corrigir docstring/cockpit quando mexer.

## Catálogo de datasets

| id | origem | filtros | campos |
|---|---|---|---|
| `cliente` | SA1010 | `PESQUISA` | COD_CLIENTE, LOJA, NOME_CLIENTE, CPF_CNPJ, EMAIL, TELEFONE, INSCRICAO_ESTADUAL, MUNICIPIO, UF |
| `vendedorcliente1` | SA1010 + SA3010 | `PESQUISA` | idem + COD_VENDEDOR, NOME_VENDEDOR |
| `baixas_pagar` | SE5010 + SE2010 + SA2010 | `DATA_DE`, `DATA_ATE`, `FILIAL` | o que SAIU do caixa |
| `baixas_receber` | SE5010 + SE1010 + SA1010 | `DATA_DE`, `DATA_ATE`, `FILIAL` | o que ENTROU no caixa |

Comentados como TODO: `estoque` (SB1010), `pedidos` (SC5010), `titulos_receber` (SE1010), `titulos_pagar` (SE2010). **Dataset novo entra no catálogo** — não criar rota solta.

### O que os datasets de baixas ensinaram — leia antes de criar dataset novo

- **Exclusão no Protheus é `D_E_L_E_T_ = ' '` (espaço)**, não `<> '*'`.
- **Join "só pra buscar um nome" muda a contagem.** Quase toda tabela tem
  `_FILIAL` e chave composta: a da SE2 inclui `E2_TIPO`, e o mesmo documento
  pode existir como dois tipos. Use `OUTER APPLY ... TOP 1` para o título e
  subconsulta escalar `TOP 1` para o cadastro. **Confira o COUNT contra a
  tabela-base sempre que acrescentar um join** — duas violações custaram um
  deploy cada (1222 × 1217).
- **Nome de parceiro é a RAZÃO SOCIAL** (`A2_NOME`/`A1_NOME`), nunca
  `E2_NOMFOR`/`E1_NOMCLI`: o relatório do Protheus imprime razão social
  (Pergunta 30) e o `E1_NOMCLI` é char(20) com o nome da FAZENDA truncado.
- **A regra de seleção é a do RELATÓRIO, não a do SQL óbvio.** Os três recortes
  das baixas (`TIPODOC`, `SITUACA`, `NUMERO` preenchido) foram derivados por
  aritmética contra a planilha, com a aba de parâmetros como especificação. O
  porquê de cada um está no docstring da função de query — não apague.
- **O alvo é a TELA do consumidor, não o arquivo.** O `parseBaixas` do painel
  do financeiro descarta linha sem nome; bater com o arquivo e não com a tela
  teria mostrado R$ 98,1 mi onde a equipe sempre viu R$ 64,9 mi.

Validação: filial 0201, 01/07–24/08/2026 — pagar **1217 / R$ 64.871.478,52**,
receber **358 / R$ 35.283.442,36**.

## Endpoints

| Rota | Auth | O que faz |
|---|---|---|
| `GET /health` | — | status + conectividade (mostra `"database": "protheus"`, nome genérico de propósito) |
| `GET /datasets` | — | lista o catálogo |
| `GET/POST /query/<dataset_id>` | — (CORS do SE) | consulta; POST aceita filtros JSON |
| `GET /vendedores` | `X-API-Key` ou cookie | lista de vendedores |
| `GET /clientes-por-vendedor/<cod>` | `X-API-Key` ou cookie | carteira do vendedor |
| `POST /cache/invalidar` | — | invalida tudo ou `{"dataset_id": "cliente"}` |
| `GET/POST /painel` | senha → cookie | consulta visual (HTML inline) |

## Segurança (não afrouxar)

- **CORS restrito** a `https://sementesmana.softexpert.app` e `...-test`.
- Cookie `pauth` httponly, 8h (`_COOKIE_MAX_AGE = 28800`).
- `after_request`: nosniff, X-XSS-Protection, Referrer-Policy, e `Cache-Control: no-store` em `/query`, `/vendedores`, `/clientes-por-vendedor` (dado de cliente não fica em cache de browser).
- **Anti-injection**: código Protheus só passa se casar o padrão (letras+dígitos, ≤20 chars).
- Erro sanitizado: `_safe_error` trata `pymssql.OperationalError/DatabaseError/InterfaceError` sem vazar host, base (`P12_PROD`) ou query.

## Variáveis de ambiente

`PROTHEUS_DB_HOST`, `PROTHEUS_DB_PORT` (1433), `PROTHEUS_DB_USER`, `PROTHEUS_DB_PASSWORD`, `PROTHEUS_DB_NAME` (`P12_PROD`), `PROTHEUS_LOGIN_TIMEOUT` (10), `PROTHEUS_QUERY_TIMEOUT` (30), `PROTHEUS_DB_ENCRYPT`, `PAINEL_SENHA`.

## Deploy

Railway NIXPACKS, healthcheck `/health`, gunicorn 4 workers/timeout 30. O `nixpacks.toml` instala **`freetds-dev` e `freetds-bin`** — dependência nativa do `pymssql`; sem isso o build sobe e o runtime quebra na primeira query.

## Pendência arquitetural registrada no cockpit

> "IP shared no Railway — decisão arquitetural pendente (mitigações vs VPN/Dedicated IP)."

O Protheus é liberado por IP; Railway usa IP compartilhado. Antes de propor mudança de rede, ler a obs do catálogo e o vault.
