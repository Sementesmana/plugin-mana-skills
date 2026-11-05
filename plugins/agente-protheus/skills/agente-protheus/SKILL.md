---
name: agente-protheus
description: "Gateway REST de LEITURA do Protheus da Sementes Maná (Flask/Railway, conecta direto no SQL Server via pymssql, não via dataset do SE). Expõe datasets catalogados em /query/<dataset> com auth obrigatória (X-API-Key por consumidor, CORS restrito ao SE, cookie no painel). Use SEMPRE no agente-protheus: dataset novo, cache, auth, CORS, pymssql/FreeTDS, timeouts. Também quando mencionar SA1010, SE1010, SE2010, SE5010, SC7010, NP9010, SBF010, P12_PROD, estoque de semente por cultivar × tratamento, safra de produção × comercialização (defasada um ciclo), faturamento/faturamento_detalhe, E1_VENCORI, natureza 400101/400103, RA, royalty, romaneio, NJJ010/NJK010/NJM010, datasets ubs_* do ubs-mana, dataset restrito por consumidor (403), cache desligado por dataset."
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
| `titulos_pagar` | SE2010 | `FILIAIS` | acervo completo, aberto e baixado (~23,7 mil linhas) |
| `titulos_receber` | SE1010 | `FILIAIS` | idem, ~5,9 mil linhas |
| `pedidos_compra` | SC7010 | `FILIAL`, `EMISSAO_DE`, `ENTREGA_DE` | pedidos em aberto, item a item |
| `estoque` | NP9010 + SBF010 (+ SB5010/NKD010) | `SAFRA`, `FILIAL` | semente por cultivar × tratamento |
| `faturamento` | SE1010 **agregada** | `FILIAIS`, `EMISSAO_DE` | faturado por cliente × vencimento original |
| `faturamento_detalhe` | SE1010 + SA1010 | **`CLIENTES`**, `FILIAIS`, `EMISSAO_DE` | as NOTAS das raízes pedidas, linha a linha |
| `faturamento_sementes` | SFT010 + SD1/SD2 + SA1/SA2 | `FILIAIS`, `DATA_DE`, `DATA_ATE` | livro fiscal de semente item a item (agente-rrm) |
| `ubs_recepcao` 🔒 | NJJ010 + NJK/NJ0/NJR/SB1/SB5/NP4/SFT | `ANO` | romaneios de recepção do ano — aba Cargas do ubs-mana |
| `ubs_romaneio` 🔒⛔cache | NJJ010 + cadastros | **`ROMANEIO`**, `FILIAL` | cabeçalho do romaneio **com CPF/CNPJ e CNH** |
| `ubs_romaneio_classificacao` 🔒⛔cache | NJK010 | **`ROMANEIO`**, `FILIAL` | classificação/descontos |
| `ubs_romaneio_comercializacao` 🔒⛔cache | NJM010 | **`ROMANEIO`**, `FILIAL` | entidade/contrato/nota por item |
| `ubs_empresa` | SYS_COMPANY | **`FILIAL`** | dados da filial (cabeçalho do romaneio) |
| `ubs_producao` 🔒 | SD3010 (TM 002 com OP) + NP9/CTT/SB1/SB5/NKD | `SAFRAS` | produção por lote — aba Produção |
| `ubs_descarte` 🔒 | SD3010 RE7→DE7 (SOJA GRAO) | `ANO` | descarte — aba Produção |
| `ubs_perda` 🔒 | SFT010 saída, finalidade BAIXA, SOJA DEST | `ANO` | perda |
| `ubs_estoque_lote` 🔒 | SBF010 0201 + NP9/SB8/SDD/SDC/SC2/SC9 | — | estoque por endereço/lote — Estoque e Detalhe |
| `ubs_estoque_saldo` 🔒 | SBF010 0201 (próprio) ⟗ SB6010 (terceiros) | — | saldo MANA/SGL — Estoque Novo |
| `ubs_venda` 🔒 | SFT010 saída SPED, finalidade VENDA | `ANO` | venda de semente de soja |
| `ubs_metas` 🔒 | NN3010 filial 02 + NNV | — | metas por talhão — Metas e Planejamento |

🔒 = restrito ao consumidor `ubs-mana` (outros levam **403**) · ⛔cache = nunca entra no cache em memória.

São **vinte e cinco** (18 conferidos em `/datasets` em 2026-11-05 + 7 `ubs_*` da Fase 2b); `saldo_produto` e `saldo_lote` ainda sem linha nesta tabela. Falta `pedidos` de venda (SC5010). **Dataset novo entra no catálogo** — não criar rota solta.

⚠️ Versões antigas desta skill listavam dois ou quatro, e mandavam procurar estoque na SB1010. A **SB1010 é cadastro, não saldo**: o saldo de semente é por ENDEREÇO (SBF010) e a ficha do lote é a NP9010.

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

### O dataset `estoque` — três grandezas que não se confundem

```
QTD_PRODUZIDA   o que a UBS fichou            NP9010, histórico
QTD_TRATADA     o que passou pelo TSI         NP9_TRATO = '1'
QTD_SALDO       o que está no armazém HOJE    SBF010, saldo
```

A **SBF010 é saldo**: lote que zera SOME dela. A **NP9010 é a ficha do lote** e sobrevive ao lote zerar (medido: 476 de 1.038 lotes da 25/26 já sem saldo). Produzido − saldo = o que **já embarcou**.

**"Falta tratar" = Vendido(SA) − TRATADO**, jamais `Vendido − saldo atual`: tratei 50, tenho 10, vendi 60 → faltam 10, não 50. Contra o saldo a conta erra sempre para mais, no tamanho do que já saiu.

⭐ **A SAFRA É DEFASADA UM CICLO.** `SAFRA 25/26` aqui é **produção**; a mesma semente é comercializada como safra **26/27** no Simple Agro. Sempre. Casar 26/27 com 26/27 devolve conjunto VAZIO e parece bug de integração. O dataset **deriva** a safra da data (`_safra_producao_padrao`), e o `_validar_safra` aceita `25/26` ou `SAFRA 25/26`.

**Os de-para casam sozinhos** (medido nas duas direções): tratamento por `NKD_DESCRI` via `B5_TRATAM` contra `tsi_receitas` — **9 de 9**; variedade por `NP9_CTVDES` contra `cultivares.nome_norm` — **21 de 21**. E **código ↔ nome é 1:1**, então mapa se faz por **código** e exibe o nome: renomeação no Protheus mantém o código e não quebra; tratamento novo aparece como código não mapeado.

⚠️ **Nunca a descrição do produto.** O `B1_DESC` escreve `FORTENZA DUO` onde a receita é `FORTENZA DUO INTACTA`, e mistura `O780CE` com `NEO780CE`.

⚠️ **`NP9_UM` sempre no grão.** Quatro embalagens (`5.0 M` = bag de 5 milhões, `200 M` = 1/25, `140 M`, `S40`); as duas últimas nem estão no mapa do agente-estoque. Hoje a safra corrente é `5.0 M` pura — o que segura o número é a base, não a query.

⚠️ **`NP9_TRATO` pode discordar do produto.** Em 09/09 havia 4 lotes / 17 bags de SKU tratada (`71KA72 · FORTENZA DUO INTACTA`) com o flag em `2`. O flag erra para o lado seguro. Quem consome **mostra** a divergência, não escolhe em silêncio.

Campo de domínio se pergunta à **SX3010** (`X3_CBOX`), nunca se deduz: `NP9_TRATO` = `1=Sim, 2=Não, 3=Troca de Produto`. E dois campos que parecem úteis estão **vazios em 100%**: `NP9_FORMUL` e `NP9_DOCD3`.

Validação (safra 25/26, todas as filiais, 09/09/2026): **89 linhas, 1.038 lotes, 22.590 produzidas, 3.661 tratadas, 11.960 de saldo**. Os 3.661 fecham por outro caminho na SD3010 (`TM 002 / PR0`, estorno em branco).

### O dataset `faturamento` — agregado, e o que ele NÃO faz (2026-09-17)

Alimenta o controle de lastro do `agente-pedidos`
(`Saldo c/ Garantia = Aprovado com Garantia − Total Faturado`). Agrega a SE1010 por
`(COD_CLIENTE, VENCIMENTO_ORIGINAL, TIPO, NATUREZA)`: 6.319 títulos viram algumas centenas de
linhas em vez de 6 mil registros para somar no navegador.

**Não reuse o `titulos_receber` para isso** — ele traz `E1_VENCTO` e `E1_VENCREA` mas **não traz o
`E1_VENCORI`**, vem linha a linha e tem filial travada em 0201+0202.

`COD_CLIENTE` é a **raiz sem DV**: 8 dígitos = CNPJ, 9 = CPF. Medido contra a SA1010 em 2026-09-17:
3.673 de 8 → 100% CNPJ, 2.645 de 9 → 100% CPF, zero sem cadastro. A `LOJA` fica fora do
agrupamento de propósito — o pedido do Simple Agro consolida "CNPJ Principal + Filiais" e a raiz
reproduz esse recorte.

⚠️ **`VALOR`, não `SALDO`.** `E1_VALOR` é o faturado; `E1_SALDO` é o que falta receber. Quem somar
o saldo vê o faturamento encolher conforme o cliente paga.

⚠️ **Devolve TIPO e NATUREZA em vez de classificar aqui**, e os dois são necessários. Medido:
`NF` 4.953 (R$ 671,9 mi), **`RA` 1.015 (R$ 277,0 mi — recebimento ANTECIPADO)**, `NCC` 150,
`PR` 47 (royalty), mais `EMP`/`RC`/`FOL`/`TX`/`CH`/`FT`. Tratar "não-NCC" como faturado inflaria a
conta em ~41%. E a natureza sozinha também não resolve: a `400101` é **NF e RA**, e a NF tem
**duas** naturezas (`400101` e `400103`). O consumidor classifica de forma POSITIVA — só `NF`
entra, só `NCC` abate, natureza ∈ {400101, 400103} — e o resto fica de fora **e é contado**.

⚠️ **Filial ABERTA por padrão** (`_validar_filiais_opcional`). Título em filial fora da lista
sumiria em silêncio e o saldo apareceria MAIOR do que é — o erro que libera faturamento sem lastro.

A safra **não** é filtro: `E1_CODSAF` está vazio em 86% dos títulos. O recorte sai da chave do
consumidor (vencimento da parcela a-prazo).

> **Acrescentar `NATUREZA` foi mudança quebrante.** O consumidor classifica por ela; sem o campo,
> tudo cairia em ignorados e o faturado viraria R$ 0,00 (saldo cheio). Ele tem guarda que devolve
> "não sei" nesse caso, mas **o gateway sobe primeiro**.


### O dataset `faturamento_detalhe` — as NOTAS, não o total (2026-09-19)

Irmão do `faturamento`: aquele responde **quanto** por (cliente, vencimento); este responde
**quais notas**. Serve à lupa do `painel-reais`, onde a pessoa abre um grupo econômico e confere
nota por nota contra a garantia.

| filtro | obrigatório? | |
|---|---|---|
| `CLIENTES` | **SIM** | raízes separadas por vírgula (8 ou 9 dígitos), teto de 60 |
| `FILIAIS` | não | vazio = todas |
| `EMISSAO_DE` | não | AAAAMMDD |

⚠️ **`CLIENTES` é obrigatório e sem ele a query nem é montada** — devolve `SELECT TOP 0 1`. Sem
esse filtro isto seria um dump da SE1010 inteira por HTTP, exatamente o que o `faturamento`
agregado existe para evitar. Lista vazia é conjunto vazio, **nunca** a base inteira.

Campos: `COD_CLIENTE`, `LOJA`, `NOME_CADASTRO`, `RAZAO_SOCIAL`, `PREFIXO`, `NOTA`, `PARCELA`,
`TIPO`, `NATUREZA`, `EMISSAO`, `VENCIMENTO_ORIGINAL`, `VENCIMENTO`, `VENCIMENTO_REAL`, `VALOR`,
`SALDO`, `DATA_BAIXA`.

**Os TRÊS vencimentos vão juntos de propósito**, e discordam em 11,1% dos títulos (medido):

* `VENCIMENTO_ORIGINAL` (`E1_VENCORI`) — o que **casa** com a parcela do pedido; imutável na prorrogação
* `VENCIMENTO` (`E1_VENCTO`) — o vigente, que a prorrogação move
* `VENCIMENTO_REAL` (`E1_VENCREA`) — ajustado para dia útil; é o que o banco cobra e o que a
  pessoa reconhece no extrato

Mostrar só um faz alguém jurar que o sistema está errado quando os três divergem.

**Dois nomes, e os dois são necessários:** `NOME_CADASTRO` é o `E1_NOMCLI` — nome da FAZENDA
truncado em 20 caracteres ("FAZ SÃO JOSE") — e `RAZAO_SOCIAL` vem da SA1010. Quem confere a nota
dentro do Protheus vê o primeiro; quem confere contra o grupo econômico precisa do segundo.

⚠️ **Não classifica nada.** Devolve `TIPO` e `NATUREZA` crus, e o consumidor aplica a MESMA regra
do agregado. Duas classificações para o mesmo dado divergem no primeiro tipo novo — e aí o detalhe
contradiz o total logo acima dele, que é o jeito mais rápido de um painel perder a confiança. No
`agente-pedidos` isso é uma função só (`protheus_faturado.classificar`), chamada pelos dois lados.

⚠️ **Sem cache, de propósito.** É leitura sob demanda de UM grupo, não o agregado que a carteira
inteira usa; cachear guardaria dezenas de recortes diferentes para servir cada um uma vez.


### Os datasets `ubs_*` — porte fiel do ubs-mana (2026-11-05)

Vieram de `ubs-mana/server/erp/consultas/*.sql` (app do Wesley, migrando do SRV-APP-IA para o Railway). **Mesmos nomes de coluna** do .sql original, para o app não mudar; as regras DESC_TIPO, CLASSE e o corte "SOJA GRAO" ficam no consumidor (`server/erp/fontes.js`), como no Power Query.

- **Leitura sem bloqueio:** cada consulta abre com `SET NOCOUNT ON; SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;` (`_UBS_PREAMBULO`). Seguro porque `_get_connection` abre conexão NOVA a cada consulta — se um dia virar pool, esse SET passa a valer para os outros datasets.
- **Romaneio:** `ROMANEIO` obrigatório, só letras e dígitos, **zeros à esquerda preservados** (a chave é filial + código com zeros). `FILIAL` vazia = primeira filial que tem o código (`_ubs_resolver_romaneio`). Inválido ou inexistente → lista vazia, sem tocar na NJJ.
- **Recepção:** `ANO` fora de 2000..2100 cai no ano corrente de SP. Cacheia 5 min (o sincronizador do app roda a cada 15).
- ⚠️ **Defeitos herdados, mantidos de propósito:** o pivot da NJK não filtra `D_E_L_E_T_` nem `NJK_FILIAL` (UMI/IMP podem misturar filiais com o mesmo código de romaneio) e os joins de SB1010/DA4010 não filtram `D_E_L_E_T_`. Porte fiel para conferir número a número contra o app atual no paralelo; **corrigir nos dois lados juntos ao fim do paralelo**.

### Os datasets `ubs_*` da Fase 2b — abas que vinham do Power BI (2026-11-05)

Porte de `ubs-mana/scripts/pbix-consultas/*.m` (o .pbix "BI - Maná - UBS"). Regras:

- **Mesmos FROM/JOIN/WHERE do .m**, inclusive os que multiplicam linha; **SELECT só com as colunas que as telas usam** (`exportar_pbix.py` → `COLUNAS`). Venda e Perda traziam CNPJ/nome do parceiro: ficaram fora.
- **"Ano corrente" virou `ANO`**: `campo BETWEEN CAST(%s AS char(8)) AND CAST(%s AS char(8))`. O CAST é porque o pymssql manda `str` como `N'...'` (nvarchar) e a comparação com char(8) forçaria conversão implícita na coluna. `SAFRAS` (produção) aceita texto com vírgula ou lista JSON; padrão = as 3 safras fixas do .pbix.
- ⚠️ **pymssql + `%`**: com parâmetros, todo `%` de LIKE vai como `%%`; sem parâmetros, `%` simples. Um teste confere os 7.
- **Texto sai como char do Protheus (espaços no fim)** e data vazia sai `''`: aparar/tratar é do consumidor (`texto()` em `server/erp/fontes.js` do ubs-mana). As classificações do Power Query (OPERAÇÃO REPASSE, CLASSIFICAÇÃO ADTM/ADTP) também.
- Insumos **não** tem dataset: o .m depende de duas sub-consultas que não vieram com o código. Tela "Em desenvolvimento" no ubs-mana.
- ⚠️ **Defeitos herdados do .pbix, mantidos para conferir número a número no paralelo** (corrigir nos dois lados juntos depois):
  - `ubs_estoque_saldo`: FULL OUTER JOIN Próprio × Terceiros **só pelo código do produto** → N lotes × M terceiros = N×M linhas (infla saldo).
  - `ubs_estoque_lote` / `ubs_estoque_saldo`: joins de SDD/SDC (bloqueio/empenho) e SC2/SC9 podem repetir a linha do endereço.
  - `ubs_perda` / `ubs_venda`: joins de SF3/SD2/SA1/SA2 podem repetir item.
  - `ubs_metas`: NN3010 sem filtro `D_E_L_E_T_`.
- Volume hoje (snapshot do .pbix): fEstoque 281 linhas, Estoque 748 — longe do teto de cache (`CACHE_MAX_LINHAS = 5000`); se passar, a aba vai direto ao SQL a cada abertura.


Duas chaves opcionais no catálogo, genéricas — servem para qualquer dataset futuro com dado pessoal:

- `"consumidores": ["ubs-mana"]` → `consumidor_pode()` + 403 na rota `/query`. Só passam chaves de `API_KEYS` com esses nomes; **cookie do painel e `PAINEL_SENHA` legada não passam**. Sem a chave = aberto a qualquer autenticado (comportamento de sempre).
- `"cache": False` → o resultado nunca entra nem sai do cache em memória.

O gateway entrega CPF/CNH **cru** ao ubs-mana; **mascarar por permissão é papel do app**.


| Rota | Auth | O que faz |
|---|---|---|
| `GET /health` | — | status + conectividade (mostra `"database": "protheus"`, nome genérico de propósito) |
| `GET /datasets` | — | lista o catálogo |
| `GET/POST /query/<dataset_id>` | `X-API-Key` ou cookie | consulta; POST aceita filtros JSON |
| `GET /vendedores` | `X-API-Key` ou cookie | lista de vendedores |
| `GET /clientes-por-vendedor/<cod>` | `X-API-Key` ou cookie | carteira do vendedor |
| `POST /cache/invalidar` | `X-API-Key` ou cookie | invalida tudo ou `{"dataset_id": "cliente"}` |
| `GET/POST /painel` | senha → cookie | consulta visual (HTML inline) |

## Segurança (não afrouxar)

- **CORS restrito** a `https://sementesmana.softexpert.app` e `...-test`.
- Cookie `pauth` httponly, 8h (`_COOKIE_MAX_AGE = 28800`).
- `after_request`: nosniff, X-XSS-Protection, Referrer-Policy, e `Cache-Control: no-store` em `/query`, `/vendedores`, `/clientes-por-vendedor` (dado de cliente não fica em cache de browser).
- **Anti-injection**: código Protheus só passa se casar o padrão (letras+dígitos, ≤20 chars).
- Erro sanitizado: `_safe_error` trata `pymssql.OperationalError/DatabaseError/InterfaceError` sem vazar host, base (`P12_PROD`) ou query.

## Variáveis de ambiente

`PROTHEUS_DB_HOST`, `PROTHEUS_DB_PORT` (1433), `PROTHEUS_DB_USER`, `PROTHEUS_DB_PASSWORD`, `PROTHEUS_DB_NAME` (`P12_PROD`), `PROTHEUS_LOGIN_TIMEOUT` (10), `PROTHEUS_QUERY_TIMEOUT` (30), `PROTHEUS_DB_ENCRYPT`, `PAINEL_SENHA`, `API_KEYS`.

## Auth — chave por consumidor

`API_KEYS` é `nome:chave,nome2:chave2`. O log registra `[AUTH] consumidor=<nome>`, então dá pra saber quem chamou e revogar um sem derrubar os outros. Consumidores: `financeiro`, `estoque` e `ubs-mana` (este com o nome EXATO `ubs-mana` — é o que libera os datasets 🔒; nome diferente = 403 em tudo).

⚠️ Chave **sem** o `nome:` na frente o parser **descarta em silêncio** — sem erro e sem log, ela simplesmente não existe e o consumidor toma 401. E `_API_KEYS` é lido no import: chave nova só vale depois do restart.

A `PAINEL_SENHA` ainda é aceita como chave, por compatibilidade — é o que o SoftExpert usa. Mas consumidor NOVO entra em `API_KEYS`: senha de painel é credencial de pessoa, e girá-la derrubaria integração.

## Deploy

Railway NIXPACKS, healthcheck `/health`, gunicorn 4 workers/timeout 30. O `nixpacks.toml` instala **`freetds-dev` e `freetds-bin`** — dependência nativa do `pymssql`; sem isso o build sobe e o runtime quebra na primeira query.

## Pendência arquitetural registrada no cockpit

> "IP shared no Railway — decisão arquitetural pendente (mitigações vs VPN/Dedicated IP)."

O Protheus é liberado por IP; Railway usa IP compartilhado. Antes de propor mudança de rede, ler a obs do catálogo e o vault.
