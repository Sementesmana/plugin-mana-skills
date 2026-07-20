---
name: agente-estoque
description: Painel de controle de estoque de sementes por cultivar + módulo TSI (Tratamento Industrial de Sementes) para Sementes Maná LTDA. Serviço Flask no Railway com PostgreSQL que cruza estoque manual com pedidos do Simple Agro em tempo real. Inclui módulo TSI com cadastro de produtos químicos, receitas (tratamentos), composição produto×dose, consolidado vivo cruzando pedidos SA × receitas, drill-down, filtros, e exportação PDF nos dois painéis. Use este skill sempre que precisar trabalhar com o agente-estoque — adicionar endpoints, corrigir lógica de estoque, modificar painel HTML, ajustar cálculos TON/Bag, corrigir integração SA, mexer no TSI (produtos/receitas/consolidado/origem do peso), gerar relatórios PDF, ou entender a arquitetura do serviço.
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

## Variáveis de Ambiente Railway

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | PostgreSQL (injetada pelo Railway) |
| `SA_BASE_URL` | `https://sementesmana.api.simpleagro.com.br:3333` |
| `SA_USERNAME`, `SA_PASSWORD` | Credenciais SA |
| `SA_SAFRA_ID` | `69a5d85cae03f50036ee2531` (soja 26/27) |
| `SA_GRUPO_ID` | `610a8b743829fd00385c48c9` (soja) |
| `PAINEL_SENHA` | Senha do painel admin |

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
