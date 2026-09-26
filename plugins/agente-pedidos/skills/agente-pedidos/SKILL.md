---
name: agente-pedidos
description: Ponte de LEITURA SoftExpert ↔ Simple Agro da Sementes Maná LTDA + painel-reais da carteira de crédito. Flask no Railway, somente leitura no SE (nada é gravado no formulário). O SE chama /pedidos-venda como Fonte de Dados REST na atividade de crédito — o agente lê o cpf_cnpj do scred via SOAP fm_ws, autentica no SA com usuário dedicado, busca pedidos Soja da safra, expande o grupo econômico pelos CNPJs do campo grupoeconomico e mapeia SA→grid SE via CAMPO_MAP (fallbacks por campo: o SA renomeia campo sem aviso). Primeiro consumidor do banco-mana com schema dedicado agente_pedidos — data lake lake-first (workflows, detalhe, totais, atividades, tempos, gaps) com fallback ao vivo. Use SEMPRE no agente-pedidos — Fonte de Dados REST do SE, CAMPO_MAP, grupo econômico, data lake, painel-reais, situação de crédito, tempos de atividade, gaps sem CRE. Também quando mencionar: /pedidos-venda, /painel-reais, /api/situacao-credito, lake-first, 452 single-session, bridge SE-SA somente leitura, /api/prioridade, alta/média/baixa/não aplicável, observação do cliente, triagem da fila de crédito, Total Faturado, Saldo c/ Garantia, Aprovado com Garantia, lastro de endosso, protheus_faturado, faturado_foto, E1_VENCORI, NF menos NCC, natureza de semente, /api/faturado, /api/faturado-detalhe, dataset faturamento_detalhe, drill-down da lupa nota a nota, chaves_protheus, duplicata faturada vira Confeccionada, garantia_auto_dup, cards de faturamento sem lastro, _riscoFatDe, revenda-mae pela soma dos endossados.
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

## Situação WF — situação da instância no SoftExpert

Coluna **Situação WF**: Em andamento · Suspenso · Cancelado · Encerrado, de `WFPROCESS.FGSTATUS` (1/2/3/4).

- **Vem do próprio Conjunto SCSCRED**, colada na linha do CRE (`situacao_wf` em `get_all_open_workflows_from_se`) — sem cruzamento e sem chave auxiliar. O SCSCRED já filtra `fgStatus <= 5`, então encerrado e cancelado **sempre estiveram na lista**; só faltava a coluna no SELECT: `w0_.fgStatus AS fgstatus`.
- **Lê o código NUMÉRICO, nunca o rótulo.** O SE monta rótulo com chave de tradução (`#{103131}`) e o dataset-integration pode devolver isso cru. Código desconhecido → **""**, com log — nunca um chute.
- **Linha sem solicitação fica em branco** (não `—`): não há workflow pra ter situação.
- Aditivo e fail-soft: sem o campo no Conjunto, a coluna fica vazia. Exige reingestão do lake (chave `workflows`) após alterar o Conjunto.
- **Filtro "Situação WF"** multi-seleção, sem nada marcado por padrão. Linha sem solicitação sai quando o filtro está ativo (não há workflow).

⚠️ **Acrescentar a coluna na query NÃO basta.** O assistente do Conjunto separa *Construção da Query* (etapa 2) de *Campos* (etapa 3), e é a **etapa 3 que define as chaves do JSON da API**. Só na query, o campo aparece rodando o Conjunto dentro do SE e não sai pelo REST.

⚠️ **"Cancelado" não aparece via `fgStatus`.** Cancelar um crédito no CRE-001 é ação dentro do fluxo: o SE grava **Encerrado (4)**, não Cancelado (3). Medido em 2026-08-26: dos 27 encerrados, **26 eram cancelamentos** e só 1 concluiu o fluxo. A aba Indicadores separa cancelados pela ação no histórico (`fgtype 9`, `nmaction ILIKE '%cancel%'`) — é lá que essa distinção existe hoje.

⚠️ **`w0_.idProcess` é o número da INSTÂNCIA neste SE** (`000001`), apesar de o cabeçalho de uma das queries do vault dizer que seria o identificador do modelo. É a chave que o painel usa em tudo. Conferir contra uma linha real antes de criar Conjunto novo.

## Vencimento na lupa

Coluna **Vencimento** = data da **última parcela** do pedido (quando ele termina de ser pago), não a da primeira.

- **Fonte: `/api/financeiro` do agente-financeiro-sa**, casado por `order.numero` (mesma string dos dois lados) — não o `pagamento.parcelas` da listagem crua do SA, que é aninhado e a listagem trunca aninhado. O Painel Comercial SA já renderiza N parcelas desse array em produção: é a evidência de que o campo chega inteiro *por lá*, e a fonte agregada estável é o padrão da casa desde os totais de 2026-06-30.
- **`max()` sobre data parseada**, nunca sobre string: `"01/05/2027" < "30/08/2026"` em texto, e o pedido com parcela à vista + a prazo devolveria a data errada.
- Montado **antes** dos filtros de status/a-prazo em `_calc_totais` — a lupa mostra pedido cancelado e à vista, que também têm vencimento. `_calc_totais` retorna 4 valores.
- Lake-first (chave `vencimentos`), no bundle **fora do gate `faltando`**. Sem o mapa a célula mostra **⏳** (reingerir o lake), não `—`; `—` é reservado pra pedido que o financeiro não conhece.

## Variáveis de ambiente

`SE_URL`, `SE_API_KEY` (JWT) · `SA_BASE_URL`, `SA_USERNAME`, `SA_PASSWORD`, `SA_SAFRA_ID`, `SA_GRUPO_ID` · `BANCO_MANA_URL` · `PAINEL_SENHA`.

IDs fixos SA: safra 26/27 `69a5d85cae03f50036ee2531` · grupo Soja `610a8b743829fd00385c48c9`.

## Total Faturado e Saldo c/ Garantia — o controle de lastro (2026-09-17)

Duas colunas no `/painel-reais`, coladas no `Aprovado com Garantia`:

```
Saldo c/ Garantia = Aprovado com Garantia − Total Faturado
```

Responde "quanto ainda dá para faturar com endosso confeccionado atrás". Na SIAP no dia em que
subiu: `2.901.587,50 − 169.564,32 = R$ 2.732.023,18`, contra R$ 17,66 mi de pedido a-prazo aberto.

**A chave** (`protheus_faturado.py`, medida contra a base inteira antes do código):

```
documento   E1_CLIENTE   raiz sem DV: 8 = CNPJ, 9 = CPF (zero exceção em 6.319 títulos)
vencimento  E1_VENCORI   preenchido em 6.319/6.319
entra       TIPO = NF    e NATUREZA ∈ {400101, 400103}
abate       TIPO = NCC   e NATUREZA ∈ {400101, 400103}   ← subtração EXPLÍCITA: a NCC vem POSITIVA
```

⚠️ **`E1_VENCORI`, nunca `E1_VENCREA`.** O `VENCREA` é ajustado para dia útil e **11,1% dos
títulos** (703 de 6.319) têm `VENCREA ≠ VENCTO` — um em cada nove não casaria com a parcela do
pedido, sem erro e sem log. O `VENCREA` serve para EXIBIR, não para casar.

⚠️ **Classificação POSITIVA.** "Tudo que não é NCC" somaria os **R$ 277 mi de `RA`** (recebimento
antecipado) e inflaria o faturado em ~41%. Tipo desconhecido fica de fora **e é contado** em
`ignorados`, rotulado `TIPO/NATUREZA`, para não virar faturamento por omissão.

⚠️ **Tipo e natureza são complementares.** A `400101` é NF **e** RA; a NF tem **duas** naturezas.
Nenhum dos dois campos resolve sozinho.

⚠️ **Royalty (`PR`, `RYTCOOP*`, natureza `420104`) fica fora**: a NF de semente já sai com
germoplasma + tratamento + royalty + frete dentro. Somar o `PR` contaria royalty duas vezes.

**A foto** (`agente_pedidos.faturado_foto`): congela o par `(raiz, vencimento)` na primeira vez que
ele tem faturamento e **nunca remove**. Congela a **chave**, jamais o **valor** — em 2026-09-17
duas notas foram canceladas no Protheus e o faturado caiu R$ 236.239,56 corretamente; com valor
congelado, esse dinheiro somaria para sempre e o painel travaria faturamento com lastro.

**Três estados, sempre.** `None` = "não consegui saber" ≠ `0` = "não faturou". Qualquer ponta
desconhecida derruba o **saldo inteiro**, não só a célula do faturado. Motivo: faturado zerado por
engano deixa o saldo **cheio** e o painel autoriza faturamento sem lastro — entre os dois erros
possíveis, esse é o caro.

**Na linha da revenda**, o faturado soma o **conjunto** `{revenda} ∪ {endossados}`, cada documento
uma vez — "próprio + filhos" contaria em dobro no dia em que um endossado for faturado no
documento da revenda.

⚠️ **`/api/faturado?live=1` dispara em background e devolve 202.** Calcular dentro da requisição
mata o worker: gunicorn com `--timeout 60` e duas leituras remotas de 60s encadeadas.

Variáveis: `PROTHEUS_URL`, `PROTHEUS_API_KEY`, `PROTHEUS_NATUREZAS_SEMENTE` (default
`400101,400103`), `PROTHEUS_FATURADO_TTL` (default 600). No gateway, `API_KEYS` precisa da entrada
`pedidos:<chave>` — **chave sem o prefixo é descartada em silêncio**.


### O drill-down da lupa — as notas por trás do total (2026-09-19)

`GET /api/faturado-detalhe?chaves=<raízes>` → para cada chave: `notas[]`, `fora{}`, `nf`, `ncc`,
`valor`, `titulos`, `total_grade`, `confere`. A lupa mostra o total em cima e a lista embaixo.
A fonte é o dataset **`faturamento_detalhe`** do `agente-protheus` (irmão do `faturamento`
agregado), via `protheus_faturado.buscar_detalhe`.

⚠️ **NÃO recalcula o recorte.** `_calc_faturado` congela `chaves_protheus = {chave: {raiz:
[vencimentos]}}` no lake, e a rota só pede ao Protheus as notas dessas raízes. Se o detalhe
escolhesse sozinho o que conta, a tela teria **duas verdades** — o número da linha e a lista que
o explica — por caminhos diferentes. Concordariam hoje e divergiriam no primeiro ajuste de regra.

`confere` compara a soma da lista com o total da grade. Divergiu, a tela **diz** — não escolhe um
dos dois calado.

**O que fica de fora não some:** volta agregado por rótulo (`PR/420104`, `vencimento fora das
parcelas a-prazo`) com contagem e dinheiro. Lista crua não serviria — uma raiz sozinha (SIAP) tem
**720 títulos desde 2021**, e 717 não têm nada a ver com a safra.

`protheus_faturado.classificar(tipo, natureza)` é a MESMA regra do agregado, numa função só, e
`buscar_detalhe` não tem cache de propósito (leitura sob demanda de UM grupo).

### Duplicata faturada → Confeccionada (2026-09-19)

Garantia **duplicata** + `faturado > 0` ⇒ o Status Garantia sobe para `confeccionada`, sozinho,
depois da apuração do faturado (`_gar_auto_duplicata_faturada`).

⚠️ **Isto INVERTE a decisão de 13/09** ("duplicata não tem status de garantia"), que continua
valendo para quem **não** faturou. A inversão é coerente porque mudou um **fato**: em 13/09 não
existia a coluna Total Faturado e o painel não tinha como saber se a duplicata já tinha nascido.
A nota emitida **é** a duplicata existindo.

**O gatilho é `analise_revisao.garantias`** (o tipo da garantia, vindo da ata do comitê), não o
`Aprovado com Garantia` — esse é valor.

⚠️ **`agente_pedidos.garantia_auto_dup` existe para a regra não brigar com a pessoa.** A lei do
`quem` não cobre este caso: devolver o status para "— sem status" na tela **apaga** a linha de
`status_garantia` (o POST faz DELETE), e com ela some a marca de quem escreveu. Sem a tabela, a
regra reescreveria "Confeccionada" todo dia, para sempre. Com ela, atua **uma vez por processo**.

Não puxa de volta quem já está em assinatura/registro. **Não tranca carregamento**:
`_carreg_aplicar_regra` checa duplicata *antes* de olhar o degrau. Primeira passada: 11 processos.

### Os três alarmes de faturamento sem lastro (2026-09-19)

Cards vermelhos no topo, clicáveis, **três** e não um — cada um tem um dono diferente:

| card | o que é | quem resolve |
|---|---|---|
| Faturou SEM garantia aprovada | tem CRE, faturou, sem Aprovado com Garantia | crédito (atualizar o portal) |
| Faturou ALÉM do endosso | tem lastro, mas o faturado passou dele | crédito (lastro insuficiente) |
| Faturou SEM nenhuma CRE | faturou e não há solicitação | comercial (venda sem processo) |

`_riscoFatDe(w)` classifica, e **o card e o filtro chamam a mesma função**. Enquanto a regra
estava escrita duas vezes, consertar um lado não chegava no outro.

⚠️ **O que não se sabe não vira acusação.** `_garantidoDe` devolve `null` quando a escada não
carregou; contar isso como descoberto acusaria o crédito por causa de falha de rede, e alarme que
acusa errado para de ser olhado. Fica de fora **e é contado**, no tooltip.

**Revenda-mãe usa a soma dos endossados** (`_somaMaeDe`), a mesma expressão do `_saldoGarCel` —
numa revenda o crédito e a garantia moram nos endossados. Ignorar isso pôs a SIAP no card
mostrando R$ 2.901.587,50 de garantia na mesma linha.

⚠️ **A memo de `_aninharRevendas` tem as FONTES na chave**, não só a lista: `_garantias`,
`_situacoes` e `_faturado` chegam **depois** do load. Memoizando só pela lista, a primeira chamada
rodou antes da escada existir, os 29 endossados da SIAP deram zero e o cache congelou isso — a
coluna mostrava R$ 2,9 mi e o card dizia o contrário.

⚠️ **O HTML do painel é uma f-string:** `\\n` no fonte chega como `\n` no navegador; `\n` no fonte
vira **quebra de linha real** dentro da string JS e mata a página inteira. Validar desescapando na
mão não vale — renderize a f-string (`ast.literal_eval`) e só então rode `node --check`.


## ⚠️ Usuário dedicado no Simple Agro

O SA é **single-session**: quando o mesmo login entra em outro lugar, a sessão ativa cai (HTTP 452) e os requests em andamento morrem. O agente **precisa** de usuário/senha exclusivos da automação — um login manual de alguém durante o dia derruba a integração inteira. A cura estrutural desse problema é justamente o data lake.

## Deploy

`git push` → Railway auto-deploya em ~2 min. **Nunca `railway up`.** Validar por `/health` + log + teste funcional no painel.

## Cuidados ao mexer

- **Não voltar a gravar no SE.** Se pedirem "salva os pedidos no formulário", é a v2 de novo — leia a seção acima antes.
- **Falha não vira dado:** erro de transporte levanta exceção; lista vazia significa "não há pedidos", nunca "o SA recusou". Não persistir vazio no lake nem sobrescrever snapshot bom com falha.
- **Payload diz de quando é:** as respostas carregam `fonte` (lake/ao vivo) e timestamp — manter isso ao criar endpoint novo.
- O `README.md` do repo está **defasado** (descreve só o `/pedidos-venda`; o app tem 21 rotas, painel-reais e o data lake). Ao mexer, atualizar o README junto.
