---
name: agente-comercio-revendas
description: Plataforma de comercialização das revendas parceiras da Sementes Maná LTDA — as revendas informam periodicamente o volume já comercializado dos produtos adquiridos, e a Maná acompanha a velocidade de comercialização. Flask + PostgreSQL (schema comercializacao) no Railway, integrado ao Simple Agro via SDK mana-simpleagro + cache via habilidade data-lake-pg, scaffold via novo-agente-mana. Reaproveita a UI do agente-estoque (tabela, filtros, drilldown, PDF) mas SEM produção/qualidade/estoque físico. Núcleo: Volume Adquirido (somado dos pedidos SA), Volume Comercializado (lançado manualmente via movimentos append-only), Volume Saldo. RBAC com 4 perfis (Admin Maná, Gestor Maná, Vendedor, Revenda), acesso resolvido SEMPRE por conjunto de cliente_sa (clientes_visiveis), trava de safra bloqueada, drilldown Variedade→Revenda/Vendedor→Pedidos SA, Controle de Usuários com vínculo de clientes por usuário, e auditoria obrigatória. Use SEMPRE que trabalhar com o agente-comercio-revendas — modelar banco, endpoints, sincronização SA, permissões, painel HTML, filtros (safra/vendedor/revenda/variedade), drilldown, edição de comercializado, controle de usuários, ou publicação no Railway. Também quando mencionar: comercialização de revendas, volume comercializado, volume adquirido, velocidade de venda da revenda, clientes_visiveis, trava de safra, lançamento de comercializado, painel de revendas Maná.
---

# Agente de Comércio de Revendas — Sementes Maná LTDA

Serviço web onde as **revendas parceiras** informam periodicamente o **volume já comercializado** dos produtos que adquiriram da Maná. O **Volume Adquirido** vem dos pedidos do Simple Agro; o **Volume Comercializado** é lançado manualmente. Objetivo nº 1 da Maná: medir a **velocidade de comercialização** das revendas (acompanhamento comercial, indicadores, gestão de estoque, decisão estratégica).

Para a revenda, a ferramenta é simples: informar e consultar **apenas os seus próprios dados**.

> **Status (2026-07-04):** EM PRODUÇÃO no Railway — `agente-comercial-revenda-production.up.railway.app`, `/health` verde (db=ok, sa=ok). Fase 1 (fundação/telas/RBAC) e Fase 2 (sync SA + adquirido + data lake) concluídas. Fase 3: edição inline do comercializado, cards totalizadores, drilldown de pedidos, e **visão Por Revenda** (admin/gestor) concluídos; **auto-recompute** do adquirido ao vincular cliente. SIAP somando em produção. Falta Fase 5 (indicadores de velocidade: bags/semana, projeção). Arquitetura em `referencia/arquitetura.md`; `referencia/prototipo.html` é referência visual.

## Estado implementado (2026-07-03)

### Integração Simple Agro + Data Lake (lake-first)
- Pedidos via SDK `mana-simpleagro` (`sa.orders.list(safra_id=...)`); safras via `sa.safras.listar()` (`/api/seasons`). Safra ativa = campo booleano `status=true` (não `deleted`).
- **Lake-first** com `mana-habilidade-data-lake-pg`: `sync.rodar_sync()` lê do lake (chave `sa_orders_<safra>`, TTL `LAKE_MAX_AGE_HORAS`=6h, advisory lock `LAKE_LOCK_ID`=720124) e só cai no SA ao vivo se o snapshot estiver vazio/velho. Fail-soft: sem a habilidade, busca direto no SA.
- **Botão "Atualizar Data Lake"** no painel → `POST /api/atualizar-data-lake` (`forcar_ao_vivo=True`): busca no SA e faz upsert do snapshot. Selo **"LAKE: dd/mm hh:mm"** mostra a idade do snapshot (via `sync.lake_status()`).
- Mapeamento de item confirmado: `cliente.{id,cpf_cnpj,nome}`, `itens[].{produto, quantidade, grupo_produto}` (produto ex.: `O790IPRO`, qtd em `quantidade`).

### Regra de status (o que soma no adquirido)
- Somam **INTEGRADO + AGUARDANDO FATURAMENTO** (decisão Dayan 2026-07-03). No SA, "Integrado" chega como `status_erp` **vazio** + booleano `status=true` — o sync mapeia esse caso para `INTEGRADO`. Os demais reais: `ERRO INTEGRACAO`, `FATURADO PARCIAL` (não somam por padrão).
- Configurável por env `STATUS_INCLUIDOS` (nomes separados por vírgula; `TODOS` conta tudo). O SA já exclui deletados/cancelados.

### RBAC N:N + telas
- `clientes_visiveis`: admin/gestor=todos; **revenda**=clientes da sua revenda; **vendedor**=clientes das **várias revendas** vinculadas a ele via tabela `usuario_revenda` (N:N) — vendedor acompanha múltiplas revendas.
- Telas (login obrigatório): **Comercialização** (seletor de safra ativa + filtro de revenda; com 1 revenda auto-seleciona e esconde "Todas"; cards totalizadores; drilldown com **Lançamentos de venda** + Pedidos SA), **Cadastro de Revendas** (CRUD), **Vincular Clientes** (atribui órfãos→revenda), **Controle de Usuários** (CRUD + reset senha + checklist de revendas p/ vendedor + **Simulador de conversa**).

### D1/D2/D3 — comercializado por LANÇAMENTO (2026-07-06)
- **Fim da edição direta do número.** O comercializado é **derivado** da soma dos lançamentos ATIVOS. Cada lançamento = uma venda: `variedade + quantidade(bags) + cliente(nome/CPF opcionais) + data`. Vai somando (não substitui um total global).
- **Quem lança:** revenda + admin/gestor/vendedor, no escopo (`revendas_visiveis`). Botão "＋ lançar" na célula do comercializado + modal.
- **Histórico/versionamento (D2):** editar cria nova versão ATIVA e marca a original `substituido` (rastreável via `original_id`/`substituido_por`); cancelar → `cancelado` + observação (não some). Só `status='ativo'` conta pro estoque. Tudo visível no drilldown.
- **Janela de edição (D3):** editar/cancelar liberado até a **data de corte**; depois só `admin_mana`. A data é **editável pelo admin no painel** (tabela `configuracoes` chave `edicao_limite`; `GET/PUT /api/config`), com env `EDICAO_LIMITE_DATA` (default 2026-07-30) só como valor inicial. `_pode_editar`/`_limite_edicao` usam o valor do banco. Corte final 30/08 ainda por implementar.
- **D4 — solicitar saldo (devolução) por WhatsApp** (`saldo.py`): admin/gestor dispara `POST /api/solicitar-saldo {safra_id,revenda_id,variedade_id,volume}` (botão WhatsApp na célula de Saldo) → tabela `solicitacao_saldo` + envia à revenda (contato) e aos vendedores vinculados. A revenda responde **ACEITO** (devolve → confirma + avisa o vendedor pra ajustar o pedido no SA) ou **ASSUMO** (assume a compra → registra). Roteado no `/webhook-retorno` (`saldo.tratar`, entre `conversa` e o coletor), match por últimos-8-dígitos. Resposta explícita gravada (status/resposta/timestamp) = documentação; **não muta o núcleo** (o vendedor altera o SA e o re-sync reflete). Lista em `GET /api/solicitacoes-saldo`.
- Tabela: `lancamento_comercializacao` + colunas `cliente_nome/cliente_cpf/data_venda/status/original_id/substituido_por` (`delta_bags` = qtd do lançamento). Endpoints: `POST /api/comercializacao/venda`, `PUT /api/comercializacao/venda/<id>`, `POST /api/comercializacao/venda/<id>/cancelar`, `GET /api/comercializacao/<variedade_id>/lancamentos`.
- **Toggle "Por Variedade" / "Por Revenda"** na Comercialização (só admin/gestor): a visão por revenda lista TODAS as revendas com total adquirido/comercializado/saldo + drilldown dos cultivares de cada uma. Endpoint `GET /api/comercializacao-revendas?safra_id=` (perfil admin/gestor), agrega de `adquirido_consolidado`.
- **Auto-recompute do adquirido:** ao atribuir/alterar a revenda de um cliente (`POST /api/clientes-sa/<id>/revenda`), o snapshot `adquirido_consolidado` é recomposto na hora via `sync.recompute_adquirido()` (só recompõe do cache local `pedidos_sa_cache` + vínculos atuais, NÃO busca o SA — rápido). Não precisa mais re-sincronizar depois de vincular.

### Robustez (padrões validados — incidentes 2026-07-03)
- **Pool Postgres** (`db.py`) com keepalives + `statement_timeout`/`idle_in_transaction_session_timeout` e devolução SEMPRE (`finally: rollback()+putconn()`) — vazamento de 8 conexões congela o app.
- **Sync em thread de segundo plano** com **guard de validade** `SYNC_GUARD_MAX_S`=600s (`api.py` `_disparar_sync`): flag sem validade trava o botão até redeploy; seta a flag antes de iniciar a thread.
- Diagnóstico via log `sync DIAG` (contagens/distribuição de status/amostra sem PII).

### Segurança (endurecimento 2026-07-04)
- **Todo endpoint de dados exige auth** (`login_obrigatorio`/`perfil_obrigatorio`); RBAC por `clientes_visiveis`; senha em **bcrypt**; SQL 100% parametrizado. As páginas HTML são só a casca — os dados só chegam via `fetch` autenticado (sem token → `/app` redireciona pro `/login`, API responde 401).
- **Cookie do token**: `HttpOnly` + `SameSite=Lax` + **`Secure`** (só HTTPS) + `max_age`=TTL. O token **não** volta mais no corpo do login (JS nunca toca no token). Em dev local (http), setar `COOKIE_SECURE=false`.
- **JWT_SECRET**: se rodar com auth ligada e sem `JWT_SECRET` próprio, o app **gera um segredo efêmero forte** no boot e loga `CRITICAL` — tokens forjados com o default não valem. **Defina `JWT_SECRET` fixo no Railway** (senão todo mundo desloga a cada deploy).
- **Headers** (`@app.after_request`): `Content-Security-Policy` travada (`default-src 'self'`, `connect-src 'self'`, `frame-ancestors 'none'`; scripts/fonts só dos CDNs conhecidos — tailwind/unpkg/cdnjs/google), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, `HSTS`, e **`Cache-Control: no-store`** nas rotas privadas e `/api/*` (não cacheia dado autenticado).
- **Anti-brute-force**: rate-limit em memória no `/api/auth/login` (`LOGIN_MAX_TENTATIVAS`=8 por `LOGIN_JANELA_SEG`=300s por IP; sucesso zera). Funciona com workers=1.
- **`debug` nunca liga em produção** (env `FLASK_DEBUG`, default false). **`AUTH_DESABILITADO` deve ser false/ausente no Railway** (era da Fase 1; se true, app fica SEM login — o boot loga aviso).

### Notificações WhatsApp — via habilidade mana-habilidade-notificacao-whatsapp (2026-07-06)
**Agente-comercio-revendas é o piloto consumidor** da habilidade Camada 2C. O agente **compõe** a regra de negócio; a habilidade dá as primitivas. Envio SEMPRE pela porta única do `agente-whatsapp` (a habilidade injeta classe+idempotency_key+agente). Sem LLM.

- **Primitivas consumidas** (`notif.py`): `ContatoDDL.init_schema` (cria `contatos_notificacao`/`envios_notificacao`/`jobs_notificacao` no schema `comercializacao`), `ContatoRepo` (CRUD de contatos), `WhatsAppSender` (`broadcast_text`/`send_text`), `NotificationScheduler` (cron APScheduler, tz America/Sao_Paulo). Import guardado (`_HAB_OK`) → app sobe fail-soft se o pacote faltar.
- **Cadastro de contatos** (tela **Notificações → aba Contatos**, admin/gestor): cada contato tem `tags` = `revenda`|`vendedor`|`grupo` e `metadata` com o vínculo (`revenda_id` / `usuario_id`). Endpoints `GET/POST /api/contatos`, `PUT /api/contatos/<id>`, `POST /api/contatos/<id>/ativo`, `DELETE /api/contatos/<id>`.
- **Conteúdo** (composto no agente): adquirido / comercializado / **saldo por variedade** da safra corrente. Revenda recebe o dela; vendedor recebe o **consolidado** das revendas vinculadas (via `usuario_revenda`); grupo recebe o resumo de todas. Fan-out de texto usa `broadcast_text` (template `{corpo}` + `variaveis_por_contato` por id) → `/send-whatsapp-lista` nativo.
- **Agendamentos editáveis** (aba Agendamentos): tabela do agente `agendamentos_notif` (`hora`, `dias_semana` `1..7`/`*`, `alvo` **GRUPO/INDIVIDUAL/AMBOS**, `safra_id`, `ativo`) = fonte de intenção. `notif.sync_scheduler()` converte cada agendamento ativo em job `ag-<id>` no `NotificationScheduler` (cron `min hora * * dow`) no startup e a cada CRUD. **"Disparar agora"** = `POST /api/agendamentos/<id>/testar` (forcar=True, sufixo de idempotência com timestamp pra permitir reteste).
- **Log de envios**: `GET /api/notif-log` lê `envios_notificacao` (tabela da habilidade). Dedup por `idempotency_key` determinístico (a habilidade cuida).
- **Envio individual sob demanda** (v0.2.0): `POST /api/notificar-contato` `{contato_id, mensagem?, anexo_base64?, anexo_tipo? (pdf/png/jpg/…), filename?, caption?}` → `WhatsAppSender.send_text`/`send_pdf`/`send_image`/`send_document` conforme o anexo (`notif.notificar_contato`). Botão ✈️ por contato na aba Contatos.
- **Jobs do scheduler**: `GET /api/jobs` (lista jobs vivos, inclui os `ag-<id>` dos agendamentos) e `DELETE /api/jobs/<jid>` (remove). Criar/editar broadcast agendado = aba **Agendamentos** (persiste em `agendamentos_notif` e registra no `NotificationScheduler`).
- **Coleta de respostas (item 4, LIGÁVEL)**: `RespostaColetor` v0.2.0 (match por últimos-8-dígitos). `POST /webhook-retorno` (fora do `/api`) segue o **contrato do agente-router**: body `{"phone","text":{"message"}}`, header `X-Router-Secret` (vs `ROUTER_SECRET`). Retornos: `match` → `200 {"status":"ok"}` (router para); sem match → `200 {"status":"ignored"}` (router segue); erro parse/banco → `500`; secret inválido → `401 {"erro":"unauthorized"}`. Nasce **desligado** por `AUTH_WEBHOOK_ATIVO=false` (aceita e ignora, 200 vazio) → ligar = setar `AUTH_WEBHOOK_ATIVO=true` + `ROUTER_SECRET` no Railway, sem downtime.
- **Diálogo de atualização (conversa.py, decisões Dayan 2026-07-06)**: a revenda atualiza o comercializado por WhatsApp num fluxo multi-turno (padrão TMS). Máquina de estados em `conversa_revenda` (match por últimos-8-dígitos): **MENU** (agente lista as variedades numeradas com adq/com/saldo) → **QTD** (revenda responde os bags) → **CONFIRMA** (agente pede SIM; ⚠ avisa se > adquirido) → grava e volta ao MENU; **FIM** encerra. Valor = **TOTAL vendido na safra** (vira lançamento com `comercializado_resultante=total`, `origem='whatsapp'`, autor = admin sistema) → **direto no painel**; também espelha no inbox `respostas_distribuidor` (aplicado=true). Início: `POST /api/iniciar-coleta {contato_id}` (botão 📋 no contato revenda) OU a própria revenda manda uma palavra-chave inequívoca (`atualizar`, `comercializado`, `atualizar vendas`… — genéricos como "oi"/"menu"/"opções" NÃO iniciam; caem na guia do `reclamar_cadastrado`). O `/webhook-retorno` roteia: conversa ativa → `conversa.tratar` → `saldo.tratar` → `notif.processar_retorno` (coleta de valor único) → **`conversa.reclamar_cadastrado` (claim-sempre, 2026-07-10)**: contato cadastrado com tag `revenda` que não caiu em nada acima recebe a guia ("digite *atualizar*", template editável `conversa_guia_nao_entendi`) e é RECLAMADO — revenda nunca vaza pro fluxo interno do router (menu URA/keywords/PA). No router, o claim deste agente roda ANTES do menu URA (follow-up ADR `2026-07-10-tms-claim-por-numero-antes-do-menu`, commit router `6473a5d`). Número não cadastrado segue `ignored` (router continua normal). **Envio no caminho do webhook via `notif.enviar_bg` (fire-and-forget, 2026-07-10)**: dispara `threading.Thread(daemon=True)` e retorna na hora pra NÃO estourar o timeout ~6s do router quando o hub WhatsApp está lento (senão o claim virava timeout → revenda vazava pro menu interno). `enviar_bg` é **capture-aware** (no simulador do painel cai pro síncrono e coleta no buffer thread-local — a thread nova não herda). Usado em `conversa._avancar` (todas as respostas), `conversa.reclamar_cadastrado` (a guia) e `saldo.tratar` (respostas + ajuste). **Claim rápido (2026-07-10)**: `saldo.tratar` decide o claim SÓ com o SELECT da solicitação pendente e responde `ok` na hora — TODO o resto (UPDATE, `_registrar_ajuste`, notificar vendedor, resposta no zap) roda em `_tratar_bg` numa `threading.Thread(daemon=True)` (sob captura/simulador roda síncrono via `notif.em_captura()`). Sem isso, o encadeamento de round-trips de DB + hub estourava o budget ~6s do router e o ACEITO/ASSUMO virava timeout → revenda vazava pro Plano de Ação. **Mesmo padrão em `conversa.tratar`**: decide o claim só com lookups rápidos (`_ativa` = conversa ativa? / palavra-chave + `_contato_revenda_por_tel` = revenda cadastrada?), responde `ok`, e roda `_avancar`/`_iniciar` (montar menu, queries adq/com/saldo, envio) em `_bg` (thread daemon; síncrono sob `notif.em_captura()`). **Regra do webhook: NENHUMA query pesada/rede antes de responder o claim.** Caminhos auditados: `conversa.tratar` (bg), `saldo.tratar` (bg), `reclamar_cadastrado` (1 SELECT + `enviar_bg`), `processar_retorno` (match do coletor + insert, sem hub). Disparo ATIVO (`solicitar`, `notificar_corte`, `notificar_ajuste`, agendador, `_iniciar`) segue **síncrono** via `notif.enviar`. **Idempotência por REQUISIÇÃO (ADR porta única, 2026-07-10)**: `notif.enviar` injeta uma `idempotency_key` ÚNICA por chamada (`req-<uuid4>` via kwarg detectado por introspecção — `idempotency_prefix`/`idempotency_key` do `send_text`), porque a chave default da habilidade é derivada do CONTEÚDO (`text:<hash>`) e a guia do `reclamar_cadastrado` (sempre igual) era deduplicada no hub (`dup=True`). Fluxos de retry deliberado (broadcast do agendador) mantêm prefixo próprio via `_sender` direto.
- **Callback de negócio** (`notif._processar_valor_recebido`): grava o valor no **inbox `respostas_distribuidor`** (contato/revenda/variedade/safra do `metadata` da coleta + valor + texto + `fora_faixa`). **NÃO muta adquirido/comercializado** (WhatsApp não escreve no núcleo; admin revê e aplica). Checa `faixa_min`/`faixa_max` do metadata → marca `fora_faixa` + loga. Gate por `r["novo"]` (idempotente em retry do router). Visível em `GET /api/respostas`. Par pra disparar a pergunta: `notif.solicitar_valor(contato_id, pergunta, tipo, metadata)` (metadata carrega revenda_id/variedade_id/safra_id/faixa_*).
- **Legado**: `whatsapp.py` e as colunas `whatsapp` em `revendas`/`usuarios` (da 1ª versão hand-rolled) ficaram **redundantes** — o cadastro canônico agora é `contatos_notificacao`. Podem ser removidos num limpa futuro.

### Env vars (Railway)
`DATABASE_URL`/`BANCO_MANA_URL`, `DB_SCHEMA`, `ADVISORY_LOCK_ID`, `LAKE_LOCK_ID`, `LAKE_MAX_AGE_HORAS`, `SA_BASE_URL`, `SA_USERNAME`, `SA_PASSWORD`, `SA_SAFRA_ID`, `SA_GRUPO_ID`, `JWT_SECRET` (**obrigatório fixar**), `JWT_TTL_HORAS`, `AUTH_DESABILITADO` (**manter false**), `COOKIE_SECURE`, `FLASK_DEBUG`, `LOGIN_MAX_TENTATIVAS`, `LOGIN_JANELA_SEG`, `STATUS_INCLUIDOS`, `SYNC_INTERVAL`, `AGENTE_WHATSAPP_URL`, `AGENTE_WHATSAPP_API_KEY`, `WHATSAPP_GRUPO_ID` (destino do alvo GRUPO), `NOTIF_ATIVO` (liga o scheduler), `NOTIF_TICK_SEG`, `BRT_OFFSET_HORAS`.

## Endossos → análise de crédito Maná (2026-07-10, construído pelo hub em variação D)

A revenda **endossa CPRs de produtores** pra Maná (grão como garantia) e cada endosso
vira uma **Solicitação de Crédito (CRE-001) no SoftExpert**. Aba "Endossos" na sidebar
(perfis revenda/admin/gestor; revenda vê só os seus).

**Fluxo:** revenda cadastra o produtor (nome, CPF/CNPJ, tipo, grupo econômico, contato,
UF/município) + sobe docs e a CPR endossada (PDF/JPG/PNG ≤ `ENDOSSO_MAX_DOC_MB`, docs em
BYTEA no `endosso_docs`, **zero LLM** — LGPD) → botão **"Enviar para Maná"** →
**thread background** (workers=1; guard por endosso com validade 600s):
`se_client.new_workflow` (ProcessID `SE_PROCESS_ID_ENDOSSO`=SM.CV.PR.NE.CRE-001, título
`ENDOSSO - {cliente} - {revenda}`, UserID `SE_USER_ID`) → **idprocess salvo imediatamente**
(amarração; retry não duplica processo) → `edit_form` (EntityID `scred`, 13 campos numa
chamada) → `anexar` × docs pendentes na **ATV-01** (1 arquivo/chamada, **sessão HTTP
persistente** — regra: manter a sessão do wsdl viva senão N anexos demoram) → status
`enviado` (ou `erro`+motivo; reenvio anexa só o que faltou via `anexado_se`).
**ATV-01 fica ABERTA** — análise segue com o time de crédito (sem executeActivity, sem
acompanhamento de status na v1). **Termo de anuência (2026-07-10):** slot dedicado no modal de docs (1 arquivo,
destaque âmbar, `tipo='termoanuencia'` no endosso_docs) → no envio vai pro **campo
ARQUIVO do scred** `SE_CAMPO_TERMO` (default `termoanuencia`) via `editEntityRecord`
com `EntityAttributeFileList/EntityAttributeFile {EntityAttributeID, FileName,
FileContent(base64)}` (referência wf-ws + orientação especialista SE). Demais docs
seguem pra ATV-01 via newAttachment. Enviar sem termo avisa mas não bloqueia.
Indicador 📜 na lista (`tem_termo`). Termo já enviado não pode ser substituído pelo painel.
**Excluir (decisão Xayer 2026-07-10):** exclui local SEMPRE (hard delete);
se houver processo no SE, tenta `cancelWorkflow` lá (best-effort — WS não exclui,
cancela); SE recusou/indisponível → exclui local mesmo assim e avisa pra cancelar
manualmente no SE. Auditoria local registra idprocess + resultado. Campo `cliente` (Novo|Base) editável na
tela desde 2026-07-10 (`cliente_opcao`).

**Mapeamento scred:** nomeclientenovo=nome · cliente=**"Novo"** (fixo) · tipocliente/
tipodecliente=Pessoa Física|Jurídica (espelho opção/persistência) · grupeconom=Sim|Não ·
usosemente/usodasemente=**"Agricultor Endossado"** (fixo, espelho) · nomedistribuidor=
**revenda logada** (auto) · cpfcnpj/email/telefonecliente/uf/municipio=form.

**Arquivos:** `se_client.py` (desde 2026-07-10: adaptador fino sobre o **SDK
`mana-softexpert` v0.1.0** — este agente é o 1º consumidor real do SDK, gate beta;
o SOAP inline original foi extraído pro SDK) · `endossos.py` (negócio + envio
background) · endpoints `/api/endossos*` em api.py · `templates/endossos.html`.
**Env novas:** `SE_URL`, `SE_API_KEY` (mesmas dos outros agentes), `SE_ENTITY_ID=scred`,
`SE_PROCESS_ID_ENDOSSO`, `SE_ACTIVITY_ID_ENDOSSO=ATV-01`, `SE_USER_ID`,
`ENDOSSO_MAX_DOC_MB`. Sem elas o app sobe normal e o envio responde "integração não
configurada" (fail-soft).

## Performance (fixes 2026-07-11)
Gunicorn **1 worker gthread + 8 threads** (estado em memória preservado — guard/sync/
scheduler — mas sem fila única; candidato a padrão do scaffold). RBAC com **cache por
request** (flask.g — clientes/revendas_visiveis 1× por requisição). `/api/data-lake-status`
lê só chave+timestamp (sem `octet_length` — que serializava MBs de JSONB por load).
Badge de notificações: 5min + só consulta se o perfil tem badge. Contexto: banco-mana é
REMOTO (outro projeto Railway, ~20-60ms/query) — disciplina de roundtrips importa.

## Fora de escopo
Produção, qualidade, classificação, laudos, informações agronômicas e estoque físico **não existem** aqui. É exclusivamente acompanhamento de comercialização (+ endossos acima).

## Stack e localização (a provisionar)
- **Repo:** `Sementesmana/agente-comercio-revendas` (GitHub) — a criar.
- **Scaffold:** skill `novo-agente-mana` (Flask + Jinja2 + HTMX + Alpine.js + PostgreSQL + Railway + **JWT** + identidade visual Maná). Não escrever boilerplate à mão.
- **Stack:** Flask + `psycopg2` + `gunicorn`, PostgreSQL (banco-mana, **schema `comercializacao`**), Railway.
- **Design:** padrão Maná (skill `mana-design-system`) — Tailwind + Plus Jakarta Sans + Font Awesome 6, esmeralda/azul/âmbar, tipografia compacta MAIÚSCULA, cards arredondados, drilldown inline, PDF reportlab paisagem.
- **Simple Agro:** SDK `mana-simpleagro` (`pip install "git+https://github.com/Sementesmana/mana-simpleagro.git@v0.1.1"`) — login OAuth + auto-relogin, leitura de orders/clients. Substitui a cópia do `SimpleAgroClient`.
- **Cache da fonte lenta:** habilidade `mana-habilidade-data-lake-pg` (`pip install "git+https://github.com/Sementesmana/mana-habilidade-data-lake-pg.git@v0.1.0"`) — `read_or_compute`/`upsert` + advisory_lock para `pedidos_sa_cache` e `adquirido_consolidado`.
- **Qualidade/segurança:** skill `akita` como referência de teste (defense-in-depth, idempotência) — sustenta o teste de vazamento de escopo do RBAC.

## Reaproveitamento (skills instaladas + agente-estoque)
Compor com as skills instaladas — **ler o SKILL.md canônico de cada uma e escrever código novo usando a API** (nunca copiar exemplo):
- **`novo-agente-mana`** → scaffold Flask/PG/Railway/JWT + visual Maná.
- **`mana-simpleagro`** (SDK) → leitura de pedidos do SA no job de sync (substitui `SimpleAgroClient` copiado).
- **`mana-habilidade-data-lake-pg`** → cache durável de `pedidos_sa_cache` e recomputo de `adquirido_consolidado`.
- **`mana-design-system`** → UI, drilldown, KPIs, PDF.

Do **agente-estoque** ficam como referência de UI/lógica (a re-implementar no padrão acima, não copiar): componentes de tabela com filtro por coluna, dropdown de checkboxes, drilldown inline, `STATUS_INCLUIDOS`, amarração por `nome_norm`.

**Construir do zero (nenhuma skill entrega pronto):** RBAC dos 4 perfis + `clientes_visiveis`, auditoria e trava de safra — o `novo-agente-mana` dá só o esqueleto JWT; a lógica de perfis e o **teste de vazamento de escopo** são compostos, usando `akita` como guia.

> **Não se aplica a este artefato:** skills de SoftExpert (`se-dataset-reader`, `softexpert-dataset-integration`, `softexpert-wf-ws`) — a fonte é o Simple Agro, não o SE. Sem LLM e sem WhatsApp neste v1, então `mana-arquitetura-padrao` entra só como governança e o `mana-llm-gateway`/`agente-whatsapp` não são usados.

---

## Decisões de arquitetura (ADR resumido)
- **D1** Revenda = agrupamento de 1+ códigos-cliente do SA; o admin atribui cada `cliente_sa` a uma revenda.
- **D2** Produto = Variedade = Cultivar (uma entidade só).
- **D3** Grão único de negócio: `(safra × revenda × variedade)` — idêntico ao Nível 2 do drilldown e ao grão de edição.
- **D4** Comercializado por **movimentos append-only** (`lancamento_comercializacao`); total = soma derivada (habilita velocidade/projeção e auditoria nativa).
- **D5** Adquirido persistido em snapshot recomputado pelo sync; nunca editado por humano.
- **D6** Acesso resolvido SEMPRE para um conjunto de `cliente_sa_id` (`clientes_visiveis`). Vendedor/Maná traduzem revenda→clientes. **Nunca** filtrar por revenda diretamente.
- **D7** Login e-mail + senha com hash (bcrypt/argon2). Reset conduzido pela Maná.
- **D8** Safra é filtro de página **com trava**: safra bloqueada no SA → todos os perfis só visualizam.
- **D9** Vínculo de clientes é por usuário (lista de `cliente_sa` marcada no cadastro do usuário).

## Modelo de dados (schema `comercializacao`)
Tabelas (DDL completo comentado em `referencia/arquitetura.md`):
`usuarios` (id, nome, email UNIQUE, senha_hash, perfil[admin_mana|gestor_mana|vendedor|revenda], status, vendedor_sa_id, ultimo_acesso) ·
`vendedores` (id, codigo_sa, nome, status) ·
`revendas` (id, razao_social, nome_fantasia, cnpj, vendedor_responsavel_id, status) ·
`clientes_sa` (id, codigo_sa UNIQUE, nome, revenda_id, status) ·
`usuario_cliente_sa` (usuario_id, cliente_sa_id, criado_por, data_criacao) — vínculo de acesso ·
`safras` (id, codigo_sa, descricao, status[aberta|bloqueada], ativo) ·
`variedades` (id, nome, nome_norm UNIQUE, ativo) ·
`adquirido_consolidado` (safra_id, revenda_id, variedade_id, volume_adquirido_bags, qtd_pedidos, atualizado_em) UNIQUE(safra,revenda,variedade) ·
`lancamento_comercializacao` (safra_id, revenda_id, variedade_id, delta_bags, comercializado_resultante, usuario_id, perfil, origem, observacao, data_hora) ·
`pedidos_sa_cache` (id_sa, numero, data_pedido, cliente_sa_id, variedade_id, qtd_bags, safra_id, status, atualizado_em) ·
`auditoria` (entidade, entidade_id, acao, usuario_id, nome_usuario, perfil, payload_anterior JSONB, payload_novo JSONB, observacao, ip, data_hora).

## Regras de cálculo
```
comercializado(safra,revenda,variedade) = SUM(lancamento.delta_bags)
saldo = adquirido_consolidado - comercializado
```
**Invariante:** `comercializado ≤ adquirido` (validada no lançamento; delta que estouraria é rejeitado).
**Adquirido < comercializado** (pedido cancelado): sinaliza alerta e bloqueia lançamento positivo; nada é apagado.
**Status SA incluídos:** `{"aguardando aprovacao","integrado","aprovado"}` (lista de inclusão, normalizada NFD).

## RBAC — primitivo único
```
clientes_visiveis(usuario) -> set[cliente_sa_id]
  admin_mana / gestor_mana → todos
  revenda                  → usuario_cliente_sa do usuário
  vendedor                 → clientes_sa de revendas onde vendedor_responsavel_id = usuario.vendedor_sa_id
```
Aplicado numa **camada de repositório** (não espalhado por endpoint), com **teste de regressão de vazamento de escopo** obrigatório.

| Capacidade | Admin | Gestor | Vendedor | Revenda |
|---|:--:|:--:|:--:|:--:|
| Ver dados | tudo | tudo | suas revendas | seus clientes |
| Editar comercializado | ✅ qualquer | ✅ qualquer | ✅ suas | ✅ seus |
| Criar/editar/ativar usuários | ✅ | ✅ | ❌ | ❌ |
| Resetar senha | ✅ | ❌ | ❌ | ❌ |
| Vincular cliente↔usuário/revenda | ✅ | ✅ | ❌ | ❌ |
| Relatórios PDF | ✅ | ✅ | ✅ suas | ✅ seus |
| Controle de Usuários | ✅ | ✅ | ❌ | ❌ |

Lançar em safra **bloqueada** é negado para todos.

## Filtros do painel
Safra (default = aberta corrente; trava read-only se bloqueada) · **Vendedor** (Maná/Vendedor; oculto p/ Revenda; cascateia a Revenda) · Revenda (Maná/Vendedor) · Variedade · busca textual. Nas listas de clientes do Controle de Usuários há busca por código/nome.

## Drilldown (idêntico ao agente-estoque)
- **Nível 1 — Variedade:** Variedade · Adquirido · Comercializado · Saldo (lápis na própria linha quando há 1 só revenda no escopo).
- **Nível 2 — Revenda/Vendedor:** + Data e Usuário da última atualização. **Edição do comercializado acontece aqui** (grava delta, recalcula saldo, gera log).
- **Nível 3 — Pedidos SA:** Nº, Data, Cliente, Qtd, Safra, Status (read-only, rastreabilidade).

## Controle de Usuários
Tela admin: lista (perfil, escopo, status), CRUD, ativar/inativar, reset senha, e **edição dos clientes SA vistos por usuário** (checklist com busca, atalho na linha). Toda ação gera registro em `auditoria`.

## APIs (todas escopadas por `clientes_visiveis`)
`POST /api/auth/login` · `GET /api/comercializacao` (N1) · `…/{variedade}/revendas` (N2) · `…/{variedade}/{revenda}/pedidos` (N3) · `POST /api/comercializacao/lancamento` (valida invariante + trava de safra + log) · `GET /api/relatorio.pdf` · CRUD `/api/usuarios[...]` · `POST /api/usuarios/{id}/clientes` · `POST /api/sync/run` · `GET /api/auditoria` · `GET /health`.

## Sincronização Simple Agro
Job agendado (APScheduler) usando o SDK `mana-simpleagro` para ler os pedidos e a habilidade `data-lake-pg` para persistir/cachear: busca pedidos por safra/grupo (`sa.orders...`) → `lake.upsert("pedidos_sa_cache", ...)` → recomputa `adquirido_consolidado` por `(safra,revenda,variedade)` somando clientes de cada revenda, com `STATUS_INCLUIDOS` e `nome_norm` → atualiza `safras.status` → verifica invariante. **O job só toca o adquirido; jamais um lançamento.** Cliente SA sem revenda atribuída (`revenda_id NULL`) fica invisível até o admin atribuir.

## Variáveis de ambiente (Railway)
| Var | Descrição |
|---|---|
| `DATABASE_URL` / `BANCO_MANA_URL` | PostgreSQL (Railway / banco-mana compartilhado, schema `comercializacao`) — usado pela habilidade `data-lake-pg` |
| `SA_BASE_URL` | `https://sementesmana.api.simpleagro.com.br:3333` (lido pelo SDK `mana-simpleagro`) |
| `SA_USERNAME`, `SA_PASSWORD` | Credenciais SA (lidas pelo SDK) |
| `SA_SAFRA_ID`, `SA_GRUPO_ID` | Safra/grupo (soja) — env vars do SDK |
| `JWT_SECRET` | Sessão/token do painel |
| `SYNC_INTERVAL` | Intervalo do job (s) |

## Roadmap
1. Fundação: schema + auth/RBAC + `clientes_visiveis` + teste de vazamento.
2. Sync: job SA, `adquirido_consolidado`, `pedidos_sa_cache`, trava de safra.
3. Núcleo: drilldown 3 níveis + lançamento com invariante + auditoria.
4. Maná: Controle de Usuários, vínculo de clientes, PDF, dashboard de velocidade.
5. Indicadores: ritmo (bags/semana), projeção de esgotamento, comparativo entre revendas.

## Checklist de publicação
1. Criar repo `Sementesmana/agente-comercio-revendas` (Procfile + railway.toml + requirements).
2. Provisionar PostgreSQL e criar schema `comercializacao` (DDL de `referencia/arquitetura.md`).
3. Configurar variáveis de ambiente acima no Railway.
4. Rodar bootstrap idempotente (cria tabelas + seeds de safras/vendedores).
5. Primeira sincronização (`POST /api/sync/run`); atribuir clientes SA órfãos às revendas.
6. Criar usuário Admin Maná; cadastrar vendedores, revendas e usuários Revenda (com clientes vinculados).
7. Smoke test: login por perfil, drilldown 3 níveis, lançamento (invariante + trava de safra), PDF, `GET /health` (status=ok, db=ok).
8. Versão visível no topo/rodapé (semver) e validação de vazamento de escopo.

## Arquivos de referência (neste pacote)
- `referencia/arquitetura.md` — documento de arquitetura completo (ADR + schema SQL comentado + APIs + sync + riscos).
- `referencia/prototipo.html` — protótipo navegável (single-file, dados fictícios): drilldown, edição com invariante, trava de safra, RBAC por troca de usuário, Controle de Usuários com vínculo/busca de clientes, filtros (safra/vendedor/revenda/variedade).

## Skills relacionadas
- **`novo-agente-mana`** — scaffold Flask/PG/Railway/JWT + visual Maná.
- **`mana-simpleagro`** (SDK) — leitura de pedidos/clientes do Simple Agro (substitui o `SimpleAgroClient` copiado).
- **`mana-habilidade-data-lake-pg`** — cache durável de `pedidos_sa_cache` + recomputo de `adquirido_consolidado`.
- **`mana-design-system`** — UI, drilldown, KPIs, PDF.
- **`akita`** — referência de segurança/testes (sustenta o teste de vazamento de escopo do RBAC).
- **`mana-arquitetura-padrao`** — governança (aplicável se um dia entrar LLM/WhatsApp).
- **`agente-estoque`** — referência de UI/lógica (tabela, drilldown, `STATUS_INCLUIDOS`, `nome_norm`) a re-implementar, não copiar.
- **Não se aplica:** `se-dataset-reader`, `softexpert-dataset-integration`, `softexpert-wf-ws` (fonte é o Simple Agro, não o SoftExpert).

> **Última atualização 2026-07-20 (Dayan — teste sync marketplace):**
> verificando propagação automática do plugin no Cowork do Xayer.
