---
name: agente-governanca
description: Plataforma de Governança por Processo da Sementes Maná — Flask+PG (schema governanca)+Railway: as áreas constroem a governança de cada processo em wizard guiado (SIPOC, tartaruga de 2 níveis, IC×IV Falconi, riscos↔controles N:N, requisitos auditáveis, versionamento AS IS→TO BE) e a plataforma gera o .bpmn no dialeto SoftExpert. Inclui o módulo de PLANEJAMENTO ESTRATÉGICO (Maná-Estratégia, método Antônio Napoli em 10 etapas, tabelas pe_*, coleta individual antes da reunião, acesso FECHADO por padrão via colaboradores.acesso_pe, lido do banco a cada request) e o Maná Results (mapa estratégico BSC, semeadura idempotente, desdobramento estratégico→tático→operacional), mais importador Bizagi/BPMN, organograma gráfico, agenda com .ics e construtor de documentos. Use SEMPRE no agente-governanca. Também quando mencionar: Maná Mapeia, Maná-Estratégia, Maná Results, mapa estratégico, BSC, RFL, tartaruga, requisito auditável, dialeto BPMN SE, pe_ciclos, acesso_pe, método Napoli, cockpit, medição, velocímetro, pe_medicoes, meta × realizado, dimensão canal/condição/origem, tipo de medida e de ligação, ticket médio, importar estoque, desdobramento até cultivar.
---

# agente-governanca — Plataforma de Governança por Processo

## O que é
Ambiente de DESENVOLVIMENTO da governança da Maná (Camada 5): a área constrói a governança
completa do processo; especialistas + Xayer transpõem pro SoftExpert (PRODUÇÃO). Blueprint
mestre com as 21 decisões do Xayer: `ManaVault/00-Inbox/2026-08-07-blueprint-mana-mapeia.md`.

## Arquitetura
- Flask + Jinja + Alpine (sem React) · identidade Maná (verde #1D6B3E, ouro #B8860B)
- PG banco-mana, schema `governanca` — criado no boot (app/db.py init_db, idempotente)
- JWT cookie `gov_token`; papéis admin > gestor > dono_processo; visão segregada por área
- Copiloto Claude OPCIONAL via mana-llm-gateway (config.USAR_GATEWAY); sem env → UI esconde
- Railway; gunicorn gthread; /health

## Conceitos que NÃO se pode "corrigir"
1. **Dialeto BPMN SE** (app/bpmn_gen.py): lanes SEM flowNodeRef (pertencimento = geometria Y),
   decisões com rótulo no name do sequenceFlow SEM conditionExpression, fins com terminate,
   tamanhos 130×80/56×56/50×50, lanes 317px. Decodificado do export real do CRE-001.
   Testes em tests/test_bpmn.py travam essas invariantes.
2. **Tartaruga polimórfica**: mesma tabela serve processo (atividade_id NULL) e atividade
   (decisão 7 — dois níveis, espelha PM009 do SE).
3. **Versionamento** (decisão 8): vigente é imutável; nova versão = cópia completa
   (routes_cockpit.nova_versao) com remapeamento de ids (atividades, decisões, risco_controle).
4. **IC×IV Falconi** (decisão 9): IC no nível processo (etapa 10 do wizard), IV no Bloco C
   (handoff da atividade). indicadores.tipo ∈ {IC, IV}.

## CRUD genérico do wizard
routes_wizard.TABELAS = whitelist tabela→colunas. POST/DELETE
`/api/versao/<vid>/itens/<tabela>`. Pra adicionar campo novo: coluna no schema.sql +
whitelist + input no template. Ownership sempre via _versao_ou_403.

## State machine (routes_cockpit.TRANSICOES)
rascunho→enviado (área) → validado_gestor|devolvido (gestor) → em_modelagem→modelado_se→vigente
(admin). Publicar vigente marca a anterior como obsoleta e grava rev_se.

## Decisão 20 (2026-08-09) — organograma gráfico navegável
- `app/org_chart.py`: layout tidy-tree simplificado + SVG puro (sem lib JS, igual bpmn_gen).
  `montar_svg(arvore, areas_soltas)` consome a saída de `routes_org._arvore_unidades()`.
  Área = chip `<a href='/org/area/<id>'>`; unidade sem área ainda reserva 1 linha (senão o
  aviso "sem áreas" vaza da caixa). `tests/test_org_chart.py` trava links, XML bem-formado,
  escape de & / < e não-sobreposição das caixas.
- Rotas novas (gestor+): `/org/grafico` (desenho) e `/org/area/<id>` (estrutura da área:
  funções → par área×função, mapeamento consolidado por categoria, processos com atalhos,
  pessoas). `/org` segue admin-only pros cadastros.

## Decisão 21 (2026-08-09) — agenda por departamento + Outlook (feed .ics)
- `app/routes_agenda.py` (/agenda calendário mensal por área, /agenda/assinar links,
  POST evento, remover) + `app/agenda_ics.py` (gerador RFC 5545) + tabela `agenda_eventos`
  e `areas.agenda_token`.
- **`/agenda/<token>.ics` NÃO tem @exige_login de propósito** — o Outlook busca a URL sem
  sessão; a proteção é o token secreto (renovável em /agenda/assinar por admin). Não
  colocar dado sensível na agenda.
- ICS: CRLF, folding em 75 **octets** (acento = 2 bytes), escape de `\ ; , \n`, horários em
  UTC (Z), dia inteiro com VALUE=DATE e DTEND exclusivo (dia seguinte), X-WR-CALNAME pro
  nome aparecer no Outlook. `tests/test_agenda_ics.py` trava tudo isso — fora do RFC o
  Outlook recusa a assinatura sem mensagem clara.
- Fuso: banco em TIMESTAMPTZ (UTC), UI em America/Sao_Paulo via TZ_OFFSET −3 (sem horário
  de verão no Brasil desde 2019). Cor por área = CORES[area_id % 10] (estável).
- Visibilidade: admin vê todas as áreas; demais só a própria (mesma regra do resto).

## Performance (2026-08-09)
- **gunicorn --timeout 120** no Dockerfile: chamada ao LLM vai até 60s e o default de 30s
  MATA o worker no meio da entrevista; com `-w 1` isso derruba tudo em voo (parecia
  "lento/travando"). Não baixar o timeout. threads 12, keep-alive 15.
- **Índices** no fim do schema.sql (versao_id / atividade_id de toda tabela da tartaruga,
  form_campos, app_requisitos, doc_secoes, entrevista_msgs). Tabela nova = índice novo.
- **gzip + cronômetro** em `_perf` (after_request do main.py): header `X-Tempo-ms` em toda
  resposta e log `[governanca][LENTO] Xms MÉTODO /rota` acima de 1,5s — é o primeiro lugar
  pra olhar quando reclamarem de lentidão (Deploy Logs do Railway). `tests/test_perf.py`
  garante que o gzip não corrompe o HTML.
- Estáticos com `SEND_FILE_MAX_AGE_DEFAULT=86400`; Google Fonts carrega sem bloquear
  render (media=print/onload) e tour.js é `defer` (os templates usam DOMContentLoaded —
  seguro).
- Entrevista manda só as 12 últimas mensagens ao LLM (o estado completo já vai no prompt):
  aumentar o histórico deixa a resposta mais lenta sem ganho.

## Gotchas
- **schema.sql roda em UMA transação** (db.init_db faz `cur.execute(ddl)` inteiro): um
  comando que referencia tabela ainda não criada aborta TODO o schema — a app sobe (try/
  except no main) mas sem as tabelas novas, e as telas quebram com 500. Incidente real
  2026-08-09 (doc_secoes criada antes de documentos_metodos → v19 fora do ar). Regras:
  tabela nova SEMPRE depois da que ela referencia (ou no fim do arquivo);
  `tests/test_schema.py` trava isso; `_aplicar_ddl_por_partes` (db.py) é a rede de
  segurança — reaplica comando a comando e loga qual quebrou; `/health` lista
  `tabelas_faltando` (TABELAS_ESPERADAS em main.py) — primeiro lugar pra olhar quando
  "sumiu" alguma tela.
- wizard.html salva e dá location.reload() preservando o hash da etapa — não "otimizar" pra
  estado client-side sem repensar tudo.
- templates usam Alpine: qualquer @click novo precisa estar sob um elemento com x-data.
- capacitação embutida = static/capacitacao.html (cópia do deck; atualizar junto com o deck).
- schema init tolera boot sem DATABASE_URL (pra testes) — não remover o try/except do main.py.
- **Nada de `json.dumps` cru sobre linha do banco** (incidente 2026-08-19, entrevista do /pe
  morria na 1ª resposta com 502: `Object of type datetime is not JSON serializable`, por causa
  do `criado_em TIMESTAMPTZ`). Regra: estado que vai pro prompt passa por
  `consultor._json_estado()` — `default=str` cobre datetime/date/Decimal, remove colunas de
  controle (id, ciclo_id, autor_id, criado_em) que só gastam token, corta em ~6000 chars e é
  **fail-soft**: se falhar devolve `"{}"` em vez de derrubar a entrevista. Há 4 testes de
  regressão, incluindo `entrevistar()` ponta a ponta com `copiloto._chamar` mockado.

## Disciplina Organizacional (/org — 2026-08-07, espelho SE)
Estrutura decodificada das telas do SE: Unidade organizacional (AD003, árvore=organograma)
→ Área (identificador+unidade_id) → Função (AD002, catálogo, N:N via area_funcao) → o PAR
área×função carrega o mapeamento (af_itens → org_catalogo). org_catalogo é UNIFICADO por
categoria: atividade/autoridade/responsabilidade/experiencia/nivel_instrucao (com ordem) —
competencia e curso são categorias FUTURAS já previstas no CHECK (não mudar schema pra
adicioná-las). Exports CSV em /org/export/<entidade>.csv no layout SE (importação futura por
planilha/API). Wizard: datalist de papéis agora vem de `funcoes` (não cargos_funcoes —
tabela legada mantida só pra colaboradores.cargo_id até a etapa Colaborador).

## Decisão 10 (2026-08-09) — módulos/bibliotecas + macroprocesso + copiloto de contexto
- "Biblioteca por trás, wizard na frente": bib_riscos/bib_controles/bib_documentos/bib_indicadores
  com upsert automático em criar_item (_upsert_biblioteca) e tela /bibliotecas (gestor+).
  Instâncias por versão ganharam biblioteca_id — NÃO remover as tabelas por versão.
- macroprocessos (atravessa áreas) + processos.identificador (convenção SM.<AREA>.PR-NNN via
  _sugerir_identificador) + processos.contexto (texto livre) + processos.exemplo (gabarito
  somente-leitura; _versao_ou_403(escrita=True) bloqueia mutação pra não-admin).
- Copiloto "pre-montar": lê o contexto e INSERE rascunho de atividades/SIPOC/riscos(tipologia)/
  controles/indicadores(dimensão)/documentos direto no banco (existe=False nos propostos).
- Seed exemplo CRE-001 em app/seed_exemplo.py (idempotente, roda no init_db).
- Classificações do mapa mental: riscos.tipologia, indicadores.dimensao.
- Layout: app-shell sidebar (tokens do agente-financeiro-gestao: Inter, --primary #2d6a4f,
  cards shadow suave); logos reais em static/img/. Classes legadas (.card, table.mana, .pill,
  .linha) mantidas no mana.css novo — não renomear.

## Decisão 11 (2026-08-09) — Modo Entrevista (Maná-Process consultor sênior)
- Criar processo com copiloto ligado → redireciona pra `/versao/<vid>/entrevista` (chat);
  o wizard vira alternativa/refino. Botão "🎙️ Entrevista" na tabela de processos da home.
- Loop: copiloto.entrevistar(estado, historico, msg) devolve JSON `{fala, acoes[]}`;
  routes_entrevista._aplicar grava no banco (set_cabecalho, add_atividade c/ dedup,
  set_decisao c/ alçada, add_sipoc, add_oportunidade); painel lateral (Alpine) atualiza
  com o estado retornado. Histórico em `entrevista_msgs` (semeia ABERTURA no 1º GET).
- Colunas novas: `atividades.tipo_execucao` (manual|formulario_eletronico|sistema) e
  `decisoes.alcada` — NÃO renomear os valores de tipo_execucao (o prompt e o template
  entrevista.html dependem das strings exatas).
- **Doutrina "MAPEAR PARA AUTOMATIZAR"** (no prompt de entrevistar): o que roda em sistema
  só se registra; atividade manual → investigar gap → `add_oportunidade` (workflow+formulário
  ou app) no funil da hiperautomação. Não remover esse bloco do prompt ao "encurtar".
- POST exige _versao_ou_403(escrita=True) → exemplo CRE-001 conversa mas não grava p/ áreas.

## Decisão 12 (2026-08-09) — escopo por versão (governança por níveis)
- `processo_versoes.escopo` ∈ {mapeamento, completo} (default completo). Definido no modal
  do botão "✅ Concluir mapeamento" da entrevista (POST /api/versao/<vid>/entrevista/concluir);
  mapeamento → redirect Revisão, completo → redirect wizard.
- escopo='mapeamento' = só fluxo + SIPOC + oportunidades: revisão/wizard mostram aviso,
  cockpit mostra pill 🗺️, e check_completude recebe o escopo no resumo — o prompt manda NÃO
  cobrar riscos/indicadores/documentos/requisitos fora do escopo.
- nova_versao (cockpit) NÃO copia escopo de propósito — versão nova nasce 'completo'
  ("avança um nível a cada versão"). Não "corrigir" pra herdar.

## Decisão 13 (2026-08-09) — espec de formulário eletrônico por atividade
- Tabela `form_campos` (versao_id + atividade_id NOT NULL): nome, tipo (8 tipos CHECK),
  obrigatorio, opcoes, origem (digitado|sistema|calculado), origem_detalhe, preenche_papel,
  regras. Na whitelist TABELAS (CRUD genérico) e no `simples` de nova_versao (cockpit).
- Captura em DOIS lugares: entrevista (ação add_campo_form do copiloto — match atividade
  por nome, dedup, defaults seguros pra tipo/origem inválidos) + builder no Bloco C
  (atividade.html, card visível só quando tipo_execucao='formulario_eletronico').
- Painel da entrevista mostra "📝 formulário (N campos) detalhar ↗" (estado inclui a.id e
  n_campos). Doc de caracterização ganha seção "Especificação de formulários eletrônicos"
  — é o insumo da modelagem do form no SE; não remover.
- Fix de versionamento embutido: nova_versao agora copia atividades.tipo_execucao e
  decisoes.alcada (antes perdia os campos das decisões 11/13 na cópia).

## Decisão 14 (2026-08-09) — processo que vira APLICATIVO (requisitos guiados)
- `processo_versoes.destino_automacao` ∈ {'', workflow, app} + tabela `app_requisitos`
  (versao_id, SEM atividade_id — está na exceção tem_atv do nova_versao; destino é copiado
  pra versão nova de propósito, diferente do escopo).
- Entrevista: bloco "DESTINO DA AUTOMAÇÃO" no prompt — sinais de app → set_destino app +
  modo levantamento de requisitos (7 perguntas guiadas); ações set_destino e add_req_app
  (10 categorias CHECK, prioridade essencial/importante/desejavel, defaults seguros).
- UI: painel da entrevista (card 📱 borda accent), Revisão (editor CRUD via TABELAS
  whitelist, card visível se destino=app OU já há requisitos), cockpit pill 📱, doc de
  caracterização seção "Requisitos do aplicativo" (numeração dinâmica via namespace ns.sec).
- Essa lista É o insumo do Maná Builder (gerar app com IA) — não simplificar as categorias.

## Decisão 15 (2026-08-09) — atividade executada por AGENTE DE IA
- `tipo_execucao='agente'` (atividades.sistema = nome do agente). `app_requisitos` virou
  POLIMÓRFICA: atividade_id NULL = app do processo (dec. 14); preenchido = agente da
  atividade — mesmo padrão da tartaruga. Por isso app_requisitos SAIU da exceção tem_atv
  do nova_versao (mapa.get(None)→None preserva o NULL na cópia) — não "simplificar".
- Entrevista: bloco "AGENTE DE IA NA ATIVIDADE" no prompt (candidatas: tarefa cognitiva
  repetitiva, gerar doc, analisar, notificar; levanta o-que-faz/gatilho/fontes/regras/canal/
  GATE HUMANO→categoria restricao); ação add_req_agente (match atividade por nome, dedup
  por atividade).
- UI: painel entrevista ícone 🤖 (n_reqs + detalhar ↗), Bloco C card "🤖 Agente de IA"
  (builder, visível se tipo_execucao='agente'), Revisão card "Agentes de IA no fluxo",
  doc seção própria (reqs de processo filtram rejectattr('atividade_id')).

## Decisão 16 (2026-08-09) — fluxo clicável (preview → Bloco C)
- gerar_preview_svg(layout, escala, link_base=None): com link_base, cada userTask vira
  <a href='{link_base}{atv_id}'> com <title> tooltip + hover CSS inline no SVG.
- montar_layout adiciona atv_id ao node userTask — SÓ pro preview; gerar_xml não emite
  (testado: "atv_id" not in xml). Não deixar atv_id vazar pro XML do dialeto.
- Revisão chama com link_base=f"/versao/{vid}/atividade/" — o fluxo é o mapa de navegação
  do detalhamento (jornada: entrevista mapeia o processo → clica nas caixinhas pra
  detalhar atividade a atividade).

## Decisão 17 (2026-08-09) — voz no Bloco C ("fale e eu estruturo")
- atividade.html: 🎤 manaDitar em todo input de texto + card "🎙️ Fale o levantamento"
  → POST /api/versao/<vid>/atividade/<aid>/falar → copiloto.estruturar_atividade (fala
  livre → JSON acoes) → routes_entrevista._aplicar_atv (dedup por atividade, defaults
  seguros, papel da atividade como default de preenche_papel/responsavel).
- IV com campos padrão SE: formula, meta, frequencia, responsavel, dimensao (CHECK das
  dimensões: prazo|custo|quantidade|qualidade).
- aplicadas>0 → recarrega a página (itens novos aparecem); 0 → mantém a fala do copiloto.

## Decisão 18 (2026-08-09) — construtor de documentos (POP/IT/política/norma)
- app/routes_docs.py: LAYOUTS por tipo (pop/instrucao/politica/norma — seções padrão
  ISO 9001), /versao/<vid>/documento/<did> (editor), APIs iniciar (semeia doc_secoes,
  troca layout apaga), secao/<sid> (autosave no blur), gerar (✨ copiloto.gerar_documento
  preenche SÓ seções vazias, derivando o passo a passo das atividades mapeadas;
  faltas viram [COMPLETAR: …]).
- Entrada: botão "✍️ Confeccionar" nos documentos do Bloco C e da Revisão. Impressão:
  window.print() com timbre via @media print (.doc-timbre). Upload de layout próprio da
  empresa = etapa futura (documentado no blueprint); não prometer que já existe.
- doc_secoes NÃO entra em TABELAS (CRUD próprio) nem precisa de cópia especial no
  nova_versao (documentos_metodos novos são copiados sem seções — doc recomeça na
  versão nova por design).
- Decisão 19 — importar modelo próprio: POST .../importar-layout (multipart 'modelo',
  .docx/.txt/.md ≤4MB pelo MAX_CONTENT_LENGTH). _texto_do_modelo marca headings do docx
  com "# "; copiloto.extrair_secoes é o caminho principal, _secoes_heuristica o fallback
  (strip iterativo de "# " + numeração — não voltar pro sub único, "# 1. X" quebrava).
  tipo vira 'modelo_proprio' (está em TIPOS, fora de LAYOUTS — o chooser exclui).
  Dependência: python-docx==1.1.2 no requirements.

## Módulo Planejamento Estratégico — Maná-Estratégia (2026-08-11→19)

Segundo módulo do app, ao lado do mapeamento de processo. **Método Antônio Napoli**
(sócio-fundador da Catálises, consultor que desenhou o plano estratégico do G4), destilado
da entrevista no Papo de Gestão em **10 etapas** — a lógica vive em `app/consultor.py`
("Maná-Estratégia — consultor sênior"), cada etapa com a citação-âncora do Napoli.

**Princípios do método que NÃO se pode diluir** (estão no consultor e valem como regra):
- *Alinhamento não é consenso* — não precisa todo mundo querer a mesma coisa.
- *A pergunta que abre a estratégia é "a quem você serve"* — sem ela, o resto é ruído.
- *Amplitude de mercado e geografia vêm antes de qualquer análise.*
- *Peer group é deliberado* — peer escolhido pra se sentir bem é autoengano.
- *Olhar primeiro cliente/mercado/competidor; só depois a casa.*
- *Horizonte é por setor* — é o tempo que uma decisão leva pra virar resultado.
- *Quase ninguém pergunta o que NÃO vai mudar* (invariantes).
- *Tático se refaz todo ano; estratégia só muda em evento catastrófico.*
- *Ordem de execução: estrutura → cultura → sistema de gestão → sistema de incentivo.*

**Dado (23 tabelas `pe_*` no mesmo schema `governanca`):** `pe_ciclos`, `pe_desejos`,
`pe_alinhamento`, `pe_objetivos`, `pe_iniciativas`, `pe_indicadores`, `pe_cards`,
`pe_card_metas`, `pe_ritos`, `pe_pacing`, `pe_socios`, `pe_clientes`, `pe_arena`,
`pe_peers`, `pe_diagnostico`, `pe_ambicao`, `pe_condicoes`, `pe_invariantes`,
`pe_escolhas`, `pe_desdobramento`, `pe_entrevista_msgs`, `pe_participantes`,
`pe_coleta_feita`.

**Rotas** (`app/routes_pe.py`): `/pe` (lista de ciclos) · `/pe/novo` · `/pe/<cid>` ·
`/pe/<cid>/minha` (**coleta individual opcional antes da reunião**) ·
`/pe/<cid>/entrevista` (modo conversa) · `/pe/<cid>/pauta` (**pauta da reunião**) · API
`PATCH /api/pe/<cid>/ciclo` · `POST /api/pe/<cid>/unico/<tabela>` (registro único) ·
CRUD genérico `POST|PATCH|DELETE /api/pe/<cid>/<tabela>[/<iid>]` · `/api/pe/<cid>/metas` ·
`/api/pe/<cid>/participantes[/<pid>]` · `/api/pe/<cid>/contribuicoes/<etapa>` ·
`POST /api/pe/<cid>/consolidar`. Telas: `pe.html`, `pe_lista.html`, `pe_entrevista.html`,
`pe_pauta.html`.

**Ditado por voz em todo campo de resposta do wizard** (mesma linha da decisão 17).

### Coleta individual — como o dado se separa

Linha com `autor_id IS NULL` **é o plano**; linha com `autor_id` preenchido **é contribuição
de uma pessoa**. Só as etapas de PERCEPÇÃO se coletam sozinho
(`ETAPAS_INDIVIDUAIS = alinhamento, servico, peers, diagnostico, ambicao`) — decisão (arena,
invariantes, escolhas, desdobramento, cobrança) é para fazer junto, de propósito. Sigilo até
todos concluírem (`_coleta_aberta`); só o condutor consolida, e `consolidar` copia para o
plano sem duplicar (dedup por CHAVE).

### Pauta da reunião (`/pe/<cid>/pauta`) — 2026-08-19

Roteiro de **10 blocos** montado a partir do que cada um trouxe na coleta, imprimível em PDF.
O núcleo é classificar cada item em **três montes** — e a distinção é o produto:
- **consenso** — todos trouxeram: não gasta tempo de reunião, vai direto pro plano;
- **divergência de FATO** — enxergam a mesma realidade diferente: resolve com **dado** (quem
  busca, até quando), não com discussão;
- **divergência de VONTADE** — querem coisas diferentes: não existe dado que resolva, resolve
  com **acordo escrito** (às vezes o acordo é concordar em discordar).

`NATUREZA` em consultor.py define o monte por etapa (alinhamento e ambição = vontade;
serviço, peers e diagnóstico = fato). `montar_pauta()` devolve os blocos com `quem_falta` e
`n_coletado` — este último existe para distinguir **"ninguém respondeu ainda"** de **"todos
responderam e não sobrou atrito"**, que na primeira versão apareciam iguais na tela.
Filtros `so_onde`/`nao_onde` (via `_cabe_no_bloco`) impedem o **mesmo item de aparecer em dois
blocos** — o horizonte, por exemplo, bebe do alinhamento nos blocos 1 e 2. Teste trava isso
(`test_pauta_nao_repete_o_mesmo_item_em_dois_blocos`) e o tempo total
(`test_pauta_cabe_em_dois_meios_dias`, 240–360 min).

### ⚠️ Acesso ao módulo estratégico — fechado por padrão

`app/auth.py` → `pode_pe()` / `@exige_pe()`. **`colaboradores.acesso_pe` default FALSE**:
quem entra para mapear processo **não vê** o módulo estratégico. A permissão é lida **do
banco a cada requisição, nunca do token** — de propósito: liberar ou cortar acesso tem
efeito imediato, sem esperar o JWT expirar. Cache só dentro do request (`g._pode_pe`).

**Não migrar essa checagem para o token** "por performance" — o custo de uma query por
request é o preço de conseguir revogar acesso a conteúdo estratégico na hora.

## Outros módulos entregues (2026-08-10→18)

- **Importador Bizagi/BPMN** (`app/bizagi_import.py`, `/importar`, `importar_previa.html`):
  traz fluxo, papéis e decisões já criados; paleta BPMN 2.0 completa + inventário de
  artefatos; **raia soma origem do pool** e **gateway paralelo não vira decisão**; decisão
  com dois caminhos declara destino de cada ramo, marcador de "caminho a definir" e rótulo
  no meio da seta.
- **Organograma gráfico** (`app/org_chart.py`, `/org`, `org_grafico.html`): áreas clicáveis
  → estrutura da área, recolher/expandir ramos, nome inteiro, zoom/tela cheia, **uma
  empresa por tela**, hierarquia entre áreas em N níveis, ditado por voz.
- **Agenda por departamento + Outlook** (`app/agenda_ics.py`, `/agenda`): "minha agenda"
  consolidada e **assinatura .ics** (decisão 21).
- **Login no iframe do SE**: cookie `SameSite=None; Secure`, aviso de bloqueio e **`sub` do
  JWT como string** (embed do painel dentro do SoftExpert).
- **Performance**: gunicorn timeout 120s, **28 índices**, gzip, cache de estáticos, render
  não-bloqueante e cronômetro por rota.

## Decisão 22 (2026-08-17→19) — módulo Planejamento Estratégico (consultor Maná-Estratégia, método Napoli)

- Módulo NOVO ao lado do wizard de processo: `/pe` (lista), `/pe/<cid>` (wizard das 10 etapas)
  e `/pe/<cid>/entrevista` (modo conversa). Blueprint `pe` em `app/routes_pe.py`, registrado no
  `main.py` depois de `bp_entrevista`. Link na seção Estratégia da sidebar (`base.html`).
- **Método = Antônio Napoli** (Catálises; desenhou o plano estratégico do G4), destilado da
  entrevista dele no Papo de Gestão. NÃO é o workbook do G4 — a primeira versão do módulo era,
  e foi substituída. 10 etapas: alinhamento dos sócios → a quem você serve → arena (mercado e
  geografia) → peer group → diagnóstico de fora pra dentro → ambição + confronto honesto →
  o que NÃO vai mudar → escolhas (cada uma com o seu "não") → desdobramento → divulgação e
  cobrança. A ordem é o produto: `POST /api/pe/<cid>/etapa` devolve **409** com a lista de
  etapas travadas quando se tenta pular.
- **Cada etapa se explica na tela** antes de pedir qualquer coisa: `METODO` em `consultor.py`
  carrega `o_que_e`, `por_que`, `napoli` (a tese que origina a etapa), `erro` (o erro clássico)
  e `perguntas` (o roteiro). O template renderiza os quatro blocos. Pergunta na tela sem essa
  explicação foi reclamação explícita do Xayer — não reintroduzir.
- **`app/consultor.py` é o núcleo e é DETERMINÍSTICO** (mesma decisão 3 do copiloto do wizard):
  as travas rodam com `LLM_GATEWAY_URL/KEY` vazios. `consultor.ligado()` só controla os botões
  ✨ e o modo entrevista. NUNCA mover trava para o prompt.
- **A trava mais importante é a ordem do desdobramento**: estrutura → cultura → sistema de
  gestão → sistema de incentivo. `criticar_desdobramento` recusa camada preenchida com a
  anterior vazia. Motivo (Napoli): contexto vence força de vontade; quem começa pelo bônus
  compra o comportamento errado a preço cheio. A UI também desabilita o botão da camada.
- A régua de metas (gatilho de 80% sem interpolação, faixas 80/100/120, card de 4–6, peso
  10–50%, multiplicador por camada) vive DENTRO da 4ª camada — `criticar_incentivo` só é
  chamada quando a camada `incentivo` tem linha. Constantes: `MULTIPLICADOR`,
  `CARD_MIN/ALVO/MAX`, `PESO_MIN/MAX`, `GATILHO_PCT`. Mexer nelas muda a doutrina — mudar o
  teste junto.
- **Corte seco em 80% não interpola.** `simular_bonus` zera tudo abaixo do gatilho porque a
  fórmula é multiplicação. 79% é zero, não 79% — não "consertar" para rampa suave.
- Modo entrevista espelha o Maná-Process (decisão 11): `consultor.entrevistar` devolve
  `{fala, acoes[]}` e `_aplicar` grava. Toda ação de `_aplicar` é idempotente por nome/texto
  (não duplica ao repetir). `avancar_etapa` do LLM passa pela MESMA trava do núcleo — o
  consultor sugere, o núcleo decide.
- Tabelas `pe_*` no fim do `schema.sql`. As da reformulação: `pe_socios`, `pe_clientes`,
  `pe_arena`, `pe_peers`, `pe_diagnostico`, `pe_ambicao`, `pe_condicoes`, `pe_invariantes`,
  `pe_escolhas`, `pe_desdobramento`, `pe_entrevista_msgs`. `pe_arena` e `pe_ambicao` são
  UNIQUE(ciclo_id) — upsert por `POST /api/pe/<cid>/unico/<tabela>`. `pe_desejos` e
  `pe_alinhamento` ficaram órfãs da versão do workbook: não usar (não foram dropadas para não
  perder dado de ciclo antigo).
- Migração do CHECK de `pe_ciclos.etapa`: DROP CONSTRAINT IF EXISTS + UPDATE das etapas antigas
  para `'alinhamento'` + ADD CONSTRAINT. É idempotente por causa do DROP IF EXISTS — testado
  aplicando `schema.sql` duas vezes e sobre um banco com o esquema antigo.
- CRUD genérico igual ao do wizard: `TABELAS` (colunas graváveis, coluna de vínculo) +
  POST/PATCH/DELETE em `/api/pe/<cid>/<tabela>`. `_limpar` converte `""` para NULL nas
  `NUMERICAS`.
- Gotcha que já mordeu duas vezes: `exige_login` é decorator FACTORY, usar `@exige_login()`;
  e o token só tem `sub/nome/perfil/area_id` (**NÃO tem `id`**) — há teste de regressão para
  os dois. O mesmo vale para `exige_pe()`.

## Maná Results — mapa estratégico e desdobramento (decisão 23, 2026-08-22)

Terceira tela do módulo estratégico, entre o wizard (como se chega na estratégia) e os ritos
(como se cobra). O nome é do **rito do G4**: "Results" é a reunião mensal onde se olha o
placar inteiro antes de escolher os desvios que viram FCA. Rotas: `/pe/mapa` (atalho pro
ciclo mais recente) e `/pe/<cid>/mapa`; API `POST /api/pe/<cid>/mapa/semear`,
`POST|DELETE /api/pe/<cid>/mapa/ligacoes[/<lid>]`, `GET /api/pe/<cid>/objetivo/<oid>`.
Tela: `templates/pe_mapa.html`. Base do desenho: `app/mapa_base.py`.

### A decisão que sustenta o módulo: o nó do mapa É `pe_objetivos`

**Não existe tabela de nó do mapa** — só `pe_mapa_ligacoes` (as setas). O nó do mapa é uma
linha de `pe_objetivos` com `perspectiva` preenchida; quem tem `perspectiva=''` é objetivo
antigo, de fora do mapa, e continua funcionando. Motivo: `pe_indicadores.objetivo_id` já
existe — reusando `pe_objetivos`, **o desdobramento estratégico → tático → operacional vem
de graça** (`pe_indicadores.nivel` + `pai_id` auto-referente). Criar tabela própria
"pra ficar limpo" quebra exatamente o que o módulo existe para fazer. `test_mapa.py` trava
a ausência de `pe_mapa_objetivos` no schema.

### Colunas novas (ALTERs no fim do `schema.sql`)

- `pe_objetivos`: `perspectiva` (CHECK '' | financeira | clientes | processos | aprendizado),
  `grupo`, `memoria`, `explicacao`, `valor_ref`, `sub_ref`, `cod`, `formato`
  (card | circulo | faixa), `col`, `chave`.
- `pe_indicadores`: `nivel` (CHECK estrategico | tatico | operacional), `pai_id`
  (FK auto-referente, ON DELETE SET NULL), `area_id`, `frequencia`.
- `pe_mapa_ligacoes` (ciclo_id, de_id, para_id, tipo cadeia|sobe|influencia, secundaria)
  com **UNIQUE (de_id, para_id)** — seta duplicada é ruído visual, não informação.
- `ux_pe_objetivos_chave` — índice único parcial `(ciclo_id, chave) WHERE chave <> ''`. **É
  ele que torna semear idempotente**; sem ele, apertar o botão duas vezes duplica o mapa.

### Semear é idempotente e NÃO sobrescreve

`POST .../mapa/semear` insere só o que falta (match por `chave`) e devolve
`{objetivos_criados, ja_existiam, ligacoes_criadas}`. O que o usuário editou na tela
**permanece**: semear de novo não toca em linha existente. Só o **condutor** do ciclo semeia,
e a rota roda `mapa_base.validar()` antes de gravar — mapa base inconsistente espalharia lixo
por 40 objetivos de uma vez, e desfazer é manual.

### O desenho (`app/mapa_base.py`) carrega doutrina, não é enfeite

40 nós, 54 ligações, 102 indicadores candidatos, nas 4 perspectivas do BSC (Kaplan & Norton).
O que **não** se "arruma" sem falar com o Xayer — cada item tem teste:

- **Corte Falconi/INDG**: a DRE tem duas competências. **Operacional** (ROL → EBITDA) prova a
  cadeia de valor; **financeira** (EBITDA → lucro) prova juros, prazo e perdas. Por isso
  `ebitda → lucro_liquido` **e** `rfl → lucro_liquido`, e a mesa financeira sobe pro **RFL,
  nunca pro EBITDA** — ligar a mesa ao EBITDA seria contar spread como resultado operacional.
- **RFL = Resultado Financeiro Líquido** (receitas − despesas financeiras): é o nome do
  indicador da competência financeira. Não renomear — a tela, os testes e o mapa da pirâmide
  usam essa sigla.
- **Geração de caixa é o fim da linha**: recebe seta e **não emite nenhuma**. Nó de caixa
  saindo = alguém inverteu a causalidade do mapa.
- **Ordem da cadeia da safra** (correção explícita do Xayer): planejamento ① → **marketing ②**
  → cooperados ③ → logística interna ④ → **UBS ⑤ → comercialização ⑥ → expedição ⑦**.
  *(Superado em 29/08: o **laboratório** entrou em ⑥, a comercialização virou ⑦ e a expedição
  ⑧ — ver a seção do laboratório.)*
  Vende depois de beneficiar; expede depois de vender. Os números são o campo `passo`, que o
  cartão mostra num selo — numerados **por bloco**, não por perspectiva (só a cadeia da safra
  e a perspectiva de clientes são filas; o apoio não é).
- **Marketing é ETAPA** (passo ②), não faixa transversal — mudou em 2026-08-23. O que decidiu
  foram os indicadores que ele já carregava (leads por canal, CAC, conversão
  lead→oportunidade): geração de demanda tem entrada e saída. É ramo **paralelo** ao campo —
  `planejamento → marketing → comercialização` de um lado, `planejamento → cooperados` do
  outro. Marketing entrega funil, não bag.
- **O portão do crédito** (correção do Xayer): a cadeia física NÃO vai do pedido ao caminhão.
  `comercialização → crédito → faturamento → expedição`. Crédito é barreira antes de
  **faturar**, não antes de comercializar — o pedido nasce primeiro. A seta atravessa os três
  blocos de propósito: a cadeia física para e espera a esteira financeira.
- **Posição no tempo ≠ bloco de competência.** O crédito acontece no meio da cadeia física e
  continua sendo competência FINANCEIRA: o critério é qual linha da DRE o processo move (ele
  produz spread preservado → RFL), não quando ele acontece. Mover o nó de bloco para "arrumar"
  o desenho quebraria o corte Falconi inteiro.
- **A comercialização é P6, não P5** (renumerada em 2026-08-23 quando o marketing entrou como
  etapa ②; o Xayer liberou os códigos). O P5 hoje é a **UBS**, e a esteira financeira desceu
  para P8..P11. Texto antigo que diz "o P5" está falando da comercialização.
- **Perspectiva de clientes é o ciclo de vida do cliente**, na ordem ①cliente certo/carteira →
  ②mix e preço → ③entrega e qualidade → ④recompra → ⑤share. Estava invertida até 2026-08-23 e
  contradizia o próprio P6, onde a primeira das quatro condições da venda é o cliente que paga.
  Códigos C1..C5 acompanham a cadeia.
- **Crédito, cobrança, barter e mesa são processos de NEGÓCIO** da competência financeira —
  não apoio. O critério é "produz resultado que a estratégia conta?", **não** "está no
  EBITDA?" — a competência financeira mora depois do EBITDA por definição, então esse teste
  classificaria errado por construção.
- Causalidade BSC: seta `sobe` só de perspectiva de baixo para de cima
  (aprendizado → processos → clientes → financeira). O teste recusa o contrário.

### Gotchas

- Todo nó tem `memoria` (memória de cálculo) e `explicacao` — a tela abre o popup com os dois.
  Nó sem isso é caixa sem procedência, a mesma reclamação que originou o `METODO` explicado na
  tela do wizard (decisão 22). Teste trava.
- `pe_mapa.html` define o macro `no_card` **no topo** do bloco: Jinja avalia em ordem e macro
  declarado depois do laço explode em runtime. Há teste comparando as posições no arquivo.
- As setas são desenhadas em **SVG no cliente**, a partir da posição real das caixas — não há
  layout calculado no servidor (diferente do `bpmn_gen`/`org_chart`).
- API do mapa devolve linha do banco por `_serial()` (datetime→ISO, Decimal→str). **Nada de
  `jsonify` cru sobre linha do banco** — mesma lição do incidente da entrevista.
- Rotas do mapa são todas `@exige_pe()` (factory, com parênteses). Teste percorre o AST do
  `routes_pe.py` e falha se alguma rota nova ficar sem o decorator.

### A tela É o mapa desenhado — não uma releitura

`templates/pe_mapa.html` porta o HTML que nasceu na conversa com o Xayer
(`estrategia/piramide-financeira-mana.html`): mesma paleta, mesma forma, mesmas setas. A
forma carrega leitura e por isso está travada em teste:

- `mapa_base.LAYOUT` diz como cada faixa se desenha — **financeira e clientes em COLUNAS**
  (ali é uma conta e uma jornada, andam da esquerda pra direita) e **processos e aprendizado
  em GRUPOS** (blocos de competência lado a lado, com grade).
- `mapa_base.GRUPOS` guarda, por (perspectiva, título): quantas colunas na grade, o peso na
  linha, o estilo e **em que linha** o grupo entra — é o que faz o apoio descer para baixo
  dos dois blocos de negócio (ele serve todas as etapas, não é etapa).
- `mapa_base.css_do_no()` decide a cor, e cor aqui é semântica: azul = competência
  financeira, verde = operacional, âmbar = processo da safra, roxo = aprendizado, círculo =
  meta redonda.
- `mapa_base.PEDAGIOS` são os rótulos em cima da seta (D&A, IR/CSLL, Δ giro, CAPEX, serviço
  da dívida): a conta ATRAVESSA, mas não são objetivo de ninguém — por isso não viram nó.
- `.content{max-width:none}` no topo do template: o layout do app trava em 1280px e o mapa
  tem 5 colunas na financeira e 6 no apoio. Há ainda o botão **⛶ tela cheia**, que esconde
  sidebar e topbar (classe `mapa-cheio` no body).
- Chip de contagem só aparece no nível que TEM indicador — chip zerado rouba a linha da meta
  e não informa nada.

### `meta_txt` — a meta do mapa é frase, não número

`pe_objetivos.as_is`/`to_be` são **NUMERIC** (servem ao scorecard do wizard). A meta do mapa
é como o gestor a enuncia: "≤ 84% da ROL", "OTIF ≥ 95%", "spread líq. ≥ 13% a.a.". Por isso
existe `meta_txt TEXT` — gravar a frase em `to_be` derruba o seed inteiro com
`invalid input syntax for type numeric` (aconteceu em 22/08). `mapa_base.METAS_REF` traz a
meta de referência de cada um dos 40 nós; o seed grava, a tela edita no blur
(`PATCH /api/pe/<cid>/objetivos/<id>` pela whitelist) e semear de novo **não sobrescreve**.

### Medição do indicador — velocímetro, N/A e as linhas de receita (2026-08-22)

O painel que abre ao clicar num nó **não é mais leitura**: é a grade onde se digita meta e
realizado e onde se lê o desvio. A lógica vive em `app/medicao.py` — módulo PURO como
`bpmn_gen`/`org_chart`/`mapa_base` (teste de AST impede que passe a importar `db` ou `flask`,
senão a doutrina volta a morar dentro da rota).

- **Grão MENSAL; trimestre e semestre são SOMA calculada na leitura.** `pe_medicoes` (ciclo,
  indicador, ano, mês, meta, realizado), `UNIQUE(indicador, ano, mês)` — a tela salva no blur,
  então a célula é upsert. Não gravar acumulado é deliberado: seria uma segunda verdade que
  diverge do detalhe na primeira correção de mês fechado.
- **Ausência NÃO é zero** — a regra mais fácil de quebrar sem perceber. Meta `NULL` = "não
  aplicável" (jan/fev antes da janela de venda); realizado `NULL` = "ainda não medido".
  Nenhum dos dois tem atingimento nem cor. No acumulado a meta soma **só os meses com meta** e
  o realizado soma **tudo**: vender antes da janela prometida é superação, não erro a corrigir.
- **Velocímetro de percentuais FIXOS** (`PISO_ATENCAO`/`PISO_META`/`TETO_META`): `< 80%`
  vermelho · `80–99,9%` laranja · `100–120%` verde · `> 120%` azul. 100 e 120 EXATOS são
  verde. `faixa()` compara explicitamente em vez de varrer tabela de limites — com "limite
  inferior" o 120,05 caía na faixa errada.
- **⚠️ Estas faixas não são a régua do bônus.** `pe_indicadores.faixa_80/100/120` (decisão 22)
  guardam os VALORES da remuneração variável, com corte seco em 80% e sem interpolação. Aqui é
  semáforo de leitura. Se um dia tiverem de conversar, é ADR do Xayer — não refatoração de
  passagem. Há teste percorrendo a AST de `medicao.py` pra garantir a separação.
- **Indicador com filho é CALCULADO**: série = soma dos filhos, e `medicao_gravar` recusa
  gravação no pai com **409** em vez de aceitar em silêncio. Sustenta a decisão do Xayer "a
  soma das linhas de receita dá a ROL". `_series_do_objetivo` soma do nível mais fundo pro mais
  raso (operacional → tático → estratégico).
- **As 6 linhas de receita são doutrina** em `mapa_base.LINHAS_RECEITA`, penduradas em "ROL da
  safra (R$)" pelo NOME (por isso `validar()` recusa tático pendurado em indicador inexistente):
  Semente de soja · Grãos de soja · Fertilizantes e adubos · Defensivos agrícolas · Serviços de
  beneficiamento · Prêmios, campanhas e bonificações.
- **`_semear_taticos` preenche LACUNA, nunca sobrescreve** — e roda também em objetivo que já
  existia, que é o que leva a abertura da ROL a um ciclo semeado antes disso. Só entra onde não
  há **nenhum** tático; pai renomeado na tela é pulado de propósito (adivinhar erraria calado).
- Gotchas da tela: painel alargado pra 640px (grade de 12 meses não cabe em 420); input mostra
  número **sem separador de milhar** (o backend aceita vírgula decimal, mas "1.234" sem vírgula
  viraria 1,234); e o balde do período carrega `faixa_rotulo` separado de `rotulo` — espalhar
  `faixa()` cru fazia "T1" virar "na meta" na tela (bug pego na conferência, com regressão).

### O cartão mede e o `⤵` desce um nível (2026-08-22, mesmo dia)

- **Cartão do mapa mostra meta E medição** do indicador estratégico **principal** (o
  primeiro por `ordem`; `_medicao_dos_nos` depende do `ORDER BY objetivo_id, nivel, ordem`,
  onde 'estrategico' < 'operacional' < 'tatico' por alfabeto). Um cartão não cabe três
  indicadores — os outros aparecem no painel.
- **`medicao.resumo_ytd`: o acumulado do cartão para no MÊS CORRENTE.** É a regra que
  impede o painel de mentir — realizado de março contra meta de doze meses reprova a
  empresa inteira em março, e o desvio apareceria onde só há calendário. `meses_decorridos`
  recebe `hoje` por parâmetro pro módulo seguir puro e o teste fixar a data.
- **Clicar ≠ descer.** Clique no cartão → painel (*como evoluiu*). Botão `⤵` →
  `/pe/<cid>/desdobrar/<oid>` (*de que é feito*). No JS do mapa o handler de clique ignora
  `a.drill`, senão o botão abriria o painel junto com a navegação.
- **`desdobrar` é recursiva e genérica**: sem `?pai=` mostra o tático do objetivo; com
  `?pai=<ind>` mostra o operacional daquela linha. Serve as 4 perspectivas sem código
  específico — CPV abre a estrutura de custo e SG&A a administrativa pelo mesmo caminho.
- **⚠️ `?pai=` e não `/desdobrar/<oid>/<pai_id>`**: `test_acesso_pe` conta rotas × guardas
  1:1, e dois `bp.route` numa função só quebram a contagem. O mesmo teste conta por
  **substring** — nem docstring pode escrever o decorator do módulo estratégico por extenso
  (quebrou a contagem na primeira tentativa desta feature).
- **`_indicadores_medidos`** é a fonte única das séries (2 queries pro mapa inteiro, não uma
  por cartão) e aplica a regra do pai calculado do nível mais fundo pro mais raso.
- **CSS/JS em partials** (`_medicao_css.html`, `_medicao_js.html`) incluídos pelo mapa e pelo
  desdobramento — duas cópias divergiriam na primeira mudança de cor, e o módulo existe pro
  desvio se ler igual em qualquer nível. O partial exige `CID` e `ANO_INICIAL` já definidos,
  então o include vem DEPOIS do script que os declara.
- **`num`/`pct_texto` em `medicao.py`** como globais do Jinja: cartão renderiza no servidor,
  painel no cliente; casa decimal diferente faz o usuário achar que um dos dois erra.

### Próximo passo previsto

Aba de **Rituais** (reuniões de acompanhamento no modelo G4: Results mensal → FCA dos 5–7
desvios → Comitê de Receita 3×/semana → dailies → S&OP → Direx/Comex), reusando `pe_ritos` e
o módulo `/agenda` com feed `.ics`. O mapa é o que define os indicadores que os ritos cobram.

## Dimensões, medidas e ligações — a cadeia comercial (2026-08-23, ADR)

Módulo puro novo: `app/dimensoes.py` (sem banco, sem request — mesma linha de
`medicao`/`mapa_base`). O mapa deixou de só somar.

- **A regra que decide onde o dado mora:** *o que é intrínseco à COISA vai na árvore; o que é
  intrínseco à VENDA vai na medição.* Dimensões (colunas de `pe_medicoes`): `canal`
  (agricultor · multiplicador · distribuidor, todos com `gera_receita=True` — multiplicador é
  venda, não transferência interna), `condicao_pagto` (à vista × a prazo) e `origem` (venda
  direta × via agente de venda: é **uma comissão × duas**, não "interno × externo" — o RC está
  sempre lá). `dimensoes.COLUNAS` é a fonte única: rota, JS do painel e importação leem dali,
  então dimensão nova entra sem passar por essas funções (foi assim que `origem` entrou).
- **`NOT NULL DEFAULT ''`, nunca `NULL`** — `NULL <> NULL` em índice único deixaria duplicata
  entrar sem o banco reclamar. `''` significa *sem discriminação*. **Invariante, barrada com
  409 na gravação:** para o mesmo (indicador, ano, mês, medida) **ou** existe a linha `''`
  **ou** existem as discriminadas — nunca as duas (senão "todos" soma total + partes e dobra o
  faturamento, com os dois números plausíveis). Índice:
  `ux_pe_medicoes(indicador_id, ano, mes, medida, canal, condicao_pagto, origem)`.
- **Três tipos de MEDIDA** (`pe_indicadores.tipo_medida`): `aditiva` · `razao` (NUNCA soma —
  ticket médio, taxa de conversão, todo %) · `formula` (`valor = volume × ticket`). **Três
  tipos de LIGAÇÃO** (`tipo_ligacao`, mora no FILHO porque descreve a relação dele com o pai):
  `soma` · `formula` · **`direcionador`** — o filho *explica* o pai e o motor o **ignora ao
  somar** (o funil pendura no volume; lead não é bag).
- **`medida` é COLUNA, não indicador irmão**: `valor` (R$, universal), `volume` (bag) e
  `ticket` (R$/bag) — os dois últimos só do nó *Semente de soja* pra baixo, e lá `valor` deixa
  de ser digitável. **Medida nomeada só sobe se TODOS os filhos que a compõem tiverem** — é o
  que impede bag de vazar pra Receita bruta e o ticket de virar R$ de fertilizante ÷ bag de
  semente. Um indicador por medida dobraria as 40 cultivares para 80.
- **`sinal` (+1/−1)** resolve dedução como filha normal da árvore de soma: **ROL = receita
  bruta − deduções**. Sem esse andar, `volume × ticket` bateria contra número que já tem
  imposto descontado.
- **`espelha_id` / `espelha_medida` — uma árvore, duas leituras.** O "Volume vendido (bag)" do
  P5 não tem série própria: lê a medida `volume` do nó *Semente de soja*, na árvore da ROL.
  `_seguir_espelho` traz a árvore do espelhado; alvo não encontrado deixa o espelho
  **desligado** de propósito (cartão vazio se explica; cartão com número de outro ramo não). O
  nó espelhado NÃO entra como linha extra — o cabeçalho da tela já é ele.
- **`direcao` + `tolerancia`** (`maior_melhor` | `menor_melhor` | `estabilizar`): sem isso CPV,
  inadimplência, prazo e desconto aparecem VERDES justamente quando vão mal, e o consolidado do
  objetivo inverte sem estourar. **`peso`** (indicador e objetivo) → `medicao.consolidado`:
  parcela sem atingimento **sai da conta e os pesos renormalizam** (zero seria inventar
  desvio), peso ≤ 0 também sai, e cada parcela tem **teto de 120%** (`TETO_PARCELA`) — as
  condições de um objetivo são simultâneas, superação não paga falha alheia.
- **`nivel` é RÓTULO; a hierarquia real é `pai_id`** e a agregação soma **da profundidade maior
  para a menor** (portfólio e obtentora dividem `tatico`). Somar por rótulo fazia o portfólio
  nunca receber a soma das obtentoras — número errado, sem erro.
- **A razão do pai pondera pelo PAR CASADO**, célula a célula (mês × dimensão): só entra o
  filho que tem as **duas** parcelas. Vale em três lugares, porque o erro tinha três portas:
  `agregar_pai` (série do pai), `_razao_pares` (acumulado no tempo) e o espelho. Caso real: 7
  cultivares com meta de volume e 4 com meta de ticket deram um ticket-meta **abaixo das quatro
  metas existentes** — média ponderada mora entre o menor e o maior do que ela pondera.
- **Migração embutida na semeadura** (tudo idempotente): **adota andar** (as 6 linhas de
  receita passam pra baixo de *Receita bruta* — sem adotar, criaria seis irmãs novas e a ROL
  contaria o faturamento duas vezes), **realinha doutrina** (`medidas`, `sinal`, `tipo_ligacao`
  em nó que já existe, preservando nome/unidade/ordem, que são conteúdo do usuário) e **cria
  indicador estratégico em objetivo que já existe** (o beco que travou as linhas de receita em
  22/08). Aposentadoria só de `INDICADORES_APOSENTADOS`, e só sem medição e sem filho.

### O laboratório entra na cadeia (2026-08-29 — ADR 2026-08-29)

A análise de qualidade da semente acontece **três vezes** na safra e não estava no mapa:
pré-colheita (amostra do campo → **libera colher**), recebimento na unidade (aceita o lote) e
pós-beneficiamento na UBS (**laudo que aprova ou descarta**). Virou o objetivo `laboratorio` —
*Laboratório e qualidade da semente* — no passo **⑥**.

- **Três setas de entrada, uma de saída:** `cooperados → laboratorio`, `logistica → laboratorio`
  e `ubs → laboratorio` (as duas primeiras como secundárias); a única saída de cadeia é
  `laboratorio → comercializacao`. **Comercializa-se o lote APROVADO, não o beneficiado.**
- Mora **depois** da UBS porque a posição na fila é a do **último laudo**, que é o que autoriza
  vender; as setas contam que ele também atua antes — mesma leitura que o crédito já tinha
  (posição no tempo ≠ função).
- A ligação `ubs → comercializacao` **saiu** e virou a primeira entrada de
  `mapa_base.LIGACOES_SUPERADAS`: a semeadura agora **apaga** as setas nomeadas ali, senão um
  ciclo semeado antes ficaria com o caminho velho e o novo desenhados juntos.
- `laboratorio → entrega` (sobe): reclamação de campo por germinação/vigor nasce no laudo.
- **Renumeração:** comercialização **⑦/P7**, expedição **⑧/P8**; a esteira financeira desce
  junto **por necessidade** (crédito P9, cobrança P10, barter P11, mesa P12) — `passo`, `col` e
  `cod` são travados para contar a mesma ordem, e dois nós em P8 seria erro.
- ⚠️ **Ciclo já semeado só recebe isso ao apertar “semear” de novo** — a semeadura é
  idempotente e não roda sozinha.
- Indicadores candidatos: germinação (%), vigor (%), descarte por lote (%), tempo amostra→laudo
  (dias) e % de lotes com laudo antes da liberação. Meta de referência: *germinação ≥ 80% ·
  descarte ≤ (definir)*.

## Realizado ligado na fonte — passo 2 (2026-08-24→27, ADR 2026-08-29)

`POST /api/pe/<cid>/medicoes/importar-estoque` (só o condutor). Três módulos **PUROS** recebem
o payload e devolvem consolidado + relatório; a rota só faz o GET e a gravação.

- **Cada pergunta tem um dono, e o dono é LIDO — não reimplementado:**
  `estoque_sa.py` ← `GET /api/estoque` do **agente-estoque** (bags por cultivar; ele já
  autentica no SA e converte embalagem → bag) · `financeiro_sa.py` ← `/api/dataset` do
  **agente-financeiro-sa** (receita e ticket realizados) · `preco_meta.py` ← SQL direto no
  schema `precificacao` do mesmo banco (a **meta** do ticket). Não falar com o Simple Agro
  daqui é decisão: duas contas de bag divergem no primeiro pedido com embalagem nova, e o
  ticket precisa ser razão da **mesma** fonte (receita ÷ bags do painel comercial).
- **Meta do volume = estoque + compra − qualidade, inteira no MÊS 1** — o disponível para
  vender. Estoque não tem mês: é meta de **safra**. Daí a visão **`anual`** em
  `medicao.PERIODOS` (um balde com os 12 meses): é a única em que meta de safra e realizado se
  comparam sem ressalva; a grade avisa na tela que a meta é da safra e não do mês.
- **Meta do ticket = tabela de preço, em três recortes que são doutrina** (`preco_meta.py`):
  **tier `ALTO`** (é a medalha *Ouro* do painel de precificação; `cultivares.tier` só aceita
  ALTO/MEDIO/BAIXO — procurar por `'ouro'` leu 25.914 linhas e casou **zero** em 24/08),
  **estado `GOIAS` por extenso** (sigla não casa; aproximação consciente por causa do ICMS) e o
  preço **À VISTA, inteiro no mês 1** (o à vista é a base da tabela; os meses são base + juro, e
  o juro já tem lugar próprio na dimensão `condicao_pagto` — embutido na meta, a meta subiria
  junto com o prazo concedido, e metas em meses diferentes deixariam `valor = volume × ticket`
  ausente em TODO mês). Consequência assumida: venda a prazo tende a ficar ACIMA da meta.
- **`variantes()` é a única licença pra casar nome:** a precificação escreve o código do ERP
  **entre parênteses** quando difere do nome comercial (`'NEO690 I2X (690 I2X)'`) — o parêntese
  é o de-para declarado pelo cadastro. Nada de similaridade.
- **Cultivar sem preço fica SEM meta, nunca zero** — zero pintaria de vermelho quem não tem
  promessa (mesma doutrina do N/A ≠ zero).
- **A importação roda inteira ou não roda:** célula já lançada **discriminada** é pulada e
  reportada (total + detalhe no mesmo mês contaria o bag duas vezes); o relatório separa **bags
  LIDOS de bags GRAVADOS** — a diferença é o volume que não subiu pra receita de ninguém
  (relatar só o lido fez a 1ª importação parecer completa com duas cultivares fora); e **não se
  inventa canal** (`uso_semente` traz AGRICULTOR e DISTRIBUIÇÃO; o multiplicador não apareceu
  em pedido nenhum — os usos voltam no relatório com os bags pra confirmação). Fonte fora do ar
  devolve **502 com a URL da fonte**, sem gravar parcial.
- **Candidatos da gravação:** folha operacional (`NOT EXISTS` filho) que **declare** `volume` em
  `medidas` — pai é calculado, e bag em nó que não carrega bag não sobe pra lugar nenhum.
- **Leitura isolada — uma unidade por tela:** `_cartao(i, principal)` zera `medidas` no cartão
  do desdobramento (R$ entrando pela financeira, bag entrando pelo comercial: mesmo nó, mesma
  árvore, leitura diferente). Misturar unidade na linha é o caminho pra somar bag com tonelada.
- **Rotas do desdobramento:** `/pe/<cid>/desdobrar/<oid>` (recursiva, `?pai=`, `?medida=`),
  `GET /api/pe/<cid>/indicador/<iid>`, `POST /api/pe/<cid>/indicador/<iid>/medicoes`,
  `POST /api/pe/<cid>/objetivo/<oid>/semear-taticos`. Todas `@exige_pe()` — `test_acesso_pe`
  conta rotas × guardas por **substring**.
- **Env novas (com default):** `ESTOQUE_URL`/`ESTOQUE_TIMEOUT` e
  `FINANCEIRO_URL`/`FINANCEIRO_TIMEOUT`.
- **Portfólio:** Golden Harvest entrou em 24/08 no **portfólio de terceiros**
  (`mapa_base.OBTENTORAS_TERCEIROS`) — 6 obtentoras, 40 cultivares.

## Cadastros do `/admin` (2026-08-27)

Editar e excluir **área** e **cargo**, com trava contra exclusão em cascata (recusa com motivo
em vez de desvincular calado). E a **função do cargo vem do catálogo AD002**
(`cargos_funcoes.funcao_id` → `funcoes`), não de casar texto por semelhança — nome parecido não
é a mesma função. Mesmo princípio do de-para por parêntese na precificação: só casa o que o
cadastro declara.

## Inventário: editar e excluir (2026-08-29 — lote 1: "onde tem inserção, tem editar e excluir")

Rotas `POST /processos/<pid>/editar|excluir` e `POST /macroprocessos/<mid>/editar|excluir`,
todas `@exige_login("gestor")` — dono_processo não alcança. Na home, cada linha do inventário
alterna leitura/edição por CSS+checkbox (sem JS): identificador, nome, resumo, macroprocesso,
área e prioridade.

- **Excluir processo leva TUDO**: `processo_versoes.processo_id` é ON DELETE CASCADE e a versão
  cascateia em ~18 tabelas. Não existe "excluir só o processo" — ou vai tudo, ou não vai. A
  decisão do Xayer (24/08) foi **permitir, com aviso do que vai embora**: a confirmação conta
  versões, atividades e riscos, com os números vindos da **mesma query que monta a lista** (de
  outra fonte, o aviso divergiria do que a tela mostra).
- **Macroprocesso é o caso oposto:** `processos.macroprocesso_id` **não** é cascata — ou se
  recusa com o motivo, ou o banco estoura na cara do usuário. Desvincular em silêncio seria
  pior: o agrupamento início-ao-fim sumiria sem rastro.
- **Os `<form>` ficam FORA da tabela** e os campos se ligam a eles por `form="fp<id>"`: form que
  abre numa `<td>` e fecha em outra é HTML inválido — o navegador o retira da tabela e os campos
  param de enviar, calados.
- `_volta_home(erro)` devolve o motivo numa faixa no topo da home. Sem ela, "não excluí porque 3
  processos ainda estão no macro" seria uma lista que voltou igual.
- 11 testes em `tests/test_inventario.py`. Suíte em 459.

## Lote 2: excluir ciclo, excluir versão, editar item (2026-08-29)

Segundo lote da diretriz *onde tem inserção, tem editar e excluir*.

- **Excluir ciclo do planejamento** — `POST /pe/<cid>/excluir`, `@exige_pe()` + `_eh_condutor`
  (quem participa contribui, quem **conduz** decide — mesma régua de `consolidar` e `semear`).
  As **22 FKs** que apontam para `pe_ciclos` são todas ON DELETE CASCADE: vão junto objetivos,
  indicadores, medições, coleta individual, histórico de entrevista e as setas do mapa. A
  confirmação conta objetivos, indicadores, medições, sócios e escolhas — números vindos de
  `_lista_render()`, a mesma query que monta a tela.
- **Excluir versão do processo** — `POST /cockpit/versao/<vid>/excluir`, gestor+ com guarda de
  área (a fila da tela já filtra, mas o POST não é a tela). **A versão VIGENTE não se exclui**
  (decisão 8: vigente é imutável e é a governança publicada) — a tela não mostra o botão e a
  rota recusa com o motivo; para tirá-la do ar, publica-se outra no lugar (que marca a
  anterior como obsoleta) ou exclui-se o processo inteiro.
- **Editar item do wizard** — `GET` e `PATCH /api/versao/<vid>/itens/<tabela>/<iid>`, com a
  **mesma whitelist do criar** (`TABELAS`) **menos as colunas de VÍNCULO**: `atividade_id` não
  se edita, senão o item mudaria de dono em silêncio (quem quer mudar de atividade apaga e cria
  do outro lado). Campo vazio vira NULL, como no `criar_item`. Coluna fora da whitelist é
  ignorada **em silêncio de propósito** — recusar a requisição inteira por um campo a mais
  transformaria qualquer evolução da tela em erro na cara do usuário. E o PATCH **não** reescreve
  a biblioteca: `_upsert_biblioteca` roda na criação, quando o item nasce.
- **O ✎ é injetado, não escrito à mão.** `base.html` varre no `DOMContentLoaded` os botões que já
  chamam `delItem(vid,'tabela',id)` e insere ao lado um ✎ que abre um editor genérico — são ~25
  listas hoje, e lista nova ganha edição de graça. As colunas do modal vêm do **servidor**
  (`colunas` da resposta do GET); whitelist repetida no cliente vira uma segunda verdade, e a que
  diverge é sempre a que ninguém está olhando. O valor entra por propriedade (`.value = txt`),
  não por HTML — aspas e `<` no dado não quebram a tela.
- 16 testes em `tests/test_lote2_editar_excluir.py`; suíte em **475**.

## Lote 3: os cadastros que só sabiam inserir (2026-08-29)

Fecha a diretriz *onde tem inserção, tem editar e excluir* nos cadastros. A regra que atravessa
todos: **exclusão que o banco recusaria vira recusa explicada na tela** — `riscos.biblioteca_id`,
`area_funcao.funcao_id`, `cargos_funcoes.funcao_id` e `af_itens.catalogo_id` referenciam **sem**
cascata; apagar em uso estouraria erro cru, e desligar em silêncio seria pior (o vínculo sumiria
sem ninguém pedir).

- **Bibliotecas** (`/bibliotecas`) — linha editável e × por item. Excluir só o que tem `usos = 0`;
  a tela nem mostra o botão quando há uso, e a rota recusa com o número. Renomear é seguro: as
  instâncias apontam por `biblioteca_id`, não por texto.
- **Função do catálogo AD002** (`/org`) — editar identificador, nome e nível; remover só quando
  não há **par área×função** nem **cargo** apontando (`n_areas` e `n_cargos` na mesma query que
  monta a lista).
- **Item do catálogo organizacional** — editar nome/ordem e remover, com recusa quando está em
  `af_itens` (o mapeamento consolidado do par).
- **Colaborador** (`/admin`) — agora se edita nome, e-mail, perfil, área, cargo e, opcionalmente,
  a senha. Três travas: e-mail repetido é recusado com frase; **senha em branco não troca a
  senha** (campo vazio = "não mexi nisso"); e **o último admin ativo não pode ser rebaixado** —
  rebaixá-lo trancaria todo mundo do lado de fora e o conserto seria no banco. **Excluir
  colaborador não existe de propósito**: ele assina histórico (eventos de status, contribuições
  da coleta, autoria de melhoria) — quem sai é *desativado*.
- **Documento** — botão "× excluir documento" na tela do editor, que apaga o documento e as
  seções (`doc_secoes` é cascata) e **volta pra revisão**: o genérico responde JSON, e quem apaga
  o que estava escrevendo ficaria olhando a própria página apagada.
- **Recomeçar conversa** nas duas entrevistas (`/versao/<vid>/entrevista` e
  `/pe/<cid>/entrevista`) — apaga **só o fio do chat**. O que o copiloto já aplicou (atividade,
  SIPOC, decisão, oportunidade; sócios, arena, escolhas) **fica**: "começar de novo" não quer
  dizer desfazer trabalho aprovado. No PE, cada um limpa o **seu** fio (a coleta individual é
  sigilosa) e o fio do **grupo** só o condutor limpa. Teste extrai os alvos de todo `DELETE FROM`
  do corpo e exige que sejam só as tabelas de mensagem.
- 16 testes em `tests/test_lote3_cadastros.py`; suíte em **491**.

**Fica de fora, e é decisão pendente:** *desfazer a importação de estoque*. Hoje não há como
saber quais linhas de `pe_medicoes` vieram da importação — `origem` já é a **dimensão** da venda
(direta × via agente), não procedência. Marcar procedência é coluna nova e muda o grão da
tabela: é ADR, não conserto de passagem.

## Roadmap restante (blueprint)
F5: cargas SE (GRC/CPM/ECM/Competências via MCP/SOAP) + instanciar workflow.
F6: construtores de governança (políticas, POPs gerados das atividades, espec. formulário
eletrônico, requisitos de artefato→Maná Builder). Pendências: round-trip .bpmn no SE real;
tela de requisito auditável do SE (de-para fino).
