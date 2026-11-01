---
name: agente-comite-credito
description: "Mapa do agente-comite-credito (Sementes Maná), Flask+PG (schema comite)+Railway: comitê de crédito digital 100% em grupos WhatsApp (multi-comitê), pauta do CRE-001, convocação com Resumo de Crédito do Tarken, discussão e votos via agente-router, ata timbrada no GED do SE, comitê de carregamento, cobranças automáticas e CRM de crédito (cadastro, ICP, revendas, reports). Traz decisões, armadilhas, contratos e pendências que o código não diz. Use SEMPRE no agente-comite-credito ou ao citar comitê de crédito, ata de comitê, DEC-01/02/08, decisaoXX, Tarken, aprovo reprovo, unanimidade, pode_executar, COMITE_GRUPO_IDS, creditodefin, limitecredaprov, comitê de carregamento, ICP, endosso de revenda."
---

# agente-comite-credito — mapa

## O que é
- Substitui o componente de Reunião do SE por um rito no grupo WhatsApp: pauta (processo CRE-001) → convocação → discussão → `gerar ata` (prévia) → votação → `atualizar o SE` (gate humano) → ata oficial no GED, categoria CRE.
- Desde 2026-09 também é o **CRM de crédito**: histórico das deliberações, cadastro por cliente, régua ICP, perfil de revendas e reports (contrato do ADR 2026-09-04, consumido pela aba Reports e pelo mana-reports).
- Repo `Sementesmana/agente-comite-credito`; deploy por push em `main` (Railway builda o Dockerfile). Produção: `https://agente-comite-credito-production.up.railway.app` (consta só na skill, não no código).
- Banco-mana, schema `comite`. Grupo principal = o do `COMITE_GRUPO_ID` (120363410445766251-group, "Comitê de Crédito").

## Onde está a verdade
- `app/services/comite.py` — state machine, roteador de comandos (`processar_mensagem_grupo`), convocação, execução no SE, gravação do limite.
- `app/services/carregamento.py` — o comitê de carregamento (só o que difere do crédito).
- `app/config.py` — `DEC_CAMPOS`/`DEC_TEMAS` (o que cada DEC delibera) e o porquê de cada chave.
- `app/integrations/` — `softexpert.py` (SOAP direto), `whatsapp.py` (hub), `claude.py` (modelos, regex de voto), `tarken.py`, `pedidos.py` (ponte com o agente-pedidos), `_pseudonimizador.py`.
- `app/migracoes.py` — toda coluna nova (DDL idempotente). `app/main.py` — boot e agendador.
- CRM: `cadastro_cliente`, `icp` (`REGUA` + `REGUA_VERSAO`), `icp_revenda`, `perfil_revenda`, `compras_sa`, `extrator_ata`, `extrator_perfil`, `perfil_rotina`, `reports`, `numeros` (único parser de número escrito por gente).
- As docstrings dos módulos contam o incidente que originou cada regra: ler antes de mudar.

## Regras e decisões que o código não explica sozinho

### Rito do comitê
- Comandos `gerar ata`, `atualizar o SE` e `publicar ata` são **só do operador** (`pode_executar`). O operador nunca é votante e não entra na ata.
- `gerar ata` exige ≥1 mensagem de cada participante. "Todos falaram" ≠ "todos concordaram": o painel usa `posicoes.py` (regex na chegada, Haiku só quando muda a ação) para dizer se ainda há debate.
- Votos: APROVO / REPROVO / **AJUSTAR**. Qualquer REPROVO reprova; senão qualquer AJUSTAR devolve ao vendedor (ActionSequence 3) e a volta gera a versão 2 da ata; aprovação só por unanimidade.
- "Acompanho fulano" é **ponteiro** para a posição de outro, não voto: resolvido contra a posição real do acompanhado; se diverge ou não existe, fica em aberto. Negação nas ~3 palavras antes do termo inverte ("não concordo" = recusa).
- Ordem inegociável no `atualizar o SE`: formulário (`assuntodecXX` + `decisaoXX`, pois a rota Reprovado manda `decisaoXX` ao vendedor) → ata no SE (newDocument + newAssocDocument) → `executeActivity` → `limitecredaprov` por último.
- `decisaoXX` = seção "Decisão" da ata, e precisa dizer **qual** comitê decidiu (é o único registro disso no SE).
- **Cada DEC delibera uma coisa**: DEC-01 = continuidade da análise sem termo de anuência (não aprova valor, não grava limite, a ata não pode falar em crédito aprovado); DEC-02 = concessão + limite; DEC-08 = alçada superior, quando o valor passa de R$ 600 mil (limiar do desenho do CRE-001 no SE, não está no código).
- Valores do scred: `reais` = solicitado pelo vendedor; `crditototalfaz` = sugerido pelo modelo; `credaprtarken` = sugestão do Rating/Tarken; `creditodefin` = sugerido DEFINITIVO, o que vale na convocação; `limitecredaprov` = aprovado pelo comitê. No rito, o agente só escreve `limitecredaprov` (além de assunto/decisão), depois do executeActivity; os demais só se corrigem à mão via `/api/admin/gravar-scred`.
- Valor aprovado tem de estar preenchido antes de executar: sem ele não há chute e o limite não é gravado.
- Título do WF = `VENDEDOR | CLIENTE | CPF | VALOR`: só o vendedor vai ao grupo. Pareceres vão **na íntegra** (membros não acessam o painel), um por vez.
- O PDF do Tarken **não** é mais enviado ao grupo pelo bot (operador anexa). O derivado é o Resumo de Crédito (PNG), enviado por último, em thread. Pauta sem Tarken avisa no grupo que não haverá Resumo.
- Reunião EXECUTADA é imutável; `reabrir` volta a COMPLETA (com `limpar_doc` regenera a ata no layout vigente) e `desfazer-reabertura` é a volta (só para pauta já executada; recusa carregamento).

### Multi-comitê e carregamento
- Comitê = grupo WhatsApp (tabela `grupos`). Roteamento **estrito**: mensagem de grupo não cadastrado é ignorada, nunca cai no principal. Receita de comitê novo: bot no grupo → id no `GET /grupos` do hub → `/painel-config` → copiar membros → somar no `COMITE_GRUPO_IDS` do agente-router → `/api/admin/diagnostico-comites`.
- O nome do grupo vira `<comitê> · <CLIENTE>` na convocação (sempre, idempotente) e volta ao base ao encerrar.
- Carregamento é outro **objeto de decisão** no mesmo rito, não outro comitê; o desvio mora no roteador, não dentro das funções do crédito (o crédito roda todo dia e não pode parar). Não escreve no SE: APROVADO → `liberado_excecao`, REPROVADO → `reprovado`, AJUSTE não mexe. Só abre pauta se o status for `aguardando_comite`. Cancelar/excluir/reabrir desfaz só o que **esta** pauta escreveu (confere `quem`).
- Vendedor entra no grupo na pauta dele e sai na publicação (vendedores não podem ver clientes uns dos outros). Saída não confirmada → pauta fica ABERTA. Casamento vendedor por nome; ambíguo não escolhe. "Incerto" do hub nunca conta como sucesso.

### Limite aprovado (a fonte da verdade)
- O SE recalcula `limitecredaprov` com o número do **modelo** a cada transição de atividade (incidentes 000035/000023, 000194, 000244, 000192). Por isso: grava **primeiro** em `agente_pedidos.credito_comite` (onde nada recalcula), depois no SE, confere, e reconfere em 90s/10min/1h. Correção automática não vai ao grupo (Xayer, 2026-09-16); só a falha avisa.
- Quem precisa do número certo lê `/api/credito-aprovado` (última versão por processo); o campo do SE é cópia.
- Reconciliação por **evento**: a ingestão do lake do agente-pedidos chama `/api/admin/sincronizar-limites`; relógio curto desligado (`SYNC_LIMITE_INTERVALO_MIN=0`), passada funda 05:40. Ela tem chave própria: desligar cobranças não pode desligá-la.

### CRM, ICP e reports
- **Lacuna é dado**: cadastro mostra o que falta; **falta de dado não é nota baixa** (nota só sobre o peso com dado + `confianca` separada). `REGUA` é opinião da diretoria, com motivo ao lado de cada peso.
- Vocabulário fechado nos extratores; tudo extraído da ata cita trecho literal **conferido** contra o texto, senão é descartado. Ata é julgamento de gente: não reextrair inteira (`preencher_papel` só preenche o buraco). Tarken pode ser reprocessado, mas **nunca sobrescreve com menos**.
- Cliente liga entre safras por `cpfcnpj_hash` (HMAC, ADR 2026-06-14), nunca CPF em claro. Compras: hash do lado SA; método de casamento (documento/raiz/nome) sempre declarado. Compras só dos lakes no banco (`agente_financeiro_sa.data_lake`, que tem safra encerrada, + `agro.lake_pedidos_raw`), **nunca SA direto** (452). Uma safra só não é histórico.
- Escopo do perfil: só clientes que passaram pelo comitê.
- Endosso = `uso_semente == 'Agricultor Endossado'` com revenda; Distribuidor conta como cliente dela mesma (mesma regra do /painel-reais). Base pequena vai na confiança, nunca na nota. Eliminatório (inadimplência, RJ) tem dimensão própria.
- Grupo 7 (Vínculo e valor percebido, método Nardon) = estado `a_perguntar`, **fora** da completude global e **fora** da régua (dois testes guardam). Fila começa pelos melhores. Respostas lidas ao vivo de `perfil_confirmacao` (a `perfil_cliente` é materializada e seria sobrescrita). A tela não declara perguntas: desenha o contrato.
- Reports: servidor calcula tudo; falha vira `degradado` + `avisos`, **nunca zero**; subtotal é declarado.
- Uma senha só para o painel (Xayer cortou senha comercial separada). `X-Report-Key` só estreita: escreve apenas os campos de entrevista (`papel_operacao` → 403) e pode disparar sincronizar-limites.
- Rotina do perfil às 08:00 BRT, **depois** da ingestão do lake comercial (07:30).

### LGPD e LLM
- Pseudonimização obrigatória antes de todo LLM (ADR 2026-06-19): nomes → CLIENTE/VENDEDOR/DIRETOR_N, desmascara antes de gravar/exibir; mapa só em memória. CPF/CNPJ nunca em prompt; telefone em log como HMAC truncado.
- Tarken: `resumir_tarken` levanta NotImplementedError de propósito (não reativar). Override consciente (ADR 2026-07-28-comite-painel-credito-resumo-tarken-llm): o Tarken vai ao LLM para o Resumo; caminho por **página** — texto quando há camada de texto (4x mais barato e mais exato), imagem quando não há (PII vai junto).
- Modelos separados por custo (2026-09-07: Opus era 57% do gasto de IA da casa): ata = `mana-juridico` (só ela, há teste), extração = `mana-equilibrio`, voto = `mana-rapido`; `LLM_MODEL_TARKEN` permite fixar só o Tarken no Opus.

## Armadilhas conhecidas (sintoma → causa → o que fazer)
- Processo aprovado aparece com R$ 0,00 ou com o valor do Tarken → SE recalculou `limitecredaprov` → ver seção do limite; corrigir com `/api/admin/sincronizar-limites` ou `/api/admin/publicar-credito/<idprocess>`.
- `UndefinedColumn` numa tela sem relação → DDL não rodou → coluna nova só em `migracoes.py` (roda em todo worker), conferir `/api/admin/migrar`. Nada de UPDATE/DROP em migração (backfill vai em rota com prévia).
- Worker morto no boot (`UniqueViolation` em pg_type) → `create_all` em paralelo → advisory lock de migração; não tirar. `lock_timeout`/`statement_timeout` no engine evitam fila atrás de ALTER preso.
- `getTableRecord` (fm_ws) ignora filtro e paginação nesta instância → filtra no cliente e para em página repetida.
- `scred.idprocess` apagado por engano (é campo editável) → `POST /api/admin/restaurar-idprocess`.
- Revisão antiga do CRE-001 exige reunião associada na DEC → o bot sugere associar e repetir; se a API não enxergar a reunião reassociada (voltar atividade limpa a associação), avançar a DEC à mão e usar `publicar ata`.
- Comando cai na pauta errada → `_reuniao_ativa` entrega à pauta mais recente do grupo → pauta reaberta fica inalcançável com outra em discussão; usar `desfazer-reabertura`.
- Mensagens do grupo descartadas como "não participante" (bug do `grupo_id`, 2026-08-10) → `/importar-discussao` registra sem reenviar nada.
- "Failed to fetch" em extração/backfill → gateway do Railway corta requisição longa (LLM 30-60s) → responder na hora e trabalhar em thread.
- Resumo não chega → falha na thread; o grupo é avisado; reenviar com `/api/admin/reenviar-resumo/<processo>`.
- Painel devolve 429 ("botão que não faz nada") → rate limit baixo → manter 1000/h.
- 401 com a chave certa → branco no fim da env colada no Railway (`.strip()` já trata).
- "R$ 79M" lido como 79 reais → parse de número fora de `numeros.py` → usar só ele.
- "concordo" dentro de "não concordo" virou aprovação (2026-09-07) → negação corrigida; auditoria retroativa em `ferramentas/auditar_votos_negados.py` (não chama `create_app`).
- Build falha por Docker Hub → não recolocar `# syntax=docker/dockerfile:1.4`. Chromium: libs à mão, `playwright install-deps` quebra no bookworm.
- Z-API é aparelho dedicado; operador comanda do próprio celular. Toggle "enviadas por mim" no router fica DESLIGADO (exceção fromMe é código dormente).

## Contratos com sistemas externos
- **SoftExpert** (SOAP direto, padrão `softexpert-wf-ws`, não o orchestrator): scred do CRE-001 (formulário comitecredito); DECs com ActionSequence 1=Aprovado, 2=Reprovado, 3=Ajuste; ata em `newDocument` categoria CRE com atributos sanitizados (TIPOCLIENT só Agricultor|Distribuidor|Multiplicador; DOCUMENTO = "Ata de Comitê de Crédito" com acentos exatos, fora do domínio dá "Registro não encontrado"). `SE_USER_ID` precisa estar autorizado nas DECs.
- **agente-router** (inbound): relay raw Z-API para `/api/webhook` com Bearer `ROUTER_SECRET`; em grupo, remetente vem em `participantPhone` e o `phone` é o grupo; áudio chega transcrito (Whisper). O bot responde só em texto.
- **Hub agente-whatsapp** (outbound, X-API-Key): `/send-whatsapp`, `/send-document`, `/send-image`, `/rename-group`, `/group-participant` (200 confirmado, 202 incerto). Z-API responde ok até para grupo inexistente.
- **agente-pedidos**: lê `/api/totais-financeiro` (a-prazo por CNPJ-raiz/CPF, mesma régua do /painel-reais) e `/api/vencimentos`; escreve por SQL em `agente_pedidos.credito_comite` e `agente_pedidos.status_carregamento` (vocabulário é contrato com `_CARREG_VALIDOS` de lá); lê `agente_pedidos.analise_revisao`. O agente-pedidos lê `comite.historico_credito` no sentido inverso e chama sincronizar-limites.
- **mana-reports**: `X-Report-Key` nos reports, `/api/credito-aprovado` e confirmação de perfil. **agente-bartermanager** consome as garantias estruturadas da ata.
- **mana-llm-gateway**: usado quando `LLM_GATEWAY_URL/KEY` existem; senão Anthropic direto.

## Como testar e subir
- `pip install -r requirements.txt && pytest tests/` (o `conftest` põe env mínima e SQLite). Vários testes leem o código-fonte por regex: renomear função ou mover bloco pode quebrar teste sem bug.
- Deploy = push em `main`; nunca `railway up`. Depois: `/health`, `/api/admin/migrar` (falhas vazias) e `/api/admin/scheduler` (jobs ativos).
- Cobranças: `services/lembretes.py`, varredura a cada 30 min com advisory lock (senão 2 workers cobram em dobro); config GLOBAL com exceção por comitê, no banco via `/painel-lembretes` (padrão 8/12/16h, carência 2h, máx 3 por pauta+fase, grupo + DM com o nome do comitê); a env só liga/desliga.

## Pendências conhecidas
- Caminho TEXTO do Tarken: a docstring de `tarken.py` diz que se pseudonimiza, mas `extrair`/`extrair_de_texto` mandam o texto cru (sem `_pseudonimizador`). Corrigir ou registrar no ADR.
- Envio ao hub sem `classe` + `idempotency_key` (exigidos pelo padrão `mana-arquitetura-padrao`); só manda `agente`.
- CI (`.github/workflows/ci.yml`) roda só `test_*.py` da raiz: a suíte em `tests/` não roda no CI.
- Desalinhamentos: `.env.example` velho (rate limit 60/h, `HUB_SUPORTA_DOCUMENTO=false`, sem `REPORT_KEY`/gateway); README e docstring de `models/comite.py` dizem que qualquer membro gera ata (o código restringe ao operador); `_lixo/` com locks do git e rascunhos; `.claude/skills/.../SKILL.md` é uma terceira cópia da skill.
- Divergência do `qsa` Sonnet × Opus no Tarken (000175): decisão humana pendente.
- Validar `executeActivity` automático no 1º WF da revisão nova; rotacionar `ROUTER_SECRET`/`COMITE_BOT_SECRET` (expostos no setup de 2026-06-11); ADR formalizando o desenho e fechando o caminho texto do Tarken.
- `REGUA` do ICP virar parâmetro de servidor; login por pessoa (resolveria senha única e o `quem` = "painel"); report `padrao-dos-melhores` quando houver respostas do grupo 7.
- Ideias: polling no painel; reunião por chamada.

## Para ir além
- Não há `CLAUDE.md` no repo. Nota do vault: `ManaVault/06-Agentes-e-Skills/agente-comite-credito.md`.
- ADRs citados: 2026-06-14 (histórico de crédito/hash), 2026-06-19 (pseudonimização), 2026-07-28 (Resumo Tarken por LLM), 2026-08-27 (extração da ata; dado entre agentes pelo banco), 2026-09-04 (contrato de reports).
- Skills irmãs: `softexpert-wf-ws`, `agente-pedidos`, `agente-router`, `agente-whatsapp`, `mana-arquitetura-padrao`.
