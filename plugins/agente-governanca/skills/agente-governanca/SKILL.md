---
name: agente-governanca
description: Plataforma de Governança por Processo da Sementes Maná — app Flask+PG (schema governanca)+Railway onde as áreas constroem a governança de cada processo em wizard guiado (SIPOC Bloco A, tartaruga Bloco B, zoom por atividade Bloco C), com IC×IV Falconi, riscos↔controles N:N, requisitos auditáveis, versionamento AS IS→TO BE e geração de .bpmn no dialeto SoftExpert (lane por geometria, sem flowNodeRef/conditionExpression). Use SEMPRE que trabalhar no agente-governanca — wizard, tartaruga, SIPOC, BPMN export, cockpit, state machine, organograma D-G-S-A, capacitação embutida, copiloto gateway. Também quando mencionar: Maná Mapeia, plataforma de governança, mapeamento de processo, diagrama de tartaruga, item de controle, item de verificação, requisito auditável, dialeto BPMN SE, funil de automação, inventário de processos.
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

## Roadmap restante (blueprint)
F5: cargas SE (GRC/CPM/ECM/Competências via MCP/SOAP) + instanciar workflow.
F6: construtores de governança (políticas, POPs gerados das atividades, espec. formulário
eletrônico, requisitos de artefato→Maná Builder). Pendências: round-trip .bpmn no SE real;
tela de requisito auditável do SE (de-para fino).
