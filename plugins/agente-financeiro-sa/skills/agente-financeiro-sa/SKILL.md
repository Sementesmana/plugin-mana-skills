---
name: agente-financeiro-sa
description: >
  Visão financeira e comercial dos pedidos Simple Agro — Sementes Maná LTDA ("Painel Comercial SA").
  Flask no Railway, cache 20 min, 6 abas: Recebimentos/Mês, Por Pedido, Evolução, Clientes (LTV),
  Por Produto e Por Vendedor. A aba Por Vendedor traz ranking por receita com drill-down duplo
  (Vendedor→Cliente→Pedido e Vendedor→Cultivar) e filtros em cascata client-side (Vendedor, Cliente,
  Status, Uso da semente, Variedade, Obtentora, Tecnologia) sobre /api/dataset; enrichment do catálogo
  SA (/api/productgroups) injeta obtentora/tecnologia/terceiro. Use SEMPRE que trabalhar com o
  agente-financeiro-sa — painel HTML, filtros, cálculos de total/frete, parcelas, aba Por Vendedor,
  enrichment, /api/dataset, endpoints. Também quando mencionar: painel financeiro, painel comercial SA,
  parcelas, vencimentos, total liq+frete, visão por vendedor, por produto, cultivar, obtentora,
  tecnologia, filtros em cascata, enrichment SA, recebimentos por mês, refresh de cache.
---

# Agente Financeiro SA ("Painel Comercial SA") — Sementes Maná

Serviço Flask no Railway que lê pedidos do Simple Agro e apresenta visão financeira e comercial
consolidada: parcelas/vencimentos por cliente, evolução, LTV, análise por cultivar e ranking por
vendedor — com filtros e estatísticas. Somente leitura no SA; não grava no SoftExpert.

## Infraestrutura

| Item | Valor |
|---|---|
| URL produção | `https://painel-comercial-sa-production.up.railway.app` |
| Projeto Railway | `Painel Comercial SA` |
| Root Directory | **VAZIO** (código na raiz do repo — Caminho A; NÃO voltar pra `/agente-financeiro-sa`) |
| Repositório | `github.com/Sementesmana/agente-financeiro-sa` (repo **isolado**) |
| Branch | `main` |
| Arquivos principais | `app.py`, `agente_financeiro_sa.py` (na raiz) |

## Variáveis de ambiente (Railway)

| Variável | Descrição |
|---|---|
| `SA_BASE_URL` | `https://sementesmana.api.simpleagro.com.br:3333` |
| `SA_USERNAME` | Usuário da API Simple Agro |
| `SA_PASSWORD` | Senha da API Simple Agro |
| `SA_SAFRA_ID` | ID da safra 26/27 — `69a5d85cae03f50036ee2531` |
| `SA_GRUPO_ID` | ID do grupo Semente de Soja — `610a8b743829fd00385c48c9` |
| `PAINEL_SENHA` | Senha do painel web (padrão: `mana2026`) |

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/financeiro` | JSON consolidado por cliente; filtros: `?cliente=`, `?vendedor=`, `?agente=`, `?status=`, `?safra_id=` |
| GET/POST | `/api/financeiro/refresh` | Invalida cache (força novo fetch SA) — requer `X-API-Key` |
| GET | `/api/produtos` | Análise por cultivar (bags/receita/share/cross-sell); filtros `?vendedor=`, `?status=`, `?uso=`, `?safra_id=` |
| GET | `/api/dataset` ⭐ | **(2026-05-25)** Pedidos achatados + itens **enriquecidos** (cultivar/obtentora/tecnologia/terceiro/bags/receita) + parcelas. Sem filtros server-side — o painel filtra client-side. Consumido pela aba Por Vendedor e pela cascata. |
| GET | `/api/safras` | Lista de safras do SA (nome normalizado, flag ativa) |
| GET | `/painel-financeiro` | Painel HTML protegido por senha (cookie `fauth`) |
| GET | `/painel-financeiro-embed-v2` ⭐ | Sem login — embedado no SoftExpert via iframe |

## Arquitetura do código

```
app.py
  ├── /health
  ├── /api/financeiro          → buscar_financeiro_com_cache()
  ├── /api/financeiro/refresh  → invalidar_cache()
  ├── /api/produtos            → buscar_produtos_com_cache()
  ├── /api/dataset             → buscar_dataset_com_cache()   (2026-05-25)
  ├── /api/safras              → buscar_safras_com_cache()
  └── /painel-financeiro       → HTML/CSS/JS inline (f-string gigante + strings ev_/ltv_/produto_/vend_)

agente_financeiro_sa.py
  ├── SimpleAgroClient
  │     ├── login() + get_orders()
  │     ├── carregar_catalogo()  → GET /api/productgroups/{grupo}   (2026-05-25)
  │     └── enriquecer(orders)   → injeta item_tecnologia/obtentora_nome/terceiro
  ├── processar_pedidos()        → agrega por cliente, extrai parcelas
  ├── processar_por_produto()    → agrega por cultivar + cross-sell
  ├── montar_dataset()           → achata orders enriquecidos p/ client-side   (2026-05-25)
  ├── buscar_*_com_cache()       → TTL 20 min, memória + arquivo (/tmp) p/ multi-worker
  └── invalidar_cache()
```

## Painel HTML — abas (`_vistaAtual`) e filtros

| Aba | `_vistaAtual` | Fonte | Filtros |
|---|---|---|---|
| Recebimentos/Mês | 0 | `/api/financeiro` | `ms-mes-*`: Cliente, Vendedor, Agente, Status |
| Por Pedido | 1 | `/api/financeiro` | `ms-pedido-*`: Cliente, Vendedor, Agente, Status |
| Evolução | 2 | `/api/financeiro` | safras extras (`ev-safras`) |
| Clientes (LTV) | 3 | `/api/financeiro` | `ms-ltv-*` |
| Por Produto | 4 | `/api/produtos` | `ms-prod-*`: Vendedor, Status, Uso |
| **Por Vendedor** ⭐ | **5** | **`/api/dataset`** | **`ms-vend-*` (cascata): Vendedor, Cliente, Status, Uso da semente, Variedade, Obtentora, Tecnologia** |

### Aba "Por Vendedor" (2026-05-25)

Injetada via `vend_html` (markup) + `vend_js` (script) — strings normais (chaves JS simples),
diferente do `html = f"""` principal (chaves escapadas `{{ }}`). Ranking de vendedores por receita;
clicar num vendedor expande com **toggle Cliente ↔ Cultivar**:
- **Cliente** → clientes do vendedor → clicar cliente → pedidos (status, bags, receita, nº parcelas, total parcelas).
- **Cultivar** → cultivares do vendedor (bags/receita/pedidos).

Funções-chave (JS): `_vendLoad`, `_vendApply` (agregação), `_vendBuildFilters` (recalcula opções em
cascata), `_vendApplyFilters` (chamado pelo `_msApply` no prefixo `ms-vend-`), `_vendRenderTable`,
`_vendDrillHtml`. Estado: `_vendData`, `_vendDrill`, `_vendLast`, `_vendExpV`/`_vendExpC`.

### Filtros em cascata client-side

Reaproveitam a máquina multi-select `ms-*` global (`msInit`, `msGetSelected`, `_msState`). Ao mudar
um filtro, `_vendBuildFilters(false, triggerId)` recalcula as opções **de cada outro filtro**
considerando os demais selecionados (cascata), preservando seleção e sem fechar o dropdown em uso.
Filtros de **pedido** (vendedor/cliente/status/uso) cortam o pedido inteiro; filtros de **item**
(variedade/obtentora/tecnologia) exigem ≥1 item compatível e só agregam os itens que casam.
Safra fica no seletor de cabeçalho — trocar recarrega o dataset (`_vendOnReload` no `carregar()`).

## Enrichment SA (obtentora / tecnologia / terceiro)

`/api/orders` **não traz obtentora/tecnologia inline**. `carregar_catalogo()` busca
`GET /api/productgroups/{SA_GRUPO_ID}`, indexa por nome (UPPER) e id (com variações aninhadas), e
`enriquecer()` injeta `item_tecnologia`, `obtentora_nome`, `terceiro` em cada item. Roda uma vez por
fetch (cacheado junto dos orders). **Fallback silencioso (akita):** catálogo off → campos vazios, o
painel não quebra.

> ⚠️ **3ª cópia** dessa lógica (junto de `agente-pedidos` e `agente-premiacao`) — drift consciente,
> ADR `2026-05-25-agente-financeiro-sa-enrichment-e-visao-vendedor`. Pendência: endpoint central
> unificado. Se obtentora/tecnologia vierem vazias em produção, ajustar as chaves tentadas no
> `enriquecer()` conforme os rótulos reais do catálogo SA.

## ⚠️ Regra crítica: frete

O valor com frete está em `pagamento.parcelas[i].valor_parcela` — **NÃO** em
`preco_frete_tabela_item` (que vem 0 em muitos pedidos). A visão financeira por cliente usa o total
do produto (soma de `total_preco_item`) com fallback pra soma das parcelas; as parcelas exibidas
usam `valor_parcela`. Confirmado com a Simple Agro.

## ⚠️ Multi-worker (gunicorn) + cache em arquivo

Cada worker tem cache em memória isolado. Além do cache em memória, há cache em arquivo
(`/tmp/fin_sa_cache/*.pkl`, rename atômico) compartilhado entre workers. Funções que precisam do
cache devem chamar `buscar_*_com_cache()` para garantir população no worker atual.

## _safe_float — parsing de números SA

```python
def _safe_float(val) -> float:
    """Trata formato brasileiro: '111.345,00' → 111345.0"""
    try:
        s = str(val).strip()
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        return float(s)
    except (ValueError, TypeError, AttributeError):
        return 0.0
```

## Login Simple Agro

```python
url  = f"{base}/api/auth/login"
body = {"login": SA_USERNAME, "senha": SA_PASSWORD}
headers = {
    "Origin":  "https://sementesmana.painel.simpleagro.com.br:3333",
    "Referer": "https://sementesmana.painel.simpleagro.com.br:3333/sales/login",
}
# XSRF-TOKEN: obtido via GET no painel antes do POST de login
```

## Como fazer deploy/atualização (repo isolado — Caminho A)

```bash
# Clone do repo isolado (token gerado em github.com/settings/tokens — revogar após uso)
cd ~/Desktop && git clone https://TOKEN@github.com/Sementesmana/agente-financeiro-sa.git _deploy-fin-sa

# Copiar arquivos modificados (código vive na RAIZ do repo)
cp ~/Desktop/ORQUESTRADOR/agente-financeiro-sa/app.py _deploy-fin-sa/
cp ~/Desktop/ORQUESTRADOR/agente-financeiro-sa/agente_financeiro_sa.py _deploy-fin-sa/

# Conferir o diff (espera-se só inserções) e commitar/pushar
cd _deploy-fin-sa
git diff --stat
git add -A && git commit -m "feat: descrição"
git push origin main     # Railway auto-deploy em ~2 min
```

> ⚠️ NÃO usar `railway up`. Deploy é sempre via `git push`.
> ⚠️ Root Directory do projeto Railway fica **VAZIO** (Caminho A). NÃO voltar pra `/agente-financeiro-sa`.
> Antes do push: `python -m py_compile app.py agente_financeiro_sa.py` (o `app.py` é um f-string gigante — pega erro de chave).

## Erros conhecidos e soluções

| Erro | Causa | Solução |
|---|---|---|
| Parcelas sem frete | `preco_frete_tabela_item=0` no SA | Usar `valor_parcela` das parcelas |
| Obtentora/Tecnologia vazias na aba Por Vendedor | Rótulos do catálogo SA diferentes das chaves tentadas | Ajustar chaves em `enriquecer()` / conferir `/api/productgroups` |
| "Pedido não encontrado no cache" | Gunicorn multi-worker — cache vazio no worker | Chamar `buscar_*_com_cache()` no início da função |
| `SyntaxError: unterminated triple-quoted string` ao compilar no sandbox | Mount do sandbox trunca arquivos grandes recém-editados | Falso positivo — compilar no Git Bash local |
| Filtros cascata não atualizam | `_msApply` sem branch `ms-vend-` | Garantir branch que chama `_vendApplyFilters(id)` |
```
                                                                                                                                                                                                                                                                                                                                                                            