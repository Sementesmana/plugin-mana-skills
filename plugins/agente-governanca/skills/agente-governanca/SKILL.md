---
name: agente-governanca
description: "Mapa do agente-governanca (Sementes Maná), Flask+PG (schema governanca)+Railway: governança por processo (wizard SIPOC/tartaruga, IC×IV, riscos↔controles, requisito auditável, .bpmn dialeto SoftExpert), Planejamento Estratégico/Maná-Estratégia (método Napoli, pe_*, acesso_pe), Maná Results/BSC (mapa estratégico, meta × realizado) e SCEM. Traz o que o código não diz: decisões, armadilhas, contratos externos e pendências. Use SEMPRE ao mexer no agente-governanca ou ao citar governança por processo, wizard SIPOC/tartaruga, requisito auditável, .bpmn dialeto SoftExpert, Maná-Estratégia, Maná Results, BSC, acesso_pe ou SCEM."
---

# agente-governanca — mapa

## O que é
- Ambiente de DESENVOLVIMENTO da governança (Camada 5, app N2, dono: Xayer). A área constrói aqui a governança do processo; especialistas + Xayer transpõem para o SoftExpert, que é a PRODUÇÃO. Ao lado, dois módulos estratégicos: `/pe` (Planejamento Estratégico + Maná Results) e `/scem` (condução do board).
- Repo `Sementesmana/agente-governanca`; Railway por git push (Dockerfile, healthcheck `/health`). Produção: https://agente-governanca-production.up.railway.app (projeto Railway "Agente - Governaça"). Deploy confirmado pelo monitor: `/api/railway/deploys`.
- Banco-mana, schema `governanca`, criado e migrado no boot por `app/schema.sql`.
- Blueprint mestre (as 21 decisões do Xayer): `ManaVault/00-Inbox/2026-08-07-blueprint-mana-mapeia.md`.

## Onde está a verdade
- `app/schema.sql` — banco inteiro + migrações idempotentes; os comentários dizem o porquê de cada coluna.
- `app/main.py` — login, `/convite/<token>`, `/health` (`TABELAS_ESPERADAS`), cronômetro+gzip, sobe a rotina noturna.
- `app/auth.py` — JWT, papéis, `pode_pe`/`pode_abrir_scem`, token de escopo dos convites, cookie do iframe.
- Processo: `routes_wizard.py` (wizard, Bloco C, revisão, CRUD genérico `TABELAS`) · `routes_cockpit.py` (state machine, `nova_versao`) · `routes_entrevista.py`+`copiloto.py` (entrevista com IA) · `routes_docs.py` (POP/IT/política/norma) · `bpmn_gen.py` (dialeto SE + preview SVG) · `routes_import.py`+`bizagi_import.py` · `routes_org.py`+`org_chart.py` · `routes_agenda.py`+`agenda_ics.py` · `seed_exemplo.py` (gabarito CRE-001).
- Estratégia: `routes_pe.py` (todas as rotas do `/pe`) · `consultor.py` (método Napoli e travas) · `mapa_base.py` (mapa BSC de referência = doutrina) · módulos PUROS `medicao`, `dimensoes`, `analise`, `matriz`, `condicao_pagto`, `agenda` · leitores `estoque_sa`, `financeiro_sa`, `preco_meta` · `explicador.py` (IA que lê o gap) · `rotina.py`+`notificacao.py` (importação de madrugada).
- SCEM: `scem.py` (movimentos, travas, estados — ⚠ a ordem VERDADEIRA está no bloco de ajustes no FIM do arquivo: sócios = pré-requisito, Leitura do jogo = M1, ambição ANTES do ponto crucial; a docstring do topo e o literal `MOVIMENTOS` estão defasados — não "consertar" por eles) · `scem_perguntas.py` (roteiro) · `routes_scem.py` · `scem_ia.py` · `scem_consultor.py` · `scem_formulacao.py` (educacional).
- `tests/` — boa parte das regras abaixo está travada por teste que LÊ o código (AST/substring). Teste vermelho aqui costuma ser doutrina, não bug do teste.
- Capacitações: processos = `static/capacitacao.html` (cópia do deck — atualizar junto com o deck). Estratégia = `scem_formulacao.py` + `templates/scem_formulacao.html`, gerada do `scem` desde 2026-09-25; `static/capacitacao-estrategia.html` é MORTO (ninguém serve), não editar.
- Legados que não se pode limpar: `cargos_funcoes` só existe por causa de `colaboradores.cargo_id` — o catálogo vivo de papéis é `funcoes`. Classes CSS `.card`, `table.mana`, `.pill`, `.linha` são contrato com dezenas de templates: não renomear.

## Regras e decisões que o código não explica sozinho

### Processo
- **Dialeto BPMN SE** (decodificado do export real do CRE-001): lanes SEM `flowNodeRef` (raia = geometria Y), rótulo do ramo no `name` do sequenceFlow SEM `conditionExpression`, fim com terminate, 130×80/56×56/50×50, lane 317px. A ausência É o dialeto: não "corrigir". `atv_id` (fluxo clicável) e artefatos só vão para o preview SVG, nunca para o XML.
- **Tartaruga polimórfica**: `atividade_id NULL` = nível processo, preenchido = atividade (espelha o PM009 do SE). `app_requisitos` usa o mesmo padrão: NULL = app do processo, preenchido = agente de IA da atividade.
- **Versionamento**: vigente é imutável e não se exclui; revisão = cópia completa com remapeamento de ids (`nova_versao`); publicar torna a anterior obsoleta. Coluna nova em tabela de versão tem de entrar na cópia (já se perdeu `tipo_execucao`/`alcada` assim).
- `nova_versao` NÃO copia `escopo` (a versão nova nasce `completo`: "avança um nível a cada versão") e COPIA `destino_automacao`. As duas coisas são de propósito.
- `escopo='mapeamento'` = só fluxo + SIPOC + oportunidades; a checagem de completude não cobra riscos, indicadores ou documentos fora do escopo.
- IC no nível processo, IV na atividade (Falconi).
- **Núcleo determinístico**: a IA é opcional, só via mana-llm-gateway, e sem env a UI esconde os botões. Trava nunca vai para o prompt: o LLM sugere, o núcleo decide. Ao LLM vai só estrutura de processo, nunca nome de pessoa.
- No prompt da entrevista, não "encurtar": doutrina "MAPEAR PARA AUTOMATIZAR" (atividade manual → gap → oportunidade), blocos DESTINO DA AUTOMAÇÃO e AGENTE DE IA. Os valores de `tipo_execucao` são contrato com prompt e template. As categorias de `app_requisitos` são o insumo do Maná Builder: não simplificar.
- Exemplo CRE-001 é gabarito somente-leitura (`_versao_ou_403(escrita=True)` barra gravação de não-admin).
- "Biblioteca por trás, wizard na frente": instâncias por versão com `biblioteca_id`. Não remover as tabelas por versão. A biblioteca é alimentada só na criação do item.
- Editar item: mesma whitelist do criar, MENOS colunas de vínculo (item não muda de atividade em silêncio). Coluna fora da whitelist é ignorada de propósito.
- **Exclusão**: o que o banco recusaria vira recusa explicada na tela; nunca desvincular calado. Excluir processo leva tudo em cascata, com aviso contado pela mesma query da lista. Colaborador não se exclui (assina histórico): desativa. O último admin ativo não pode ser rebaixado.
- **Só casa o que o cadastro declara**: função do cargo pelo id do catálogo AD002; cultivar ERP×comercial só pelo parêntese da precificação. Nada de similaridade de texto.
- Documento construído recomeça vazio na versão nova (por design). Layout visual próprio da empresa como template NÃO existe: o import só extrai a estrutura de seções. Não prometer.
- "Recomeçar conversa" apaga só o fio do chat; o que o copiloto já aplicou fica.

### Planejamento Estratégico e Maná Results (`/pe`)
- **Acesso FECHADO**: `colaboradores.acesso_pe` default FALSE. `pode_pe()` lê do banco a cada request para a revogação valer na hora: não migrar para o token "por performance". Entram admin, quem tem a flag, participante de ciclo (`pe_participantes`) ou de sessão SCEM. `pode_abrir_scem()` é mais estreito (admin ou flag), senão convidado convida e distribui acesso que ninguém lhe deu.
- Método = **Antônio Napoli** (não o workbook do G4, que foi substituído). A ordem das etapas é o produto (pular devolve 409). Cada etapa se explica na tela antes de perguntar: pergunta sem explicação foi reclamação explícita do Xayer.
- Desdobramento só nesta ordem: estrutura → cultura → sistema de gestão → incentivo. Régua do bônus com **corte seco em 80%, sem interpolação** (79% = zero). Mexer nas constantes é mudar doutrina e o teste junto.
- Coleta individual: `autor_id NULL` = plano, preenchido = contribuição. Só as etapas de percepção se coletam sozinho, com sigilo até todos concluírem. Quem conduz decide: consolidar, semear, importar e excluir ciclo são do condutor.
- **O nó do mapa É `pe_objetivos`** com `perspectiva` preenchida. Não criar tabela de nó: o desdobramento estratégico → tático → operacional sai de graça de `pe_indicadores.pai_id`.
- **Semear é idempotente e não sobrescreve** o que o usuário editou (índice `ux_pe_objetivos_chave`); valida `mapa_base` antes de gravar. Ciclo já semeado só recebe mudança do mapa base quando alguém aperta "semear" de novo (é aí que as setas de `LIGACOES_SUPERADAS` são apagadas).
- **`mapa_base.py` é doutrina validada com o Xayer**, não desenho. Corte Falconi: EBITDA = competência operacional, RFL (Resultado Financeiro Líquido) = financeira, e a mesa sobe pro RFL, nunca pro EBITDA. Caixa só recebe seta. A cadeia da safra segue o negócio (lote APROVADO no laboratório é que se comercializa; crédito fica entre comercialização e faturamento e continua competência financeira, porque posição no tempo ≠ competência). Marketing é etapa. Clientes seguem o ciclo de vida. Cor e traço da seta são semânticos. Não "arrumar" sem falar com o Xayer.
- Meta do mapa é frase (`meta_txt`): `as_is`/`to_be` são NUMERIC, e a frase ali já derrubou o seed.
- **Medição**: grão mensal; trimestre/semestre/ano são somados na leitura (não gravar acumulado). **Ausência ≠ zero**: meta NULL = não aplicável, realizado NULL = não medido, e nenhum dos dois tem cor. O acumulado do cartão para no mês corrente.
- O velocímetro 80/100/120 é semáforo de leitura, **não a régua do bônus**. Uni-los exige ADR do Xayer.
- Pai com filhos é calculado (gravar nele → 409). A agregação segue `pai_id` da profundidade maior para a menor (`nivel` é só rótulo). Razão (todo %, ticket) nunca soma e pondera pelo par casado. `direcionador` explica e não soma. `sinal` −1 deduz (ROL = bruta − deduções). `direcao` impede CPV/inadimplência verdes quando vão mal. No consolidado, parcela sem dado sai e os pesos renormalizam, com teto de 120% por parcela.
- "**O que é intrínseco à COISA vai na árvore; o que é intrínseco à VENDA vai na medição.**" As dimensões são colunas de `pe_medicoes`, `NOT NULL DEFAULT ''` (NULL escaparia do índice único). Invariante (409): numa célula existe a linha `''` OU as discriminadas, nunca as duas. `dimensoes.COLUNAS` é a fonte única. Vendedor/UF/município são abertas porque a grafia do ERP varia; município = `NOME/UF` canonizado.
- A medida (`valor`/`volume`/`ticket`) é coluna, não indicador irmão; a medida nomeada só sobe se todos os filhos a tiverem (assim bag não vaza para a receita bruta).
- `pe_desejos`/`pe_alinhamento` são órfãs da versão workbook: não usar e não dropar (dado de ciclo antigo).

### SCEM (`/scem`)
- Existe porque um exemplo falado pelo Xayer foi registrado como objetivo decidido. Fala é fala, a consolidação é proposta, e só vira compromisso a **decisão** com os 4 campos (texto, o que exclui, condição que revoga, quem decidiu).
- A rodada individual saiu em 20/09 e voltou em 24/09 **assíncrona, em casa, com prazo**. Enquanto a fase é `coleta`, texto de terceiro não sai do banco: o filtro mora na CONSULTA (`_falas_visiveis`), não no template. A IA não lê antes de expor (409). Expor é definitivo.
- O bloco dos **sócios** não abre para não-sócio, nem depois de exposto, nem por convite.
- **Convite por link de WhatsApp, sem senha** (decisão de 01/10/2026): o link É a credencial. O token de escopo é estreito, numa lista fechada (`_ESCOPO_ROTAS`), e rota nova nasce fora. São dois links (preparação × folha) para o condutor decidir quando a rodada começa. O banco guarda só o sha256.
- Duas passadas da IA: **organizar** não propõe produto (o código zera mesmo se o modelo insistir) e **alinhar** propõe. A pauta do tópico descarta produto/síntese. Sem isso o board discute o texto da IA em vez do assunto.
- Ambição sai **sem número**; número só no último movimento (objetivos). A ambição vem antes do ponto crucial, que mede importância contra ela. A chave `crux` é dado: não renomear.
- O caso de ponta a ponta é fictício ("Sementes Vale Claro"), nunca a Maná. Os exemplos das perguntas são sempre hipotéticos.
- O consultor de plantão não fura o lacre, não responde no lugar de ninguém e não personifica pessoa real.
- Distribuir preparação é do condutor; dar baixa é de quem faz. `/capacitacao-estrategia` fica sob login, não sob `acesso_pe` (convidado assiste antes).
- `scem_sessoes.ciclo_id` é a ÚNICA FK para `pe_ciclos` com SET NULL (decisão de board sobrevive ao ciclo). Outra exceção exige ADR.

## Armadilhas conhecidas (sintoma → causa → o que fazer)
- Telas com 500 ou `/health` degraded com `tabelas_faltando` → `schema.sql` roda numa transação só, e uma tabela criada antes da que ela referencia aborta tudo (v19 caiu assim) → criar depois da referenciada; o log `DDL FALHOU` diz qual comando quebrou. O fallback divide por `;`: evitar blocos `DO $$`.
- 502 na entrevista (`datetime is not JSON serializable`) → `json.dumps`/`jsonify` cru sobre linha do banco → usar `consultor._json_estado()` (fail-soft) ou `_serial()`.
- "Travou/ficou lento" no meio da entrevista → gunicorn mata o worker com o timeout padrão enquanto o LLM responde (até 60s), e com `-w 1` cai tudo → não baixar `--timeout 120`. Para lentidão: `[governanca][LENTO]` nos Deploy Logs e o header `X-Tempo-ms`.
- Login todo derrubado após atualizar PyJWT → `sub` numérico é recusado no 2.10+ → `sub` vai como string no token e volta int no `_decode`. O token NÃO tem `id`: usar `sub`.
- Rota sem guarda, ou decorator que "não faz nada" → `exige_login`/`exige_pe` são factories → sempre com parênteses.
- `test_acesso_pe` falha sem motivo aparente → ele conta `@exige_pe()` por substring contra o nº de rotas → não escrever o decorator em docstring; uma rota por função (por isso `?pai=` e não segunda rota).
- Template Jinja explode em runtime → macro declarada depois do uso (`pe_mapa.html`) → declarar no topo.
- `@click` sem efeito → fora de um `x-data` do Alpine. O wizard salva e recarrega preservando o hash: não trocar por estado client-side sem repensar.
- Campos do inventário param de enviar, calados → `<form>` atravessando `<td>` → form fora da tabela, campos com `form="..."`.
- Outlook recusa a assinatura sem mensagem → .ics fora do RFC (CRLF, folding em 75 octets, UTC, DTEND exclusivo) → manter os testes. `/agenda/<token>.ics` é sem login de propósito: o token é a proteção, então nada sensível na agenda.
- Cookie some dentro do SE → iframe de terceiro precisa de `SameSite=None; Secure` → usar `auth.opcoes_cookie()` (login e convite).
- Link de convite sai `http://` em produção → `request.url_root` atrás do proxy do Railway → usar `auth.base_publica()`.
- Condutor deslogado de si ao testar o próprio link → existe a tela de colisão. Não remover.
- "1.234" lido como 1,234 → input de medição sem separador de milhar, de propósito.
- Setas do mapa desalinhadas → legenda dentro do `#palco` → legenda acima; espessura base vem de `data-w` no `<path>`, nunca deduzida pela cor.
- Dado velho com cara de novo → a rotina das 5h (BRT) não rodou → a tela avisa acima de 30h e o histórico está em `pe_importacoes`. A regra é "passou das 5h e não houve sucesso hoje", não "a cada 24h"; tem advisory lock mesmo com `-w 1`; chama a MESMA função do botão.
- Entrevista mais lenta ao aumentar o histórico → só as 12 últimas mensagens vão ao LLM (o estado completo já vai no prompt).

## Contratos com sistemas externos
- **SoftExpert**: `.bpmn` no dialeto acima, importável no modelador. `/org` espelha a estrutura organizacional do SE (unidade AD003 → área → função AD002 → par área×função com catálogo unificado), com CSV no layout SE. Roda embutido em iframe do portal SE. Nada é escrito no SE por esta app.
- **Realizado do Maná Results** (cada pergunta tem um dono, que é LIDO e não reimplementado): volume ← `GET /api/estoque` do agente-estoque; receita/ticket ← `/api/dataset` do agente-financeiro-sa; meta do ticket ← SQL só-leitura em `precificacao.*` do banco-mana. Não falar com o Simple Agro daqui (contas de bag divergem; throttle 452).
- Meta do ticket: tier `ALTO` (= medalha "Ouro"; procurar "ouro" casa zero), estado `GOIAS` por extenso, preço à vista inteiro no mês 1. Cultivar sem preço fica sem meta, nunca zero. A meta do volume é da safra (produzido + compra − qualidade; devolução fica fora, já é dedução da receita) e só se lê sem ressalva na visão anual.
- A importação roda inteira ou não roda. Fonte fora → 502 com a URL. O relatório separa bags LIDOS × GRAVADOS. Não inventa canal.
- Corte à vista × a prazo (`CUTOFF_AVISTA_DIA/MES`) é espelho do agente-gestor-comercial: os dois têm de apontar o mesmo dia. A exceção manual do gestor vence, e decide o último vencimento do pedido.
- **WhatsApp** só pelo hub agente-whatsapp (alerta da rotina; `classe` + `idempotency_key` por requisição + `agente`). Sem chave → não avisa e não quebra. O destino é `WHATSAPP_GESTOR` (fallback `WHATSAPP_TI`).
- **LLM**: `LLM_GATEWAY_URL` é raiz https SEM `/v1` (sem protocolo, falha no boot). SCEM usa `mana-juridico`; explicador `mana-rapido`.
- Schemas: escrever só em `governanca`. Ler `precificacao` é exceção deliberada.

## Como testar e subir
- `pip install -r requirements.txt` e `pytest` SEM `DATABASE_URL` (os testes dublam o banco; o boot tolera ficar sem banco, não remover esse try/except). Suíte inteira verde antes de push.
- Regras do CLAUDE.md: não alterar código sem o Xayer pedir ("verificar" = reportar); confirmar antes de push.
- Deploy = git push → Railway builda o Dockerfile. Depois, conferir `/health`: `status: ok` e `tabelas_faltando` vazio.
- Env: `DATABASE_URL`, `JWT_SECRET`, `ADMIN_EMAIL`/`ADMIN_SENHA` (seed do 1º admin); opcionais `LLM_GATEWAY_URL/KEY`, `LLM_MODEL`, `ESTOQUE_URL`/`FINANCEIRO_URL` (+`_TIMEOUT`, default produção), `CUTOFF_AVISTA_DIA/MES`, `AGENTE_WHATSAPP_URL/API_KEY`, `WHATSAPP_GESTOR`. O `.env.example` só lista as primeiras.
- Mudança não-trivial → atualizar a nota do vault e esta skill; decisão arquitetural → ADR em `08-Decisoes`.

## Pendências conhecidas
- Desfazer importação de estoque: `pe_medicoes` não tem procedência (`origem` é dimensão da venda) e `pe_importacoes` registra a execução, não as linhas. Resolver exige ADR (muda o grão).
- Round-trip do `.bpmn` no SE real; tela de requisito auditável do SE (de-para fino).
- F5 (cargas SE GRC/CPM/ECM/Competências + instanciar workflow) e F6 (construtores de governança) do blueprint.
- Aba de Rituais (Results mensal → FCA → comitês), reusando `pe_ritos` + `/agenda`.
- Upload de layout visual próprio no construtor de documentos; categorias competência/curso no catálogo org (o CHECK já prevê).
- Desalinhamentos de housekeeping: `.env.example` incompleto; o CLAUDE.md aponta `.claude/skills/agente-governanca/SKILL.md`, que não existe no repo; arquivos soltos na raiz (`.bpm` de 15 MB, `prev_console.html`) a confirmar com o Xayer.

## Para ir além
- `CLAUDE.md` do repo; nota do vault `06-Agentes-e-Skills/agente-governanca.md`; blueprint em `00-Inbox`.
- ADRs citados no código e na história do módulo: 2026-06-13 (porta única WhatsApp), 2026-06-25 (corte à vista, gestor-comercial), 2026-08-23 (dimensões/medidas/ligações), 2026-08-29 (laboratório; realizado ligado na fonte), 2026-08-31-agente-governanca-estagio-e-uso-da-semente.
- O porquê detalhado de quase toda regra está nas docstrings dos módulos PUROS, em `scem.py`/`scem_perguntas.py` e nos comentários do `schema.sql`: ler antes de mudar.
