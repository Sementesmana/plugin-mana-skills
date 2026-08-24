---
name: agente-pedidos
description: Ponte de LEITURA SoftExpert ↔ Simple Agro da Sementes Maná LTDA + painel-reais da carteira de crédito. Flask no Railway, somente leitura no SE (nada é gravado no formulário). O SE chama /pedidos-venda como Fonte de Dados REST na atividade de crédito — o agente lê o cpf_cnpj do scred via SOAP fm_ws, autentica no SA com usuário dedicado, busca pedidos Soja da safra, expande o grupo econômico pelos CNPJs do campo grupoeconomico e mapeia SA→grid SE via CAMPO_MAP (fallbacks por campo: o SA renomeia campo sem aviso). Primeiro consumidor do banco-mana com schema dedicado agente_pedidos — data lake lake-first (workflows, detalhe, totais, atividades, tempos, gaps) com fallback ao vivo. Use SEMPRE no agente-pedidos — Fonte de Dados REST do SE, CAMPO_MAP, grupo econômico, data lake, painel-reais, situação de crédito, tempos de atividade, gaps sem CRE. Também quando mencionar: /pedidos-venda, /painel-reais, /api/situacao-credito, lake-first, 452 single-session, bridge SE-SA somente leitura, /api/prioridade, alta/média/baixa/não aplicável, observação do cliente, triagem da fila de crédito.
---

# agente-pedidos — ponte de leitura SE ↔ Simple Agro

> **Somente leitura no SoftExpert.** Nada é gravado em formulário. O SE consome dados ao vivo (ou do lake) via Fonte de Dados REST.

## O que é

Duas funções no mesmo serviço:

1. **Fonte de Dados REST do SE** — quando alguém abre a atividade de crédito, o SE chama `/pedidos-venda?idprocess=XXX` e recebe a tabela de pedidos do Simple Agro daquele cliente.
2. **Painel de carteira (`/painel-reais`)** — visão consolidada dos processos de crédito abertos × pedidos SA, com situação de crédito, tempos de atividade e gaps.

Stack: Python 3.11 + Flask + Gunicorn no Railway · `requests` (SA REST + XSRF) · SE SOAP (`fm_ws`/`wf_ws`) · PostgreSQL (`banco-mana`, schema `agente_pedidos`).

## Pipeline do /pedidos-venda

```
SoftExpert (Fonte de Dados REST)
   │  GET /pedidos-venda?idprocess=XXX
   ├── 1. SE SOAP fm_ws    → lê cpf_cnpj do formulário scred
   ├── 2. SA Auth          → login com usuário DEDICADO à automação
   ├── 3. SA API           → pedidos SOJA / SAFRA 26/27 por CNPJ
   ├── 4. Grupo econômico  → soma os CNPJs do campo `grupoeconomico` (separados por vírgula)
   ├── 5. CAMPO_MAP        → JSON SA → campos da grid SE
   └── JSON → SE renderiza a tabela na atividade
```

`/pedidos-venda` **não exige senha** — quem chama é o SE, que já tem a própria autenticação. As rotas de painel exigem `X-Painel-Senha` ou `?senha=`.

## Por que somente leitura (decisão que não deve ser revertida)

As versões v1/v2 **gravavam** os pedidos no formulário do SE. Resultado: pedido cancelado ficava vivo no SE e pedido novo não entrava — estado intermediário para sincronizar é dívida garantida. A Fonte de Dados REST elimina o sync: o SE sempre lê o retrato atual.

## CAMPO_MAP — fallback por campo

O Simple Agro **não tem API versionada**: campo muda de nome sem aviso. Cada campo do SE aponta para uma lista de nomes possíveis:

```python
"nomecliente": ["cliente_nome", "cliente.nome"],
"produto":     ["produto_nome", "produto.nome"],
```

Monitorar `[WARN] campo X não mapeado` no log — é o detector de drift do ERP. Ao adicionar campo novo, **sempre** com lista de fallbacks, nunca com nome único.

## Data lake (schema `agente_pedidos` no banco-mana)

Primeiro consumidor do `banco-mana` pelo agente (ADR `mana-data-gateway`, 2026-06-30). Schema **dedicado — nunca `public`**; fail-soft se `BANCO_MANA_URL` não estiver configurado (o serviço continua servindo ao vivo).

Padrão **lake-first** em todas as leituras caras: se existe snapshot, serve do lake com `"fonte": "lake"`; senão calcula ao vivo. Chaves: `workflows`, `detalhe:<idprocess>`, `detalhe-cnpj:<digits>`, `totais`, `usos`, `atividades`, `tempos`, `gaps`.

- `POST|GET /api/atualizar-data-lake` — recalcula os snapshots (cron + botão)
- `GET /api/data-lake-status` — quando cada bloco foi atualizado
- `GET /api/tempos?live=1` — força cálculo ao vivo, ignorando o lake

## Endpoints

| Rota | Auth | O que faz |
|---|---|---|
| `GET /health` | — | status + variáveis de ambiente |
| `GET /pedidos-venda` | — | **Fonte de Dados REST do SE** (a razão de existir) |
| `GET /sa-readonly-by-cnpj` | senha | pedidos SA por CNPJ (lake-first) |
| `GET /listar-workflows`, `/api/workflows` | senha | processos de crédito abertos no SE |
| `GET /consultar-sa`, `/consultar-sa-grupo`, `/api/pedidos-sa` | senha | detalhe SE+SA de 1 workflow (lupa), com grupo econômico |
| `GET /api/painel-bundle` | senha | payload consolidado do painel |
| `GET/POST /api/situacao-credito` | senha | lê/grava a situação por `idprocess` (estado do agente, no banco-mana) |
| `GET/POST /api/prioridade` | senha | lê/grava **prioridade da análise + observação**, por `cnpj_raiz` (banco-mana) |
| `GET /api/vencimentos` | senha | vencimento da **última parcela** por nº de pedido (lake-first) — coluna Vencimento da lupa |
| `GET /api/totais-financeiro`, `/api/usos-semente`, `/api/vencimentos`, `/api/atividades`, `/api/tempos`, `/api/gaps-sem-cre` | senha | agregados do painel (lake-first) |
| `GET /painel`, `/painel-reais` | `?senha=` | painéis HTML (somente leitura / carteira consolidada) |

## Prioridade + Observação — a triagem da fila de crédito

Duas perguntas que o painel não respondia: **por onde começar** (40 CREs abertas, todas iguais na tela) e **quem nem devia estar aqui** — há cliente que, por decisão de política, não passa por análise. Enquanto esse último entrava na conta, inflava o Descoberto e derrubava a Cobertura, medindo um risco que ninguém tem.

Coluna **Prioridade** (select) + **Observação** (texto livre) no `/painel-reais`, ao lado de CPF/CNPJ, no padrão manual da Situação do Crédito: mexeu → POST → banco-mana.

- **Quatro níveis:** `alta` · `media` · `baixa` · `nao_aplicavel`. Não Aplicável é o fim da régua de urgência, não um eixo separado.
- **Chave = CNPJ-raiz (8 dígitos), não `idprocess`.** A decisão é sobre o CLIENTE: vale pro grupo econômico inteiro, pras linhas vermelhas sem CRE (que não têm `idprocess`) e pras CREs que ele abrir depois.
- **Ausência de linha = "Sem prioridade"**, que é diferente de "Média": `Alta` e *"ninguém triou ainda"* precisam ser distinguíveis, senão a coluna nasce mentindo que a carteira toda foi analisada. O filtro tem a opção pra varrer o que falta triar.
- **Prioridade e observação na mesma linha, POST com MERGE.** A tela manda um campo só; o servidor lê o estado atual antes de gravar — senão escrever a observação zeraria a prioridade. Sem prioridade **e** sem observação → a linha é apagada.
- **Observação não filtra e não re-renderiza** (roubaria o foco de quem está digitando na linha de baixo); prioridade re-renderiza, porque muda o recorte. Limite 500 caracteres.
- **O painel abre sem os "Não Aplicável"** e o `✕ Limpar` volta a esse padrão, não a "mostrar tudo". Pra conferir os excluídos, marcar `Não Aplicável` no filtro.
- **Vale pro portal inteiro** da aba Solicitações — tabela, cards de KPI, cobertura, funil/Kanban "Onde está" e Exportar Excel — porque entra no `_passaFiltros`, que é a fonte única do recorte. A aba **Indicadores (tempos) não é afetada**: ela lê o WFHISTORY, cujo universo inclui processos encerrados que a lista de abertos não conhece.
- **Ordenação "Prioridade ▼ (Alta primeiro)"** no dropdown Ordenar, rankeando todos juntos (com e sem CRE).
- **O rodapé da tabela avisa** quantos ficaram de fora por política. Número que encolhe sem explicação vira KPI mentiroso.

**Migração 2026-08-24** (`agente_pedidos.migracoes`): a coluna anterior era binária (Elegibilidade, aplicável/não aplicável, viveu 1 dia) — quem estava `nao_aplicavel` virou **`baixa`**. Roda **uma vez**, guardada por linha de controle: sem isso todo deploy reescreveria por cima de quem fosse marcado "Não Aplicável" de novo depois. Usa `to_regclass` pra checar a tabela antiga — o `SELECT` direto numa tabela ausente abortaria a transação e deixaria a migração pendente pra sempre. A tabela antiga não é apagada.

## Vencimento na lupa

Coluna **Vencimento** = data da **última parcela** do pedido (quando ele termina de ser pago), não a da primeira.

- **Fonte: `/api/financeiro` do agente-financeiro-sa**, casado por `order.numero` (mesma string dos dois lados) — não o `pagamento.parcelas` da listagem crua do SA, que é aninhado e a listagem trunca aninhado. O Painel Comercial SA já renderiza N parcelas desse array em produção: é a evidência de que o campo chega inteiro *por lá*, e a fonte agregada estável é o padrão da casa desde os totais de 2026-06-30.
- **`max()` sobre data parseada**, nunca sobre string: `"01/05/2027" < "30/08/2026"` em texto, e o pedido com parcela à vista + a prazo devolveria a data errada.
- Montado **antes** dos filtros de status/a-prazo em `_calc_totais` — a lupa mostra pedido cancelado e à vista, que também têm vencimento. `_calc_totais` retorna 4 valores.
- Lake-first (chave `vencimentos`), no bundle **fora do gate `faltando`**. Sem o mapa a célula mostra **⏳** (reingerir o lake), não `—`; `—` é reservado pra pedido que o financeiro não conhece.

## Variáveis de ambiente

`SE_URL`, `SE_API_KEY` (JWT) · `SA_BASE_URL`, `SA_USERNAME`, `SA_PASSWORD`, `SA_SAFRA_ID`, `SA_GRUPO_ID` · `BANCO_MANA_URL` · `PAINEL_SENHA`.

IDs fixos SA: safra 26/27 `69a5d85cae03f50036ee2531` · grupo Soja `610a8b743829fd00385c48c9`.

## ⚠️ Usuário dedicado no Simple Agro

O SA é **single-session**: quando o mesmo login entra em outro lugar, a sessão ativa cai (HTTP 452) e os requests em andamento morrem. O agente **precisa** de usuário/senha exclusivos da automação — um login manual de alguém durante o dia derruba a integração inteira. A cura estrutural desse problema é justamente o data lake.

## Deploy

`git push` → Railway auto-deploya em ~2 min. **Nunca `railway up`.** Validar por `/health` + log + teste funcional no painel.

## Cuidados ao mexer

- **Não voltar a gravar no SE.** Se pedirem "salva os pedidos no formulário", é a v2 de novo — leia a seção acima antes.
- **Falha não vira dado:** erro de transporte levanta exceção; lista vazia significa "não há pedidos", nunca "o SA recusou". Não persistir vazio no lake nem sobrescrever snapshot bom com falha.
- **Payload diz de quando é:** as respostas carregam `fonte` (lake/ao vivo) e timestamp — manter isso ao criar endpoint novo.
- O `README.md` do repo está **defasado** (descreve só o `/pedidos-venda`; o app tem 21 rotas, painel-reais e o data lake). Ao mexer, atualizar o README junto.
