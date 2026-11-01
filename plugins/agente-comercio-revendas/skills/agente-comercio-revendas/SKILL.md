---
name: agente-comercio-revendas
description: "Mapa do agente-comercio-revendas (Sementes Maná), Flask+PG (schema comercializacao)+Railway: revendas parceiras informam o volume comercializado do que adquiriram (adquirido vem dos pedidos do Simple Agro) para medir velocidade de venda; mais endossos de CPR que viram CRE-001 no SoftExpert, Gestão de Cargas e notificações WhatsApp. Traz decisões, armadilhas e contratos que o código não diz. Use SEMPRE no agente-comercio-revendas ou ao citar comercialização de revendas, volume comercializado/adquirido, clientes_visiveis, trava de safra, data de corte, endosso, termo de anuência, devolutiva de crédito, Gestão de Cargas, sugestão de carga."
---

# agente-comercio-revendas — mapa

## O que é
- Plataforma onde as **revendas parceiras** informam o que já venderam do que compraram da Maná. Adquirido = pedidos do Simple Agro; Comercializado = lançamentos manuais (painel ou WhatsApp); Saldo = diferença. Objetivo nº 1: **velocidade de comercialização** por revenda. Fora de escopo: produção, qualidade, laudo, estoque físico.
- Módulos que cresceram depois: **Endossos** (revenda endossa CPR de produtor → Solicitação de Crédito CRE-001 no SE), **Gestão de Cargas** (carteira faturado/agendado/a agendar) + **Sugestão de carga**, **Notificações/diálogo WhatsApp** (piloto da habilidade notificacao-whatsapp).
- Repo `Sementesmana/agente-comercio-revendas`. Dono: **Dayan** (decide); Xayer/hub revisa. Produção: https://agente-comercial-revenda-production.up.railway.app (o nome do serviço é "comercial-revenda", não "comercio-revendas").
- Banco-mana (REMOTO, outro projeto Railway, ~20-60 ms/query), schema `comercializacao`, criado no boot por `sql/schema.sql`.

## Onde está a verdade
- `config.py` — todas as envs com o porquê (embed SE, status que somam, SE_USER_ID). `VERSAO` é a versão exibida.
- `sql/schema.sql` — banco + migrações idempotentes (ALTER ... IF NOT EXISTS).
- `rbac.py` — primitivo único de acesso. `auth.py` — JWT em cookie, bcrypt, decorators de perfil.
- `sync.py` — leitura SA lake-first + recompute do adquirido. `api.py` — todas as rotas `/api/*` (inclui endossos, devolutiva, tipos de crédito, relatórios).
- `notif.py` (primitivas da habilidade + envio) · `conversa.py` (diálogo menu→qtd→confirma) · `saldo.py` (solicitação de saldo ACEITO/ASSUMO + corte e lembretes).
- `endossos.py` + `se_client.py` (adaptador sobre o SDK `mana-softexpert`) · `INTEGRACAO-SOFTEXPERT.md` (doc viva da integração SE — mais detalhada que esta skill).
- `cargas.py` (carteira) · `sugestao_carga.py`. ⚠ A docstring do topo de `cargas.py` diz que NF vem do `orders-scheduling`: está DEFASADA — o código lê NF/carga do `charge-montage` (ver armadilhas); e o "só APROVADOS" da mesma docstring também: valem os 3 de `_STATUS_OK`.
- `app.py` — headers de segurança, `/health`, `/webhook-retorno` (ordem de roteamento), seed do admin.
- `referencia/arquitetura.md` (ADR original + DDL comentado) e `referencia/prototipo.html` (protótipo visual) — são da Fase 1; úteis para o porquê, não para o estado atual.

## Regras e decisões que o código não explica sozinho

### Núcleo (ADR D1-D9)
- Grão único `(safra × revenda × variedade)`. Revenda = grupo de 1+ clientes SA (`clientes_sa.revenda_id`); cliente novo entra órfão e fica invisível até o admin vincular. Produto = variedade = cultivar (amarração por `nome_norm`).
- **Acesso SEMPRE por conjunto de cliente_sa** (`clientes_visiveis`/`revendas_visiveis`, cache por request em `flask.g`). Nunca filtrar por `revenda_id` direto. Vínculo canônico é N:N `usuario_revenda` (vendedor acompanha várias revendas); sem linha ali, `rbac` cai no LEGADO (revenda → `usuarios.revenda_id`; vendedor → `revendas.vendedor_responsavel_id = usuarios.vendedor_sa_id`); sem nenhum vínculo = tela vazia, sem erro. Código novo não lê `revenda_id` do JWT (o `PUT /api/usuarios` o zera — causou revenda não identificada nos endossos, fix v0.1.3); colunas legadas só saem depois de migrar todos para `usuario_revenda`.
- Perfis: admin_mana e gestor_mana fazem CRUD de usuários, revendas e vínculos; reset de senha SÓ admin_mana (D7).
- Adquirido = snapshot recomputado pelo sync, **nunca editado por humano**; o sync jamais toca lançamento. Vincular cliente a revenda recompõe o adquirido na hora a partir do cache local (sem ir ao SA).
- Comercializado = soma dos lançamentos `status='ativo'`. Cada lançamento é uma venda (variedade, bags, cliente opcional, data). Editar cria versão nova e marca a antiga `substituido`; cancelar = `cancelado` com observação. Nada some.
- Invariante: comercializado ≤ adquirido (venda que estoura é recusada com o saldo disponível). Revenda inativa não recebe lançamento. Safra `bloqueada` é só leitura para todos.
- Só aparecem variedades com movimento no escopo.
- **Status que somam no adquirido** (fix 2026-08-20, pedido Dayan): campo `status_pedido` (situação do PEDIDO), default AGUARDANDO APROVACAO + INTEGRADO + APROVADO + REPROVADO, mesmo critério do agente-estoque + REPROVADO. NÃO usar `status_erp` (é a integração com o ERP) — era a causa da SIAP não bater. Booleano `status=true` sem texto = INTEGRADO. Env `STATUS_INCLUIDOS` sobrescreve (`TODOS` conta tudo).
- Pedido/item com `deleted=true` não conta, e linha do cache que não reaparece na leitura do SA é podada antes do recompute (pedido fantasma NEO680IPRO, SIAP/DUQUIMA).
- Safra ativa no SA = booleano `status=true` (não `deleted`).

### Data de corte (D3)
- Até a data de corte revenda/vendedor/gestor editam e cancelam; depois só `admin_mana`. Data editável no painel (config `edicao_limite`); env `EDICAO_LIMITE_DATA` só vale enquanto não houver linha salva.
- **Corte desativável**: salvar a data VAZIA desliga trava, lembretes e aviso. Campo vazio sem salvar não desativa (vale o default do env e as notificações disparam).
- Lembretes D-N (config `corte_lembretes`, default 7,3) são só aviso; no dia sai `msg_corte` com CONFIRMO + coleta. Comercializado listado vira compromisso; o bloco de saldo lista só produtos com saldo > 0.
- Aviso e lembretes saem UMA vez (flags `corte_notificado`/`corte_lembretes_enviados` em `configuracoes`). Para reenviar depois de teste: `POST /api/limpar-respostas` (admin), que apaga as flags.

### WhatsApp (revenda conversa com o agente)
- Envio só pela porta única do hub `agente-whatsapp` via habilidade (classe + idempotency_key + agente). Sem LLM neste agente.
- `notif.enviar` injeta `idempotency_key` ÚNICA por requisição (`req-<uuid>`): a chave default da habilidade é por conteúdo e o hub deduplicava a guia (sempre igual). Broadcast agendado mantém prefixo próprio (retry deliberado).
- Resposta da revenda ao diálogo vira lançamento direto no painel (`origem='whatsapp'`, valor = TOTAL vendido na safra). Já a coleta de valor único e o ACEITO/ASSUMO da solicitação de saldo **não mutam o núcleo**: vão para inbox/registro e o vendedor ajusta o pedido no SA.
- Só palavra-chave inequívoca (atualizar, comercializado...) inicia o diálogo; oi/menu não.

### Endossos → CRE-001 (decisões Xayer)
- Fluxo de aprovação (2026-08-04): revenda monta (rascunho) → envia ao Administrador → admin/gestor devolve para ajuste com observação obrigatória OU **só `admin_mana`** envia ao SoftExpert. Revenda só edita em rascunho/ajuste; após `aceita` só lê.
- Zero LLM nos documentos (LGPD); docs em BYTEA no banco. Cada demais documento é marcado com um tipo de crédito (bandeirinha, catálogo em `/credito`, só admin gerencia).
- Envio = UMA chamada `newWorkflowEditData` (instancia + 13 campos do `scred` + termo de anuência no campo ARQUIVO) e grava o `idprocess` na hora (âncora anti-duplicação: retry pula a criação); depois `newAttachment` de cada doc na ATV-01 (CPR inclusive, como doc comum), mesma sessão HTTP do wsdl (reabrir custa segundos por anexo). Não para no primeiro anexo recusado: endosso fica `erro` com os nomes, reenvio sobe só os pendentes. Falta de documento nunca vira sucesso silencioso.
- Campos fixos: `cliente` Novo|Base (editável), `usosemente`=Agricultor Endossado, `nomedistribuidor`=revenda logada; pares opção/persistência recebem o mesmo valor.
- ATV-01 fica ABERTA (sem executeActivity, sem leitura de status do SE na v1). Pendência cai em `SE_USER_ID` (Lorena Martins desde 2026-08-27): a ATV-01 não é modelada para equipe e nenhum método do `wf_ws` aceita equipe. Trocar = mudar a env; a pessoa precisa poder INSTANCIAR o CRE-001.
- Desfazer: **Cancelar envio SE** (admin) preserva endosso/conversa/docs e só rebobina se o SE confirmar (503/502 = nada muda; `?forcar=1` com 2ª confirmação para processo já cancelado/excluído à mão). **Lixeira** = hard delete local sempre, cancelamento no SE best-effort.
- **Devolutiva de crédito** (2026-08-30, revista 2026-09-15): o painel de crédito (agente-pedidos) grava só a decisão; aqui o Administrador escreve a mensagem e publica para a revenda (um humano em cada ponta). Aprovado/reprovado NÃO são terminais: o comitê reativa o CRE no SE e redecide; pendência é por decisão diferente da última publicada.

### Cargas
- Três baldes somam 100% da carteira: **Faturado** (agendamento com NF), **Agendado** (data sem NF, mesmo com carga montada — regra do dono: entregue = transferido = faturado), **A agendar** (usa SALDO A AGENDAR, nunca a qtd do pedido). Carga é chip, não balde. Só pedidos APROVADO/AGUARDANDO APROVACAO/INTEGRADO (critério diferente do adquirido).
- Tratamento (TSI) faz parte da identidade da linha: mesma cultivar em vários tratamentos é outro produto a carregar.
- Sugestão de carga é GERENCIAL: não abate saldo, não vai ao SA, não gera nota; é recado da revenda à logística. Ordem de embarque é o coração (renumerada 1..N; mesma cultivar pode repetir em ordens diferentes), espelha a planilha ORDEM PARA CARREGAMENTO.

### Segurança
- Login obrigatório; token em cookie HttpOnly (nunca no corpo). `JWT_SECRET` fixo no Railway, senão o app gera segredo efêmero e todo mundo desloga a cada deploy. `AUTH_DESABILITADO` nunca true em produção.
- **Embed no SE** (`SE_EMBED_ORIGIN`, decisão Xayer 2026-08-03): com a env, X-Frame-Options e frame-ancestors somem POR COMPLETO e o cookie vira SameSite=None. Motivo: o validador do widget Página WEB do SE recusa qualquer restrição de frame (nem lê allowlist). Trade-off de clickjacking aceito; remover a env restaura a proteção. Exige https e `COOKIE_SECURE=true` (falha no boot se não).

## Armadilhas conhecidas (sintoma → causa → o que fazer)
- Botão de sync travado até redeploy → flag sem validade → guard de 600 s, setado antes de iniciar a thread (mesmo padrão no envio de endosso).
- App congela → vazamento de conexões → pool com keepalives/timeouts e `finally: rollback()+putconn()` sempre.
- Revenda cai no menu interno do router (URA/Plano de Ação) → claim estourou o budget ~6 s do router → NENHUMA query pesada ou rede antes de responder o claim; trabalho em thread daemon (`enviar_bg`, `_bg`, `_tratar_bg`), síncrono só sob o simulador (`em_captura`). Contato com tag revenda sem match recebe a guia e é reclamado.
- `code=-9 workflow não encontrado` com processo existente → `editEntityRecord` não tem UserID e age como dono do `SE_API_KEY` → usar `newWorkflowEditData` (SDK v0.2.0). Termo não entra depois de criado: Cancelar envio SE e reenviar. Órfão real: CRE-001-000196.
- `code=-5` → quem está no `SE_USER_ID` não pode instanciar o CRE-001 (lista escopada por permissão).
- `code=-23` no `newAttachment` → nome com acentos (ç+õ) → `nome_seguro` tira só o acento; nome original vai no Summary.
- Devolutiva nunca aparece → formatos de idprocess diferentes (`000216` × `CRE-001-000216`) → casa por sufixo de dígitos (mín. 4); não trocar por igualdade.
- Faturado = 0 com SA normal → NF/carga não existem no `orders-scheduling` → vêm do `/api/charge-montage`, chave `id_agrupamento + variedade` (agrupamento sozinho é a ENTREGA e cobre várias variedades). Se a carga cair, `faturado_indisponivel` e faixa amarela, nunca zero.
- Carteira zerada (itens=0) → SA manda `itens` como lista, dict único ou dict de dicts → sempre `_itens()` (mesmo tombo do agente-tms).
- Saldo a agendar zerado → campo mudou de nome → busca em profundidade com fallback marcado `fallback:quantidade`; o SA não tem linha de não agendado com saldo zero.
- Tela vazia que não volta → cache vazio do lake vale até o TTL (30 min) → `?live=1`; `_diag` mostra o funil para perfil Maná.
- Validação SIAP 26/27: pedido 260000010055/1, O760CE, agendado 28/09/2026, 1 bag, sem carga/NF → tem que cair em Agendado.
- `/api/data-lake-status` lento → não usar `octet_length` (serializa MBs de JSONB).

## Contratos externos
- **Simple Agro**: só via SDK `mana-simpleagro` (`orders.list`, `safras.listar`), nunca `sa_client.py` copiado. Lake-first via `mana-habilidade-data-lake-pg` (chave por safra, advisory lock próprio distinto do do schema). Cargas leem `/api/orders-scheduling` (`nao_agendado` true/false) e `/api/charge-montage`.
- **SoftExpert**: escrita via SDK `mana-softexpert` (tag fixada no requirements), processo `SM.CV.PR.NE.CRE-001`, entidade `scred`, ATV-01. Mesmos `SE_URL/SE_API_KEY` dos outros agentes. Sem config o envio responde integração não configurada (fail-soft). Leitura futura de status: Conjunto de Dados (se-dataset-reader), não `getWorkflow` em loop.
- **agente-pedidos**: lê `agente_pedidos.devolutiva_endosso` (outro schema, mesmo banco) — fail-soft se a tabela não existir.
- **agente-router**: `POST /webhook-retorno` com `{phone, text:{message}}` + header `X-Router-Secret`; `ok` = router para, `ignored` = segue, 401/500. Nasce desligado (`AUTH_WEBHOOK_ATIVO=false`, responde 200 vazio). O claim deste agente roda ANTES do menu URA no router.
- **Hub agente-whatsapp**: via habilidade `mana-habilidade-notificacao-whatsapp` (contatos com tags revenda/vendedor/grupo); destino do alvo GRUPO em `WHATSAPP_GRUPO_ID`.
- Sem LLM: não usa `mana-llm-gateway`.

## Como testar e subir
- Regras do CLAUDE.md: o sandbox não autentica no git — Claude valida (py_compile + smoke) e entrega UM comando (`./deploy.sh "msg"`) para o Dayan rodar; 1 motorista por vez; nunca `railway up`.
- `pytest tests/` roda sem banco (boot tolerante). Deploy = git push → Railway (~2 min) → `/health` com db=ok, sa=ok + log + teste no painel.
- Gunicorn 1 worker gthread 8 threads de propósito: guards, sync, scheduler e rate-limit do login (8 tentativas/300 s por IP) vivem em memória. Não subir workers.
- Diagnóstico por linhas DIAG no log (`sync DIAG`, `cargas DIAG campos`), sem PII. Simulador de conversa no Controle de Usuários testa o diálogo sem WhatsApp.
- Mudou comportamento/endpoint/env/integração → atualizar o SKILL.md no mesmo push; decisão grande → avisar o hub (ADR no ManaVault).

## Pendências
- Fase 5: indicadores de velocidade (bags/semana, projeção de esgotamento, comparativo entre revendas).
- Nada marca safra como `bloqueada` (sync só cria `aberta`): a trava existe mas não é acionada.
- `SYNC_INTERVAL`/`SYNC_AO_INICIAR` existem no config mas não há job periódico do SA: sync só pelo botão.
- Teste de vazamento de escopo do RBAC (exigido pelo ADR) não existe; `tests/` só tem smoke. `test_login_page_200` espera 200 em `/`, que hoje redireciona (302).
- `POST /api/comercializacao/lancamento` (Fase 1) soma sem filtrar `status='ativo'` e não é usado pelas telas: candidato a remoção.
- Endossos: sem acompanhamento de status do SE; colunas legadas `whatsapp` em revendas/usuarios e `usuarios.revenda_id` a limpar.
- `.env.example` e README desatualizados (só a Fase 1); CLAUDE.md ainda cita status INTEGRADO + AGUARDANDO FATURAMENTO.

## Para ir além
- `CLAUDE.md` do repo; `INTEGRACAO-SOFTEXPERT.md`; `referencia/arquitetura.md`.
- Nota do vault `ManaVault/06-Agentes-e-Skills/agente-comercio-revendas.md`; levantamento do executor da ATV-01 em `ManaVault/00-Inbox/atv01-cre001-executor-nao-e-equipe.md`; ADRs porta única WhatsApp e `2026-07-10-tms-claim-por-numero-antes-do-menu`.
- Skills: `mana-simpleagro`, `mana-softexpert`, `softexpert-wf-ws`, `mana-habilidade-notificacao-whatsapp`, `data-lake-pg`, `agente-pedidos`, `agente-tms`.
