---
name: agente-estoque
description: Painel de controle de estoque de sementes por cultivar + módulo TSI (Tratamento Industrial de Sementes) da Sementes Maná LTDA. Flask + PostgreSQL no Railway que cruza estoque manual com pedidos do Simple Agro em tempo real e, desde 2026-09-09, traz o volume TRATADO do Protheus pelo gateway agente-protheus: a aba TSI mostra Vendido (SA) × Tratado (PRT) × Falta tratar por receita, com quebra por variedade no drill, de-para por CÓDIGO na tabela protheus_depara e a safra defasada UM ciclo (produção no Protheus × comercialização no SA). Inclui cadastro de produtos químicos, receitas, composição produto×dose, consolidado vivo, drill-down, filtros rápidos, snapshots, campanhas e exportação PDF/XLSX. Use SEMPRE no agente-estoque — endpoints, lógica de estoque, painel HTML, cálculos TON/Bag, integração SA, módulo TSI, de-para do Protheus, relatórios.
---

# Agente Estoque — Sementes Maná LTDA

Serviço Flask Railway que controla o estoque de soja por cultivar e o consumo previsto de produtos químicos de Tratamento Industrial de Sementes (TSI), cruzando dados manuais com pedidos vindos do Simple Agro API em tempo real.

## Localização do Código

- **Repo:** `Sementesmana/agente-estoque` (GitHub)
- **Clone local:** `C:\Users\Sementes Mana\Desktop\ORQUESTRADOR\agente-estoque\`
- **Script principal:** `app.py` (raiz, não em scripts/)
- **Módulo TSI:** `tsi/` (Blueprint Flask)
- **Railway:** project `Painel-estoque-sa` (production)
- **URL:** https://agente-estoque-sa-production.up.railway.app
- **Banco:** PostgreSQL Railway acoplado ao mesmo project

## Estrutura

```
agente-estoque/
├── app.py                    ← painel estoque + admin + endpoints
├── requirements.txt          ← flask, psycopg2, openpyxl, reportlab
├── Procfile, railway.toml
└── tsi/                      ← módulo TSI (Blueprint Flask)
    ├── __init__.py           ← init_tsi, bootstrap_tsi
    ├── calc.py               ← norm, conversor embalagem→bag, fórmula, consolidar_pedidos
    ├── consolidado.py        ← rodar_consolidado, drill_produto, filtros
    ├── routes.py             ← Blueprint + endpoints
    ├── seed.py               ← import xlsx → tsi_*
    ├── pdf.py                ← gerar_pdf_consolidado + gerar_pdf_estoque (reportlab)
    ├── templates.py          ← BASE_CSS + _sidebar + PAINEL_PLACEHOLDER_HTML
    ├── templates_admin.py    ← PRODUTOS_HTML + RECEITAS_HTML + CONFIG_HTML
    └── schema.sql            ← DDL de referência
```

## Endpoints

### Painel Estoque (principal)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/` (alias `/painel`) | Dashboard principal |
| GET | `/admin` | Painel admin para cadastrar/editar estoque |
| GET | `/api/estoque` | JSON com cultivares + métricas |
| GET | `/api/estoque/relatorio.pdf` | **PDF** com filtros `q`, `cultivar` (repetível — `?cultivar=A&cultivar=B`), `min_bag`, `min_qtd`, `min_saldo`, `min_pct`, `uso_semente`. Lido via `request.args.getlist("cultivar")`; `tsi/pdf.py` aceita lista ou string (compat). |
| GET | `/api/sa-nomes` | Nomes de cultivares do SA |
| POST | `/api/cultivar/rename` | Renomeia cultivar `{old_name, new_name}` |
| POST | `/api/cultivar/delete` | Remove cultivar `{name}` |
| POST | `/api/cache/refresh` | Força refresh do cache SA |
| GET | `/api/debug-sa-raw` | Pedidos brutos do SA |
| GET | `/api/debug-status` | Status únicos dos pedidos |

### Módulo TSI (Tratamento Industrial de Sementes)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/tsi` | **Painel consolidado** — consumo previsto por produto químico |
| GET | `/tsi/produtos` | CRUD produtos (catálogo + estoque) |
| GET | `/tsi/receitas` | CRUD receitas (composição produto × dose) |
| GET | `/tsi/config` | Pesos + **toggle SA/Sistema** |
| GET | `/api/tsi/consolidado` | JSON consolidado (filtros: safra_id, data_ini/fim, cliente_ids, variedade_norms, tratamento_norms) |
| GET | `/api/tsi/produto/<id>/drill` | Drill-down: pedidos × variedades × dose |
| GET | `/api/tsi/filtros` | Listas únicas pra dropdowns |
| GET | `/api/tsi/relatorio.pdf` | **PDF** do consolidado |
| GET/POST/PUT/DELETE | `/api/tsi/produtos[/id]` | CRUD produtos |
| GET/POST/PUT/DELETE | `/api/tsi/receitas[/id]` | CRUD receitas |
| GET/POST | `/api/tsi/config` | Configurações |
| POST | `/api/tsi/import-planilha` | Upload `DOSES TSI.xlsx` |

## Fórmulas

### Estoque (painel principal)
```
Kg = total_ton × 100   (fator interno — NÃO 1000)
SC(60kg) = Kg / 60
Sc200MIL = Kg / 33
Bag = Sc200MIL / 25
% Pedido = (qtd_pedida / estoque) × 100
```

**Exibição:** Bag arredondado pra inteiro.
**% Pedido:** vermelho se >100%, verde se ≤100%.

### TSI (consumo de produtos químicos)
```
consumo_ml = qtd_bag × dose(ml/100kg) × peso_bag_kg / 100
```

**Peso da bag** = `item.peso_embalagem` do SA (padrão) ou `peso_bag_kg_fallback` (quando `usar_peso_sistema=1`). Ver ADR `2026-05-13-origem-peso-bag-tsi` no ManaVault.

## Status SA Incluídos no Cálculo

```python
STATUS_INCLUIDOS = {"aguardando aprovacao", "integrado", "aprovado"}
```

Lista de **INCLUSÃO** (não exclusão), normalizada por NFD.

## Mapeamento Embalagem SA → Bag (TSI)

```python
EMBALAGEM_PARA_BAG = {
    "5 M":          1.0,      # bag (5 mi sementes)
    "5.0 MIL S":    1.0,
    "5,0 MIL S":    1.0,
    "BAG":          1.0,
    "200 M S":      1.0/25,   # SC200MIL
    "200 MIL S":    1.0/25,
    "SC200MIL":     1.0/25,
}
```
Fora desse mapa → "unidade desconhecida" (alerta amarelo no painel TSI).

## SimpleAgroClient — Login Correto

```python
url  = f"{self.base}/api/auth/login"
body = {"login": CONFIG["SA_USERNAME"], "senha": CONFIG["SA_PASSWORD"]}
# XSRF de: painel.simpleagro.com.br:3333/sales/login
```

Cache duplo no app.py (TTL 1800s, thread-safe):
- `_sa_cache` — resultado agregado de `fetch_sa_vendas()` (cultivar → vendas)
- `_pedidos_brutos_cache` — pedidos brutos do SA para o TSI

## Banco de Dados

### Estoque
```sql
cultivares (
    id SERIAL PK,
    nome VARCHAR(200) UNIQUE,
    nome_norm VARCHAR(200) UNIQUE,
    total_ton NUMERIC(14,3),
    updated_at TIMESTAMP
);
```

### TSI (criadas 2026-05-13)
```sql
tsi_produtos (id, nome, nome_norm UNIQUE, unidade L|KG, estoque_atual, ativo);
tsi_receitas (id, nome, nome_norm UNIQUE, descricao, ativo);
tsi_receita_itens (receita_id FK, produto_id FK, dose_ml_por_100kg);
tsi_config (chave PK, valor, descricao);
-- Chaves default: peso_bag_kg_fallback=835, peso_sacaria_kg_fallback=33, usar_peso_sistema=0
```

Bootstrap em `tsi/routes.py::bootstrap_tsi(conn)` — idempotente, chamado por `_bootstrap_tudo()` no app.py.

## Integração no `app.py`

```python
from tsi import init_tsi, bootstrap_tsi

_pedidos_brutos_cache = {"data": None, "ts": 0}
_pedidos_brutos_lock  = threading.Lock()

def get_pedidos_sa_cached() -> list:
    """Cache 30min separado pra TSI."""
    ...

init_tsi(app, get_db, get_pedidos_sa_cached)

def _bootstrap_tudo():
    init_db()
    with get_db() as conn:
        bootstrap_tsi(conn)
```

## Painel Principal — UI

- **Coluna Saldo (Bag) no drill de Venda/Devolução (2026-09-26):** o que
  ainda não foi faturado do pedido = `quantidade − item.quantidade_faturada`
  do SA (campo ausente = nada faturado). Hover mostra o faturado; rodapé
  soma "Saldo a faturar" respeitando o filtro.
- **Coluna Terceiro no drill de Venda/Devolução (2026-09-26):** vem de
  `item.classificacao_produto_terceiro` do pedido SA (ADTM / ADTP; TERC é
  exibido como **GOIAS - TERC** e é o único fora do total ADTM + ADTP; vazio =
  própria). Pedido antigo sem o campo e com `produto_terceiro = true` sai pelo
  prefixo do `codref` (050 = ADTM, 070 = ADTP — igual ao sufixo do SKU no
  catálogo do SA). Gravado como `terceiro` em cada linha de `pedidos`. O
  rodapé mostra, ao lado do total, **ADTM + ADTP** e **GOIAS - TERC** somados por item
  (pedido com itens mistos soma certo em cada balde) e respeita o filtro.

- **Sidebar verde** com Estoque, Inserir Estoque + grupo TSI (Painel, Produtos, Receitas, Configurações)
- **Busca de cima** filtra a tabela inteira por substring (não só seleciona dropdown)
- **5 KPIs respondem aos filtros:** Cultivares, Estoque Total, Qtd Pedida, Saldo Disponível, Saldo Negativo
- **Chart.js top 12** cultivares (por estoque + pedido)
- **Tabela com filtros por coluna:** min bag/qtd/saldo/pct, **cultivar (dropdown de checkboxes com busca, Todas/Limpar; seleção múltipla — vazio = todas)**, uso semente; sortable; expand inline mostra pedidos
- **Filtro de cultivar — implementação:** botão `#f_nome_btn` + painel `#f_nome_drop` (position:fixed posicionado via JS pra escapar do `overflow:hidden` do `.table-card`); checkboxes em `#f_nome_list`; busca interna em `#f_nome_search`. JS: `_getCultivarSel()`, `_atualizaLabelCultivar()`, `toggleCultivarDrop()`, `filtraCultivarDrop()`, `marcarTodasCultivar()`, `onCultivarCheck()`. Fecha em outside-click e scroll de viewport.
- **Botão "Exportar PDF" (dourado)** entre Atualizar e Inserir Estoque

## Painel TSI — UI

- **Filtros:** safra, intervalo de datas, multi-select de clientes/variedades/tratamentos
- **4 KPIs:** Bags TSI, Volume L, Volume KG, Produtos em alerta
- **Tabela mestre por produto** com drill-down
- **Painéis colapsáveis:** Pedidos sem receita (órfãos) e Unidades desconhecidas
- **Botão "⬇ Exportar PDF" (verde)** no header

## Geração de PDF (`tsi/pdf.py`)

- `gerar_pdf_consolidado(dados, filtros, filtros_disponiveis) → bytes`
- `gerar_pdf_estoque(cultivares, filtros, safra_descricao) → bytes`

Layout:
- Paisagem A4 com cabeçalho verde Maná
- KPIs em cards, tabela mestre com linhas em alerta (vermelho)
- **PDF de estoque inclui detalhamento de pedidos por cultivar** (Nº, Data, Cliente, Vendedor, Filial, Qtd, Uso, Status)
- Textos longos em `Paragraph` para wrap automático

## Volume TRATADO do Protheus (2026-09-09)

A aba TSI cruza o que foi **vendido** (Simple Agro) com o que foi **tratado**
(Protheus), por receita e por variedade.

```
Vendido (SA)    bags pedidas com aquele tratamento    ← já existia, chamava-se
                                                        "Bags tratadas" e mentia
Tratado (PRT)   NP9_TRATO = '1' no Protheus
Falta tratar    Vendido − Tratado
```

**Nunca calcule "falta tratar" contra o SALDO do Protheus.** Saldo é o que está
no armazém hoje, já líquido do que embarcou: tratei 50, tenho 10, vendi 60 →
faltam 10, não 50. Contra o saldo a conta erra sempre para mais.

### Tela de de-para = CONFERÊNCIA completa (2026-09-26)

`/tsi/depara` abre em "Todos": lista TODO código do Protheus nos dois eixos
(`protheus_client.codigos_todos`, inclusive volume zero), com a coluna **Como
vinculou** (automático = nome normalizado igual ao cadastro; à mão = data da
escolha + obs; pendente; ignorado = código 00) e alertas: dois códigos no mesmo
destino, vínculo à mão com nome diferente, destino que sumiu. Card **Sem par no
Protheus** = receitas/variedades que nenhum código aponta (conferência nos dois
sentidos). O dropdown de variedade é `cultivares` ∪ variedades dos pedidos SA
(`opcoes_destino`, marcadas "só no SA") — o POST valida contra a mesma lista. O
casamento AUTOMÁTICO continua só contra o cadastro (a tela não mostra vínculo
que a conta não usa); variedade só-do-SA entra por escolha manual.

### TSI por Receita: Devolvido, Entregue e linha por pedido (2026-09-29)

Colunas: Vendido · Tratado · **Devolvido** · Falta tratar · **Entregue** ·
**Falta entregar**. Devolvido = lançamento manual do Pedido de Compra tipo
Devolução, agora com **tratamento obrigatório** (`compras.tratamento`, receita
ou SEM TRATAMENTO) — ABATE do vendido: Falta tratar = vendido − devolvido −
tratado; Falta entregar = vendido − devolvido − entregue. Entregue = faturado
no SA (`item.quantidade_faturada`, convertido para bag pela mesma razão da
quantidade). Devolução antiga sem tratamento vai para
`res["devolucao_sem_tratamento"]` (linha vermelha à parte), nunca chutada numa
receita. Filtro de cliente/vendedor exclui as devoluções manuais (cliente
delas é texto livre). Drill: Variedades (padrão) e Consumo; aba Pedidos saiu.
"+" da variedade = uma linha por PEDIDO (cliente, pedido, vendido, devolvido,
entregue, falta entregar), sem Tratado/Falta tratar. Código:
`calc._acum_ped`/`_var_out` e `consolidado._aplicar_devolucoes`.

### Card "Saldo de Tratamento" (2026-09-26)

Abaixo do "TSI por Receita": saldo de HOJE por SKU do Protheus (código +
B1_DESC cheio, cultivar, tratamento, tipo pelo prefixo 040/420 Própria · 050
ADTM · 070 ADTP · 071 GH), com Saldo / Empenhado / Bloqueado / Disponível em
bags. Fonte: dataset `saldo_produto` do agente-protheus (SBF010 somada por
lote × armazém; empenho SDC010 e bloqueio SDD010 pré-agregados — join direto
multiplicava o lote). Caminho: `protheus_client.buscar_saldo_produto` (cache
5 min, fail-soft) → `GET /api/tsi/saldo-produto` → card (filtros cultivar,
tratamento, tipo, filial, busca; ordenação; TOTAL). UM fora do UM_PARA_BAG
aparece como "?" com a quantidade crua — não vira bag inventada. Carrega à
parte do consolidado. **Só a safra comercial corrente** (26/27 em set/2026 =
`SAFRA 25/26` de produção no Protheus, via `safra_producao_de_comercial`);
`?safra=27/28` troca, `PROTHEUS_SAFRA` força. Lote de safra velha não aparece.

### Linha SEM TRATAMENTO (2026-09-25)

O quadro "TSI por Receita" mostra, **depois** da linha TOTAL e fora dela, uma
linha cinza `SEM TRATAMENTO` com as bags vendidas sem TSI (tratamento `00` /
label "SEM TRATAMENTO" / vazio). Ela vem em `res["sem_tratamento"]`
(`{receita, bags, qtd_pedidos, variedades}`), **não** em `res["receitas"]`, e
não soma em `bags_total`, `bags_por_fornecedor` nem em campanha nenhuma
(Corteva/Syngenta) — quem consome `receitas` (campanhas, xlsx, pdf) não a vê.
Tratado/Falta ficam "—" (não se aplica). Some com filtro de fornecedor ativo, e
com filtro de tratamento que não inclua SEM TRATAMENTO. Drill: Pedidos
(`/api/tsi/receita/SEM%20TRATAMENTO/drill`) e Variedades.

### O caminho

```
agente-protheus /query/estoque  →  protheus_client.py  →  tsi/consolidado.py
                                   (X-API-Key, cache 5min, idade do dado)
```

`protheus_client.py` é a única porta: nada aqui abre conexão com o SQL Server.
Env: `PROTHEUS_URL`, `PROTHEUS_API_KEY` (consumidor `estoque`), e
`PROTHEUS_SAFRA` opcional para fixar a safra.

### ⭐ A safra é defasada UM ciclo

`SAFRA 25/26` no Protheus é **produção**; a mesma semente é comercializada como
safra **26/27** no Simple Agro. Sempre. Casar 26/27 com 26/27 devolve conjunto
VAZIO e parece bug de integração. Por isso a safra **não** é derivada do filtro
do painel — o gateway já tem o padrão certo, que se corrige sozinho na virada.

### De-para por CÓDIGO, na `protheus_depara`

Tabela `protheus_depara (tipo, codigo, nome_protheus, destino_norm, obs)`,
bootstrap idempotente no boot. **Nasce vazia**: os 9 tratamentos e as 21
cultivares casam sozinhos por `nome_norm` (medido nas duas direções). Só entra
exceção. Precedência: **override de pessoa > casamento automático > pendência**.

Chave é o CÓDIGO (`TRATAMENTO_COD`, `CULTIVAR_COD`), nunca o nome: renomear no
Protheus mantém o código e o mapa não quebra; tratamento novo chega como código
não mapeado, que é o único caso que pede decisão humana.

### ⚠️ Normalizadores são INJETADOS, não copiados

O `app.py` passa `norm_nome` e o `norm` do `tsi/calc.py` via
`protheus_client.registrar_normalizadores`. A primeira versão copiava as duas
funções e a cópia envelheceu **no mesmo dia** (o `norm_nome` ganhou
`_strip_regiao`). Normalizador divergente **não dá erro** — só devolve pendência
a mais. Regra: quem grava o `nome_norm` é quem manda no `nome_norm`.

E são dois normalizadores diferentes: `cultivares.nome_norm` mantém acento,
`tsi_receitas.nome_norm` tira.

### Regras da tela

- **`—` e `0` são distintos.** Zero é "não tratou nada"; travessão é "a ponte
  com o Protheus caiu". Igualar os dois fabrica alarme falso.
- **`falta` negativa aparece**, em azul, em vez de ser cortada em zero: tratado
  acima do vendido é informação (UBS adiantou, ou casamento errado).
- **Nada some calado.** Código sem destino e embalagem fora do mapa aparecem na
  faixa acima da tabela **com o volume em bags**.
- **Pendência só com volume.** Código com zero tratado (`00 = SEM TRATAMENTO`,
  cultivar só com lote não tratado) fica fora: lista que nunca esvazia é lista
  que ninguém olha.

### Validação (2026-09-09, safra 25/26)

`Vendido 6.032 · Tratado 3.661 · Falta 2.371`, com 89 linhas do gateway. O KPI
"Bags TSI" mostra 6.040 — a diferença de 8 bags são os pedidos órfãos, que o
painel de órfãos já contava.

⚠️ **Em aberto:** 8 receitas com INOC/ARVÁTICO somam 407 bags com tratado zero.
Se a UBS trata pela receita BASE e aplica o inoculante à parte, esse volume está
somando dentro do `CAIXA VIGOR E PRAGA` e do `FORTENZA DUO INTACTA`. Pergunta
para a operação, não para o código.

### A tela de de-para — `/tsi/depara`

`TSI — De-para Protheus` na barra lateral. Mostra **todos** os códigos vistos no
Protheus, não só os pendentes: dá para conferir o que casou sozinho, e não só
consertar o que falhou. Ordem: pendência primeiro, maior volume no topo.

Três situações, e a tela distingue as três: `automático` (casou por nome),
`à mão` (alguém escolheu — e essa escolha vence sempre) e `pendente`.

`POST /api/tsi/depara` **valida o destino contra o cadastro**: aceitar texto
livre criaria mapa apontando para nada, que falha calado — justamente o que esta
tela existe para evitar. Salvar não invalida o cache do Protheus: o mapa é lido
do banco a cada consolidado, então bater no ERP a cada salvamento seria custo à
toa.

## Variáveis de Ambiente Railway

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | PostgreSQL (injetada pelo Railway) |
| `SA_BASE_URL` | `https://sementesmana.api.simpleagro.com.br:3333` |
| `SA_USERNAME`, `SA_PASSWORD` | Credenciais SA |
| `SA_SAFRA_ID` | `69a5d85cae03f50036ee2531` (soja 26/27) |
| `SA_GRUPO_ID` | `610a8b743829fd00385c48c9` (soja) |
| `PAINEL_SENHA` | Senha do painel admin |
| `PROTHEUS_URL` | `https://agente-protheus-production.up.railway.app` |
| `PROTHEUS_API_KEY` | chave do consumidor `estoque` no `API_KEYS` do gateway |
| `PROTHEUS_SAFRA` | opcional — fixa a safra de PRODUÇÃO (ex.: `SAFRA 25/26`) |

## Como Modificar

### Adicionar coluna na tabela de cultivares
1. Calcular e incluir o campo em `build_estoque_view()`
2. Adicionar `<th>` em `PAINEL_HTML`
3. Adicionar `<td>` em `renderTable()` JS
4. Atualizar `applyFiltersAndSort` se quiser filtro/ordenação
5. Adicionar coluna no PDF (`gerar_pdf_estoque`)

### Adicionar tratamento TSI
- UI: `/tsi/receitas` → "+ Nova receita"
- Planilha: editar `DOSES TSI.xlsx`, subir via `/tsi/produtos` → "Importar planilha"

### Adicionar status SA
```python
STATUS_INCLUIDOS = {"aguardando aprovacao", "integrado", "aprovado", "novo"}
```

### Mudar TTL do cache SA
```python
SA_CACHE_TTL = 1800  # segundos
```

## Amarração Cultivar (SA ↔ BD)

Cruzamento por `nome_norm` (uppercase + sem espaços extras). Se nome divergir entre SA e BD, saldo não calcula. Resolver via Admin → editor inline → renomear pra bater com SA.

## Dependências

```
flask==3.0.3
flask-cors==4.0.1
requests==2.32.3
urllib3==2.2.2
gunicorn==22.0.0
psycopg2-binary==2.9.9
openpyxl==3.1.5
reportlab==4.2.5
```

## Notas relacionadas no ManaVault

- `06-Agentes-e-Skills/agente-estoque.md` — nota canônica
- `08-Decisoes/2026-05-13-origem-peso-bag-tsi.md` — ADR sobre toggle SA/Sistema
- `08-Decisoes/2026-05-02-caminho-A-padrao-migracao.md` — padrão de migração preservando PG↔Flask

## Painel de Estoque: switch Convertido × Por embalagem (2026-09-30)

- Base: 1 bag = 5 milhões de sementes. `tsi.calc.EMBALAGEM_PARA_BAG` é a tabela única
  (5M = 1 · 2,5M "2.5 MIL S" = 0,5 · 200 mil = 1/25). O painel usa a mesma via `_embalagem_item`.
- `fetch_sa_vendas` grava por pedido `embalagem`, `fator`, `quantidade_eq`, `faturado_eq`, `saldo_eq`;
  `quantidade` continua FÍSICA. `build_estoque_view` acrescenta `qtd_bag_eq`, `devolucao_bag_eq`, `saldo_bag_eq`.
- Os campos antigos (`qtd_bag`, `saldo_bag`…) NÃO mudaram: `/api/estoque/totais`, gestor-estoque e celular
  seguem somando quantidade física até o Dayan autorizar a troca (ver `/api/diag/embalagens`).
- Tela: switch no cabeçalho da tabela (localStorage `mana_modo_emb`). **Convertido** troca os campos pelos `_eq`
  (drill sem etiqueta; unidade física no tooltip da quantidade). **Por embalagem** abre a variedade em uma linha por embalagem,
  em unidade física; estoque fica na linha 5M, meio bag/sacaria entram com estoque 0 (saldo = −venda) até o saldo do Protheus por embalagem.
  Cards do resumo e top-lista ficam sempre convertidos.
- Embalagem fora da tabela: fator None, soma 1:1 e aparece em vermelho "fora da tabela" — não some.
- Filtro **Embalagem** (multi, junto de Uso/Estado): filtra por PEDIDO (`p.embalagem`, sem valor = 5M), igual Estado/Uso —
  recalcula venda/devolução/saldo e o drill. Opções montadas dos pedidos (5M, 2,5M, 200 mil e qualquer outra que aparecer).
  No modo Por embalagem filtra a própria linha (`_emb`). Estoque (produzido/compra) não tem embalagem: no Convertido
  continua o da variedade inteira.

## Faturado pela NOTA FISCAL da carga (2026-10-05)

- O `quantidade_faturada` do item do SA não sobe enquanto o agendamento não é aprovado, mesmo com carga
  Finalizada e NF emitida (260000040108/2: 4 cargas com NF = 212 bags, item com faturado 0).
- Regra Maná (igual `agente-comercio-revendas/cargas.py`): faturado = agendamento com NF. `_aplicar_faturado_carga`
  lê `/api/orders-scheduling` (agendados) + `/api/charge-montage` (NF), casa por `id_agrupamento + variedade`,
  e soma a qtd agendada com NF por pedido × produto × tratamento × embalagem.
- O item fica com `quantidade_faturada = max(SA, NF de carga)`; o original vai em `quantidade_faturada_sa` e
  `faturado_fonte = "nf_carga"`. Vale para o Saldo a faturar do Estoque e o Entregue do TSI.
- Falha nas cargas/agendamentos: mantém o faturado do SA (nunca zera) e serve o último mapa bom. Conferência:
  `/api/diag/faturado/<pedido>`.

## Bloqueio automático de variedade negativa no Simple Agro (2026-10-08) — `bloqueio_sa.py`

- Gatilho: `saldo_bag_eq < 0` (Saldo Convertido do painel). Alcance: o PRODUTO da variedade no grupo SEMENTE DE SOJA
  (`status=false` bloqueia todos os SKUs). Escrita: `PUT /api/productgroups/{GRUPO_SOJA_ID}/products/{produto_id}`
  com `{"status": bool}`, sempre conferida relendo o catálogo (status mudou e nº de variações igual; senão para a rodada).
- Rotina: thread leve (5 em 5 min) roda 1× por dia depois de `BLOQUEIO_SA_HORA` (padrão 06:30 BRT), lock
  `pg_try_advisory_lock(7310026)` entre os 2 workers, registro em `sa_bloqueio_run`. Só bloqueia; nunca libera.
  Rebloqueia o que alguém liberou com saldo ainda negativo. SA fora/452/sem dado: não marca o dia e tenta de novo.
- Travas: `BLOQUEIO_SA_ATIVO=1` liga (padrão desligado); `BLOQUEIO_SA_MAX` (15) aborta se negativas demais;
  sem vendas do SA não bloqueia nada. Log de tudo em `sa_bloqueio_log` (`/api/bloqueio/log`).
- Painel: cadeado ao lado da variedade (vermelho = bloqueada; laranja = liberada com saldo negativo; cinza = liberada).
  Clique bloqueia/libera via `POST /api/bloqueio/variedade` com header `X-Bloqueio-Pin` = `BLOQUEIO_SA_PIN`
  (sem PIN configurado, o cadeado não escreve). `POST /api/bloqueio/rodar` roda a regra na hora (mesmo PIN).

## Saldo de Tratamento: filtros, Falta entregar, visão Lotes e Reserva de lotes (2026-10-09)

- Filtros Cultivar e Tratamento viraram multi-seleção com busca (× limpa); "Limpar filtros" zera tudo.
- Coluna **Falta entregar** + drill (+) por código: `GET /api/tsi/falta-entregar` casa o item do pedido SA pelo
  `codref` (= código Protheus, comparado sem zeros à esquerda). Falta = quantidade − faturado (faturado já corrigido
  pela NF da carga). Entram aguardando aprovação / aprovado / integrado; ficam fora reprovado e tipo DEVOLUÇÃO.
- Lotes ficam DENTRO do drill (+) do código, em abas no estilo da composição do saldo: **Falta entregar | Lotes** (não há mais switch no topo). Lotes = `GET /api/tsi/saldo-lote` ← dataset `saldo_lote` do agente-protheus (mesma
  SELECT do saldo_produto, aberta por lote × armazém; autorizado pelo Dayan em 09/10/2026). Livre = Disponível − Reservado.
- **Reserva de lotes** (`/reservas`, tabela `lote_reservas`): lote × código (opcional) × cliente × quantidade (bags).
  Lançar/editar/excluir na tela ou subir .xlsx/.csv (Lote, Cliente, Quantidade; Código e Obs opcionais) —
  soma/atualiza pela chave lote+código+cliente, nada é apagado. Reserva cujo lote não está no Protheus aparece em
  `reservas_sem_lote` (aviso na visão Lotes).
