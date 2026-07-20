---
name: agente-integracoes
description: "Agente de integração SoftExpert ↔ Simple Agro para Sementes Maná. Consulta pedidos de venda por CPF/CNPJ no Simple Agro e sincroniza com grids do SoftExpert Workflow. Gerencia serviço Railway Flask com dois painéis web (/painel populador de grid, /painel-reais somente leitura com drill-down grupo econômico). Use este skill sempre que precisar trabalhar com o agente-integracoes — adicionar endpoints, corrigir sync de pedidos, modificar os painéis HTML, ajustar mapeamento de campos SA→SE, depurar erros de integração, implementar novas funcionalidades no Railway, ou entender a arquitetura SE↔SimpleAgro. Também use quando o usuário mencionar pedidos de venda, painel reais, painel comercial, Simple Agro, scred, scredito, grupo econômico ou qualquer integração entre SoftExpert e SimpleAgro."
---

# Agente Integrações — SoftExpert ↔ Simple Agro

Automatiza a consulta e sincronização de pedidos de venda do **Simple Agro** no **SoftExpert Workflow** da Sementes Maná LTDA.

## Arquitetura

```
SoftExpert Workflow (processo: gestaopedido / scred)
    │
    ▼ Atividade Sistêmica GET /pedidos-venda?idprocess=X&cpf_cnpj=Y
Railway Flask API  →  agente-integracoes-production.up.railway.app
    │
    ├── POST /api/auth/login  → Simple Agro (usuário dedicado automação)
    ├── GET /api/orders?safra.id=...  → filtra por CPF/CNPJ em Python
    │
    └── newChildEntityRecordList (SOAP) → insere itens na grid scredito do SE
```

## Serviço Railway

- **URL produção:** `https://agente-integracoes-production.up.railway.app`
- **Repo:** `Sementesmana/hiperautomacao-mana` (pasta `agente-integracoes/`)
- **Deploy:** automático via push GitHub
- **Start:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 30`

### Variáveis de Ambiente (Railway)

| Variável | Descrição |
|---|---|
| `SE_URL` | URL SoftExpert (ex: `https://sementesmana.softexpert.app`) |
| `SE_API_KEY` | API Key do SoftExpert |
| `SA_BASE_URL` | `https://sementesmana.api.simpleagro.com.br:3333` |
| `SA_USERNAME` | Usuário **dedicado** automação Simple Agro |
| `SA_PASSWORD` | Senha do usuário dedicado |
| `SA_SAFRA_ID` | ID da safra ativa (ex: `69a5d85cae03f50036ee2531` = 26/27) |
| `SA_GRUPO_ID` | ID grupo Semente de Soja (`610a8b743829fd00385c48c9`) |
| `PAINEL_SENHA` | Senha do /painel-reais (padrão: `mana2026`) |

## Formulários SoftExpert

| Item | Valor |
|---|---|
| Formulário pai | `gestaopedido` (tabela: `scred`) |
| Formulário filho | `gridgestaopedido` (tabela: `scredito`) |
| Relacionamento pai→filho | `importpedido1` (FK `ABC40RKER3DEQG2`) |
| Relacionamento grupo econômico | `gridgrupoecon` (tabela `parentxscred`) |

### Campos importantes da tabela `scred`

| Campo | Descrição |
|---|---|
| `reais` | Solicitação de Crédito |
| `limitecredaprov` | Limite de Crédito Aprovado |
| `cpfcnpj` | CPF/CNPJ do cliente principal |
| `inicnome` | Nome do vendedor |
| `nomeclientenovo` | Nome do cliente |
| `datasolicitacao` | Data da solicitação |
| `safra` | Safra (ex: `26/27`) |
| `prazo` | Prazo de pagamento |

## Endpoints da API Flask

### GET /pedidos-venda
Atividade Sistêmica do SE → insere pedidos na grid.

```
?idprocess=000123&cpf_cnpj=13.566.152/0004-40
```

Resposta:
```json
{ "status": "sucesso", "pedidos_inseridos": 5, "timestamp": "2026-03-29T10:00:00" }
```

### GET /consultar-sa?idprocess=X
Consulta SA somente leitura (não grava no SE). Retorna:
```json
{ "status": "sucesso", "pedidos": [...], "reais": 120000.0, "cpf_cnpj": "..." }
```

### GET /consultar-sa-grupo?idprocess=X
Consolida pedidos do CNPJ principal + filiais + grupo econômico (raiz CNPJ).
Retorna: `{ reais, limitecredaprov, grupos[], total_geral }`

### GET /listar-workflows
Retorna todos os workflows abertos da tabela `scred`. Usado pelo /painel-reais.

### GET /debug-scred?idprocess=X
Retorna todos os 206 campos do `scred` para debug.

### GET /health
Health check do serviço.

## Painéis Web

### /painel — Populador de Grid
- Busca workflow por ID no SE
- Consulta pedidos no Simple Agro
- Grava itens na grid `scredito` via SOAP
- Botão "Atualizar" executa sync

### /painel-reais — Consulta Somente Leitura ✅ Produção
- Senha: variável `PAINEL_SENHA` (padrão: `mana2026`)
- Auto-carrega todos os workflows ao abrir
- Filtros client-side: vendedor, cliente, ordem por valor
- Colunas: Workflow · Título · CPF/CNPJ · Vendedor · Cliente · Solicitação · Total SA · Saldo · 🔍
- Total SA carrega assincronamente por linha (`carregarTotaisLinha()`)
- Botão 🔍 abre modal com itens detalhados
- `?idprocess=X` na URL abre modal direto (link do SE)

## Scripts de Produção

Os arquivos de produção ficam em:
- `ORQUESTRADOR/agente-integracoes/agente_simpleagro.py` — core de integração (2215 linhas)
- `ORQUESTRADOR/agente-integracoes/app.py` — Flask API + painéis HTML (1776 linhas)

Os mesmos arquivos estão no repositório GitHub para deploy Railway.

## Mapeamento de Campos: Simple Agro → SE Grid (scredito)

```python
CAMPO_MAP = {
    "safra":          ["safra.descricao"],
    "filial":         ["filial.nome"],
    "numpedido":      ["numero"],
    "statuspedido":   ["status_pedido"],
    "pedidoprotheus": ["pedido_erp"],
    "dataemissaoped": ["order_created_at"],
    # ... ver agente_simpleagro.py para mapeamento completo
}
```

## Atenção: Sessões Simple Agro

O Simple Agro **derruba sessões simultâneas**. Use sempre um usuário dedicado para automação — nunca o usuário pessoal do vendedor.

## Lógica de Sync da Grid (Botão "Atualizar")

Regras de negócio para sync bidirecional:

- **Saem da grid SE:** pedidos `cancelado` ou `em cotação` no SA
- **Entram na grid SE:** pedidos novos válidos (não cancelado/em cotação) ainda não presentes
- **Ficam na grid SE:** pedidos `em aprovação` (novos ou antigos) e `aprovados`

Objetivo: sync real sem duplicar, refletindo estado atual do SA.

## Como Atualizar o Serviço

```bash
# 1. Editar os arquivos em ORQUESTRADOR/agente-integracoes/
# 2. Copiar para o repo GitHub local
cp ORQUESTRADOR/agente-integracoes/*.py repo-mana/agente-integracoes/
# 3. Commit + push → Railway deploy automático
git add agente-integracoes/
git commit -m "feat: descrição da mudança"
git push
```
