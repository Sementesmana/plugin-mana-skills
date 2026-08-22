---
name: agente-governanca
description: Plataforma de Governança por Processo da Sementes Maná — Flask+PG (schema governanca)+Railway: as áreas constroem a governança de cada processo em wizard guiado (SIPOC, tartaruga de 2 níveis, IC×IV Falconi, riscos↔controles N:N, requisitos auditáveis, versionamento AS IS→TO BE) e a plataforma gera o .bpmn no dialeto SoftExpert. Inclui o módulo de PLANEJAMENTO ESTRATÉGICO (Maná-Estratégia, método Antônio Napoli em 10 etapas, tabelas pe_*, coleta individual antes da reunião, acesso FECHADO por padrão via colaboradores.acesso_pe, lido do banco a cada request) e o Maná Results (mapa estratégico BSC, semeadura idempotente, desdobramento estratégico→tático→operacional), mais importador Bizagi/BPMN, organograma gráfico, agenda com .ics e construtor de documentos. Use SEMPRE no agente-governanca. Também quando mencionar: Maná Mapeia, Maná-Estratégia, Maná Results, mapa estratégico, BSC, RFL, tartaruga, requisito auditável, dialeto BPMN SE, pe_ciclos, acesso_pe, método Napoli, cockpit.
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
- **Ordem da cadeia da safra** (correção explícita do Xayer): planejamento → cooperados →
  logística interna → **UBS (beneficiamento/armazenagem) → comercialização → expedição**.
  Vende depois de beneficiar; expede depois de vender.
- **Marketing é faixa transversal** (`formato='faixa'`), não etapa: permeia o ciclo inteiro.
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

### Próximo passo previsto

Aba de **Rituais** (reuniões de acompanhamento no modelo G4: Results mensal → FCA dos 5–7
desvios → Comitê de Receita 3×/semana → dailies → S&OP → Direx/Comex), reusando `pe_ritos` e
o módulo `/agenda` com feed `.ics`. O mapa é o que define os indicadores que os ritos cobram.

## Roadmap restante (blueprint)
F5: cargas SE (GRC/CPM/ECM/Competências via MCP/SOAP) + instanciar workflow.
F6: construtores de governança (políticas, POPs gerados das atividades, espec. formulário
eletrônico, requisitos de artefato→Maná Builder). Pendências: round-trip .bpmn no SE real;
tela de requisito auditável do SE (de-para fino).
