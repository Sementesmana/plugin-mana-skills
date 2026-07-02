---
name: simpleagro
description: >-
  SDK oficial do Simple Agro para o ecossistema Maná. SDK canônico da
  Maná Builder que consolida em 1 pacote reusável ~8.500 linhas de código SA
  espalhadas em 10 agentes: login OAuth AdonisJS + auto-relogin em 401, CRUD
  de Orders/Clients/Wallets/Properties, catálogos (Product Groups, Price Tables,
  TSI, tipos de venda/garantia/pagamento), engine de preço com juros no
  vencimento, filiais (Companies), safras, geolocalização, erros ERP com
  classificação. Use SEMPRE que um agente/app Maná precisar ler ou escrever
  no Simple Agro. Também use quando: criar app novo que fala com SA, migrar
  cópia inline de sa_client.py pra habilidade central, adicionar novo agente
  que faz login SA, precisar de preço com juros, listar pedidos com erro ERP,
  extrair coordenadas de pedidos, criar cliente novo, cadastrar propriedade,
  ver carteira do vendedor. Camada 2A da Maná Builder — SDK canônico de sistema legado.
---

# SDK Simple Agro — Maná Builder Camada 2A

> **Ponte oficial de leitura+escrita entre agentes Maná e o Simple Agro.**
> Antes: cada agente reimplementava login+XSRF+retry+parse+preço. Agora: 1 import.

## Quando usar

- Precisa listar pedidos, clientes, produtos, safras do Simple Agro
- Precisa criar/atualizar/cancelar pedido, cadastrar cliente ou propriedade
- Precisa de preço com juros aplicado a um vencimento
- Precisa detectar pedidos sem coordenada / com erro de integração ERP
- Está criando agente novo que fala com SA (não copie mais `sa_client.py`)
- Está migrando agente antigo pra parar de duplicar código

## Como consumir

```python
# 1. Instalar
# pip install "git+https://github.com/Sementesmana/mana-simpleagro.git@v0.1.1"

# 2. Setar env vars
#    SA_BASE_URL, SA_USERNAME, SA_PASSWORD, SA_SAFRA_ID, SA_GRUPO_ID

# 3. Usar
from mana_simpleagro import SimpleAgro
sa = SimpleAgro()
sa.login()   # opcional; on-demand em cada request

# Leitura
pedidos = sa.orders.list()
pedidos_do_cliente = sa.orders.list_por_cnpj("12345678000199")
cliente = sa.clients.buscar(cpf_cnpj="123")[0]

# Escrita
pid, numero = sa.orders.criar_pedido(cabecalho, itens, parcelas, observacao="...")

# Preço com juros
dados = sa.pricing.dados_produto("O790IPRO", tabela_id, "2026-08-30")
```

## Filosofia (você que compõe, não copia)

O SDK é **wrapper genérico** — não copie exemplos. Você (Cowork) lê a API do
módulo relevante, entende os parâmetros, e escreve código específico do que o
usuário pediu.

Exemplos:
- Usuário quer *"lançar pedido de 10 sacos de O790IPRO pra cliente X"* — você
  monta o cabeçalho + itens + parcelas usando `SimpleAgro().catalog`,
  `SimpleAgro().clients`, `SimpleAgro().pricing` como REFERÊNCIAS. Não copie um
  exemplo do agente-lancamento-pedido — use os wrappers como base e componha.
- Usuário quer *"quantos pedidos do fulano estão parados com erro ERP?"* — use
  `sa.erp.listar_classificado()` filtrando por CNPJ.

## Padrões que o SDK já cobre (não implemente de novo)

| Padrão | Onde |
|---|---|
| Login OAuth AdonisJS + XSRF | `SimpleAgroAuth` — automático |
| Cache de token 50min | `SimpleAgroAuth` — automático |
| Auto-relogin em 401 | `SimpleAgroClient.request` — automático |
| Formato pt-BR (`"1.234,56"`) | `fmt_ptbr`, `parse_ptbr` |
| Normalização CPF/CNPJ | `so_digitos`, `normalizar_cnpj` |
| Fórmula de juros no vencimento | `PricingAPI.dados_produto` — validada bit-a-bit |
| Retry inteligente em busca por nome | `ClientsAPI.buscar_por_nome(retry_palavras=True)` |
| Fuzzy match de produto | `CatalogAPI.obter_produto` |
| Classificação de erro ERP | `ErpAPI.classificar` |
| Detecção de geoloc ausente | `GeolocationAPI.pedidos_sem_coordenadas` |

## LGPD

SDK trafega **PII** (CPF/CNPJ, nome, telefone, endereço). Se for enviar dado
pra LLM depois, **pseudonimize antes** com `mana-habilidade-pseudonimizar-pii`.

## Se falta funcionalidade

Antes de duplicar código no agente:
1. Verifique se `SimpleAgro` já tem o método
2. Se não tem mas cabe no escopo do SDK → PR pro repo
3. Se é caso muito específico → tudo bem chamar `sa.client.get("/api/...")` cru

## Recursos

- **Repo:** https://github.com/Sementesmana/mana-simpleagro
- **README completo:** [README.md](./README.md)
- **Nota vault:** `ManaVault/06-Agentes-e-Skills/sdks/simpleagro.md`
- **ADRs:** Maná Builder (2026-06-26), Stack dados (2026-06-30)
