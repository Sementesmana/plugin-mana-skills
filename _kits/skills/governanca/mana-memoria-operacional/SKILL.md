---
name: mana-memoria-operacional
description: >-
  Memória operacional da máquina-hub da Sementes Maná pra qualquer dev do
  modelo federado (Dayan, Lorena, Pablo, futuros). Use SEMPRE na PRIMEIRA
  sessão numa máquina nova de dono de agente — semeia a memória do Cowork com
  os gotchas que custam horas: git não autentica no sandbox, index.lock órfão,
  mount que trunca arquivo, heredoc como escrita confiável. Também quando o
  dev travar com: git pull/push falhando, arquivo que "não salva", deploy que
  não sobe, Railway, banco-mana remoto. Se a conversa é "por que isso não
  funciona na minha máquina?" — use esta skill. GERA também o CLAUDE.md do
  repo — peça "semeia a memória e configura o repo". Traz: falha nunca vira
  dado, 452 do SA e a API que MENTE (listagem trunca aninhado; limit=-1 e
  total mentem — sempre paginado, listagem é só índice; vínculo por posição
  desliza), conferir por conjunto, diff fantasma
  de CRLF (core.autocrlf, jamais checkout), fechamento é push, documentação à
  frente do código, e os 3 pontos do marketplace (espelho, dois JSONs, card
  do cockpit).
---

# Memória Operacional Maná — kit do dono de agente

> **O problema que esta skill resolve:** a máquina-hub (Xayer) acumulou meses de
> gotchas em memória de Cowork + vault. Uma máquina nova começa do zero e
> redescobre tudo na dor. Esta skill é essa memória **empacotada** — instale e
> peça ao Claude: *"semeia a memória operacional"*.

## 0. Configurar o repo — CLAUDE.md do dono (uma vez por agente)

Claude: se o repo do agente do dev NÃO tem `CLAUDE.md` na raiz (ou tem um
desatualizado), crie a partir do template abaixo, preenchendo `<DONO>` e
`<AGENTE>`. Esse arquivo viaja no Git — vale em qualquer máquina que clonar.
Commit junto com o trabalho do dia ("chore: CLAUDE.md do dono").

```markdown
# <AGENTE> — regras de trabalho (dono: <DONO>)

> Claude: leia este arquivo INTEIRO antes de qualquer tarefa neste repo.

## Papéis
- Dono deste agente: <DONO>. Decide o que muda. O hub (Xayer) é revisor.
- Claude faz o trabalho técnico e reporta no final. Não pergunta
  "quer que eu faça?" no meio — faz. Recua só em: credencial que só o
  dono tem, 403 do GitHub, decisão de negócio.

## Git (o sandbox não autentica — quem pusha é o dono no Git Bash)
- ANTES de mexer: `git status` (se sujo: `git stash`) → `git pull`.
- DEPOIS de mexer: Claude valida (py_compile + smoke em /tmp), então
  entrega UM comando pronto: `git add -A && git commit -m "..." && git push`.
- `index.lock` travando: `rm -f .git/index.lock` e repete.
- 1 motorista por vez neste repo. Commits pequenos e frequentes.

## Deploy
- Deploy = `git push` → Railway auto-deploya ~2 min. NUNCA `railway up`.
- Credenciais SÓ em env vars no Railway. Nunca no código, nunca no chat.
- Validar depois: /health + log do Railway + teste no painel.

## Arquitetura obrigatória (Maná)
- LLM sempre via mana-llm-gateway. WhatsApp sempre via hub agente-whatsapp
  (classe + idempotency_key). Dedup por requisição.
- Fonte lenta atrás de painel → mana-habilidade-data-lake-pg (lake-first).
- Receitas: skills mana-arquitetura-padrao + akita + novo-agente-mana.

## Memória que viaja
- O SKILL.md deste repo é a nota canônica do agente. Mudou comportamento,
  endpoint, env var ou integração → atualizar o SKILL.md NO MESMO push.
- Decisão arquitetural grande → avisar o hub (vira ADR no ManaVault).
- Se `ManaVault/` estiver clonado ao lado: consultar 08-Decisoes/_index.md
  e 09-Runbooks/ antes de propor padrão novo.

## Fluxo com o dono
- Um comando por vez. Esperar o resultado antes do próximo.
- Divergência entre doc e realidade → sinalizar ANTES de prosseguir.
```

**Instruções de projeto do Cowork (dev cola em Projeto → instruções):**

```
Trabalho no <AGENTE> (repo com CLAUDE.md na raiz — seguir SEMPRE).
Antes de qualquer tarefa: ler o CLAUDE.md e o SKILL.md do repo.
Skill instalada mana-memoria-operacional cobre gotchas de máquina
(git/mount/deploy). Sou o dono; Claude executa e reporta no final.
```

## 1. Semeadura — fazer na PRIMEIRA sessão (uma vez)

Claude: ao ler esta seção numa máquina onde a memória ainda não foi semeada,
crie os arquivos de memória abaixo (diretório de memória do Cowork, com entrada
no MEMORY.md pra cada um). Conteúdo de cada seed nas seções 2–6.

| Arquivo | Gancho no MEMORY.md |
|---|---|
| `reference_git_maquina_dev.md` | Git: sandbox não autentica; Git Bash do dev roda push; index.lock; pull-antes/push-depois |
| `reference_mount_truncamento.md` | Mount trunca arquivo recém-editado; heredoc escreve; validar em /tmp |
| `reference_deploy_railway_mana.md` | Deploy = git push (nunca railway up); env vars; validar por /health + log |
| `reference_padroes_codigo_validados.md` | Pool keepalives; guard com validade; finally+rollback; dedup por requisição |
| `feedback_fluxo_trabalho_mana.md` | Validar antes do push; 1 comando por vez pro humano; reportar no final |
| `reference_dados_falha_nao_vira_dado.md` | Falha levanta exceção; vazio de erro não persiste; payload diz de quando é; timestamp com offset |
| `reference_sa_single_session_452.md` | SA é single-session: 452 = outro login entrou; usuário dedicado; cura = data lake |
| `feedback_verificacao_por_conjunto.md` | Conferir por diff de conjuntos, nunca por contagem; reportar órfãos E links quebrados |
| `reference_cowork_remoto_bridge.md` | Sessão na nuvem: gravar por commit_files, ler por list_dir, `touch` antes do `git add` |

> Conteúdo dos 5 primeiros nas seções 2–6; dos 4 novos, nas seções 8–10 e em
> `memorias/` (um arquivo por aprendizado, com o índice em `memorias/_INDICE.md`).

## 2. Git e GitHub (o sandbox NÃO autentica)

- **O sandbox do Cowork não tem credencial GitHub.** Clone/push de repo privado
  é SEMPRE o humano no **Git Bash**. Claude edita os arquivos via mount e
  entrega o comando pronto pro dev colar.
- **Sequência canônica** que Claude entrega (um passo por mensagem):
  `git pull` antes de mexer → edições → `git add -A && git commit -m "..." && git push`.
- **`index.lock` órfão** — se `git add/commit` falhar com *"Unable to create
  index.lock: File exists"*: `rm -f .git/index.lock` e repete. Acontece quando
  um processo git morreu no meio (Obsidian Git, sessão caída).
- **Working tree sujo antes de pull** → `git status`; se sujo:
  `git stash && git pull` (stash é backup, não perda). Nunca pull por cima de
  edição não commitada.
- **1 motorista por solução** — antes de editar um repo compartilhado, confirmar
  que ninguém (nem outra sessão de Claude) está com o volante.
- **Paste no Git Bash pode comer `/`** — se um comando colado falhar estranho,
  conferir o que chegou na tela antes de rodar de novo.
- **Nunca editar pasta que não é clone git** — pasta solta = drift, não sobe.

## 3. Mount Windows × sandbox (arquivo que "não salva" / SyntaxError fantasma)

- **Sintoma:** Claude edita um arquivo e depois `py_compile`/`cat` no sandbox
  mostra arquivo TRUNCADO (ex: "SyntaxError: '(' was never closed" na última
  linha). O arquivo real no Windows está ÍNTEGRO.
- **Causa:** o mount do sandbox serve versão em cache de arquivos
  grandes/recém-editados. É leitura stale — não é corrupção.
- **Regras:**
  - *Leitura confiável* = ferramenta Read com caminho Windows.
  - *Escrita confiável em arquivo que o sandbox precisa ler* = heredoc bash
    (`cat > arquivo <<'EOF'`). Escrita via python no mount pode não persistir.
  - *Validação de código editado* = reconstruir cópia em `/tmp` (conteúdo que
    Claude tem em contexto) e rodar `py_compile` + smoke test lá. NUNCA
    confiar no py_compile direto do mount logo após editar.
- **Smoke test padrão:** stub das dependências (config, db, SDK) + exercitar a
  função alterada nos cenários principais. 20 linhas de teste economizam um
  deploy quebrado.

## 4. Deploy e Railway

- **Deploy é `git push`** → Railway auto-deploya em ~2 min. **NUNCA
  `railway up`** (sobe estado local por fora do Git).
- **Credenciais só em env vars no Railway.** Nunca hardcode; nunca colar
  secret no chat (se vazou → rotacionar).
- **Validação pós-deploy:** `/health` (via web_fetch GET) + logs do Railway +
  teste funcional no painel. O sandbox pode não alcançar o domínio de produção
  por allowlist (POST bloqueado) — quem clica botão de produção é o humano;
  Claude confere pelo log.
- **Log é o oráculo:** colocar linhas DIAG no código (contagens, distribuições,
  amostra de chaves SEM PII) transforma "não funciona" em diagnóstico de
  1 leitura de log.

## 5. Padrões de código validados em produção (copiar, não reinventar)

- **Pool Postgres pra banco remoto (banco-mana)** — sempre com keepalives e
  timeouts, senão socket morto vira thread pendurada pra sempre:
  ```python
  ThreadedConnectionPool(1, 8, DATABASE_URL,
      connect_timeout=10,
      keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3,
      options="-c statement_timeout=120000 -c idle_in_transaction_session_timeout=300000")
  ```
- **Devolução de conexão SEMPRE** — `finally: rollback() + putconn()` em todo
  caminho. Vazamento de 8 conexões = app inteiro congelado.
- **Job em background (botão "rodar agora")** — thread daemon + flag de estado
  **com timestamp e validade** (ex: 600s): se a thread morrer/pendurar, o guard
  expira sozinho e libera novo disparo. Flag sem validade = botão travado até
  redeploy. Setar a flag ANTES de iniciar a thread (evita corrida de 2 cliques).
- **Fonte lenta atrás de painel** → habilidade `mana-habilidade-data-lake-pg`
  (lake-first + botão "Atualizar Data Lake"). Não fazer fetch pesado no load.
- **Leitura SE/SOAP por linha em painel zera sob concorrência** (N workers ×
  fetches) — pra totais em lote, usar fonte agregada; detalhe item-a-item só
  em modal sob demanda.
- **Dedup por requisição** (idempotency_key), nunca por conteúdo.
- **LLM sempre via `mana-llm-gateway`; WhatsApp sempre via hub
  `agente-whatsapp`** (skill `mana-arquitetura-padrao` tem a receita).

## 6. Fluxo de trabalho com o Claude da máquina

- **Validar ANTES de pedir o push** — py_compile + smoke em /tmp. O dev não é
  CI; não usar o push dele pra descobrir erro de sintaxe.
- **Um comando por vez pro humano** — em fluxo operacional (terminal,
  migração), entregar UM passo, esperar o resultado, dar o próximo. Nunca
  empacotar 5 passos numa mensagem.
- **Fazer, não perguntar** — tarefa técnica que o Claude consegue fazer, ele
  faz e reporta no final ("Fiz X, criei Y, URL Z"). Recuar só em: credencial
  que só o dev tem, 403 do GitHub, chave virtual pendente.
- **Nota do agente = mesmo repo, mesmo PR** — mudou comportamento/endpoint/env
  → atualizar o SKILL.md/nota do repo no mesmo push.
- **Drift entre doc e realidade** → sinalizar o dono ANTES de prosseguir.

## 7. Repo vizinho como referência (não reinvente padrão)

Antes de inventar padrão (botão, pool, guard, painel, fan-out, state machine),
**clone o agente que já resolveu isso em produção** e copie adaptando:
`cd ~/Desktop/ORQUESTRADOR && git clone https://github.com/Sementesmana/<agente>.git`
(clone de leitura — NUNCA editar repo de outro dono sem coordenar).

| Preciso de... | Clonar | O que copiar |
|---|---|---|
| Data lake / botão "Atualizar agora" | `agente-comercio-revendas` | sync lake-first, botão com estado |
| Pool Postgres robusto + guard de job background | `agente-comercio-revendas` | db.py, api.py `_disparar_sync` |
| Painel financeiro com cache + drill-down + filtros | `agente-financeiro-sa` | /api/dataset, enrichment SA |
| Fan-out DM + portal ocorrências + Pareto | `agente-gestor-comercial` | pipeline gaps, cobrar 1-clique |
| State machine votação + gate humano + ata Word | `agente-comite-credito` | pauta→votos→ata→executeActivity |
| Rota OSRM + cotação WhatsApp com retorno | `agente-tms` | webhook-retorno, tel match |
| Classificação docs Claude → SE com atributos | `agente-documentos` | triagem Haiku, urn:attributes |
| Bot WhatsApp determinístico + PDF/PNG | `agente-gestor-estoque` | harness zero-LLM, send-image |
| PWA mobile GPS/foto → SE | `agente-km` | overlay foto, SOAP sessão |
| Roteamento webhooks Z-API / keywords DM | `agente-router` | GRUPO_IDS, relay |

Copiou o mesmo trecho pela 2ª vez em agentes diferentes → candidato a
habilidade canônica: avisar o hub.

**Conectores/MCPs:** dev novo NÃO instala conector nenhum no D1 — o agente fala
com SE/SA pelo código (env vars), não pelo chat. Instale MCP só quando a tarefa
pedir (e provavelmente o que a tarefa pede é skill/habilidade do cockpit).

## 8. Dados: falha nunca vira dado (regra que custou um painel branco)

Quatro regras que andam juntas — detalhe e história em
[`memorias/falha-nao-vira-dado.md`](memorias/falha-nao-vira-dado.md):

1. **Erro de transporte levanta exceção.** `return []` no caminho de falha é
   proibido — lista vazia significa uma coisa só: **não há registro**.
2. **Vazio de erro não é persistido; falha não sobrescreve snapshot bom.** Vazio
   só entra no lake quando a origem confirmou sucesso (safra nova com zero
   pedidos é verdade gravável — a proibição é no caminho de erro).
3. **Todo payload diz de quando é** (`fonte` + idade) e a tela avisa quando o
   dado está velho. Dado antigo com aviso é útil; sem aviso é mentira.
4. **Timestamp que cruza processo carrega o offset.** ISO sem fuso é ambíguo.

Corolário: **um valor que significa duas coisas é um bug esperando data.** Dê à
falha um tipo próprio.

### Origens lentas: leia do lake, não do ERP

- **Simple Agro é single-session** — HTTP **452** quando o mesmo login entra em
  outro lugar. Credencial **exclusiva da automação** (login humano derruba a
  integração), 452 tratado como 401 com retry limitado, e a cura estrutural é o
  data lake ([`memorias/sa-single-session-452.md`](memorias/sa-single-session-452.md)).
- **Nunca consultar o ERP no caminho da requisição do usuário.** Quem espera a
  origem é o cron, não a pessoa. Ordem de leitura:
  `memória → arquivo → lake → origem ao vivo`; origem fora do ar cai para o lake
  **de qualquer idade** (com o aviso da regra 3).
- **SoftExpert**: leitura por Conjunto de Dados (`se-dataset-reader`) em vez de
  `getTableRecord` paginado. Guarda de truncamento: retorno com exatamente
  10.000 linhas é **possivelmente truncado** — alertar, nunca gravar como completo.

## 9. Conferir por conjunto, nunca por contagem

Soma bate com conjunto errado: um item faltando e um sobrando **se cancelam**.
Antes de dizer "está tudo lá", compare as duas listas nos dois sentidos —
órfãos (existe e não está indexado) **e** links quebrados (indexado e não
existe) — e reporte os dois lados **mesmo vazios**. Receita em
[`memorias/verificar-por-conjunto.md`](memorias/verificar-por-conjunto.md).
Vale para migração, índice do vault, import de memória, carga no banco.

## 10. Cowork remoto (sessão na nuvem + bridge do desktop)

Quando a sessão roda na nuvem com a pasta do dev montada pela bridge, os
fantasmas do mount mudam de nome mas continuam:

- **Gravar no disco do dev = `device_commit_files`**; construir e validar no
  container (`/tmp`) antes.
- **Não editar arquivo do mount in-place** (`sed`, `open(...,'w')`, `git checkout`).
- **Fonte autoritativa do que está no disco = `device_list_dir`** — o bash local
  lê stale logo depois de gravar.
- **`touch` antes do `git add`**: a gravação pela bridge mantém o mtime antigo e
  o git pula o arquivo dizendo *"nothing to commit"*.
- **O bash da bridge não tem rede e não deleta** — para remover, `mv` para
  `_to_delete/` ou `git rm` no Git Bash do dev.

Detalhe em [`memorias/cowork-remoto-bridge.md`](memorias/cowork-remoto-bridge.md).

## 11. Nome do repo ≠ nome do plugin ≠ nome do serviço

Antes de concluir que "falta skill/plugin/nota" para um agente, **confira os três
nomes** — na Maná eles divergem com frequência (repo `agente-gfi` publica como
`portal-gestao-diaria`; `agente-plano-acao` é o `agente-whatsapp-pa`; `agente-ponto`
virou `auditoria-ponto-*`; `agente-mapa-pedidos` roda em `mapa-comercial-production`).
Comparar listas por nome, sem checar o conteúdo, produz gap falso — e o oposto
também: skill publicada sem repo correspondente é mapa sem território. Ao criar
artefato novo, **usar o mesmo nome nos três lugares**.

## 12. Diff fantasma: nunca commitar uma varredura "suja" em lote

Antes de gerar comandos de commit para vários repos de uma vez, **separe mudança
real de fim de linha**. No Windows, sem `core.autocrlf`, o disco grava CRLF e o
HEAD guarda LF: qualquer editor que toque o arquivo cria um diff que parece a
reescrita inteira. Na varredura do parque (18/08), 20+ repos apareciam sujos e só
6 tinham trabalho de verdade.

**Detectar (5 segundos):** `insertions == deletions` no `git diff --stat` é
suspeita; `git diff --ignore-cr-at-eol --stat` vazio é prova — é fantasma, não
commite.

**Curar na máquina:** `core.autocrlf` — **`true`** no Git Bash do Windows (é o que
o POP de passagem de bastão manda na Fase 2.4), **`input`** na sessão Cowork
remota, que é Linux. Uma linha, zero commit, nenhum arquivo reescrito — o Git
normaliza no `git add` e o `status` limpa sozinho. São duas máquinas e dois
`.gitconfig`: configurar num não configura o outro, e máquina antiga não herda o
POP (na hub estava vazio em tudo). **Nunca** use `git checkout -- .` nem `git restore .` para isso — descarte com `.`
apaga trabalho não commitado sem volta (`memorias/descartar-no-escuro.md`):
já apagou edição não commitada aqui. Em repo que mais de uma máquina clona, vacine com
`.gitattributes` contendo `* text=auto`.

Detalhe, comando de varredura do parque inteiro e as duas lições caras em
[`memorias/git-crlf-fantasma-e-checkout.md`](memorias/git-crlf-fantasma-e-checkout.md).

## 13. Fechamento é push, não "funcionou"

Ao fim de toda tarefa não trivial, **perguntar explicitamente se sobe pro Git** — com o
comando pronto — e atualizar a nota do vault e a SKILL junto. Sem esse rito, o trabalho
fica no disco e a documentação segue em frente sozinha: na varredura de 18–19/08 o parque
tinha **quatro** funcionalidades descritas como prontas no vault e ausentes do repositório,
com atrasos de 13 dias a 2 meses — uma delas devolvendo 404 em produção e exibindo painel
zerado como se fosse dado.

Onde a nota está à frente do código, ela é o **mapa do que falta**: não apague nem corrija
a data — confira contra o código e commite. Antes de subir trabalho represado, três
conferências: `git fetch` (log local é cache, não verdade), dependências no
`requirements.txt`, e colisão com o que entrou depois.

Detalhe, tabela dos quatro casos e a varredura periódica em
[`memorias/documentacao-a-frente-do-codigo.md`](memorias/documentacao-a-frente-do-codigo.md).

## 14. Mexeu em skill do marketplace? Confira os TRÊS pontos antes de fechar

Publicar não é só editar o `SKILL.md`. A skill vive em três lugares e eles divergem
sozinhos — cada um por um motivo diferente:

| Ponto | O que conferir | Como diverge |
|---|---|---|
| **1. Espelho no `_kits/`** | `plugins/<x>/skills/<x>/SKILL.md` e `_kits/skills/governanca/<x>/SKILL.md` **byte a byte** (`md5sum` nos dois) | edita-se um e esquece o outro |
| **2. Versão em DOIS arquivos** | `plugins/<x>/.claude-plugin/plugin.json` **e** `.claude-plugin/marketplace.json` | bumpar só um deixa o Cowork sem sinal de que mudou |
| **3. Card no cockpit** | `agente-monitor/plataforma_agentica.py` — nome com a versão **e** a descrição | é outro repo; ninguém lembra |

E um quarto que não é arquivo: **a `description` do frontmatter**. Ela tem teto de
**1024 caracteres** e é a *vitrine* — o catálogo de skills mostra ela, não o corpo. Se
o corpo vai pra v1.6 e a `description` para na v1.4, todo mundo enxerga versão velha e
não abre a skill. Como o teto é fixo, **cada versão nova disputa espaço com as antigas**:
resuma o que envelheceu em vez de só empilhar.

⚠️ **Caso real (19/08):** seis bumps de versão num dia e **zero** conferências do
cockpit — o card ficou anunciando `v1.3.0` e "5 memórias iniciais" com a skill em v1.6.1
e 11 memórias. Quem pegou foi o Claude de OUTRA conta, na verificação cruzada. A regra
existia; morava só na memória local de uma máquina, que é ilha. Por isso ela está aqui
agora: **regra que não viaja pelo marketplace não é regra, é lembrete pessoal.**

## Como instalar (dev novo)

1. Cockpit Maná Builder → card **Skills (plugin)** → `mana-memoria-operacional`
   → botão "📥 Copiar SKILL.md" (ou copie este arquivo do repo
   `Sementesmana/plugin-mana-skills`, pasta
   `_kits/skills/governanca/mana-memoria-operacional/`).
2. Cowork → Personalizar → Habilidades → Adicionar → cole.
3. Na primeira conversa: *"semeia a memória operacional e configura o repo"*
   — Claude cria os seeds da seção 1 **e** o CLAUDE.md da seção 0. A máquina
   nasce com a memória da casa e o repo com o contrato de trabalho.

---
*v1.10.0 — 2026-08-22. v1.10 acrescenta a **prova de frescor** em
`memorias/verificar-por-conjunto.md`: conjunto completo não garante conteúdo fresco.
Definir ANTES da migração uma pergunta cuja resposta certa só existe se a última
atualização chegou, e checar o artefato de ORIGEM antes de culpar o transporte — o
achado que gerou a regra foi a memória do 452 já estar velha dentro do próprio backup.
Origem: conferência do one-way pro Claude Team (22/08).*

*v1.9.0 — 2026-08-21. v1.9 acrescenta `memorias/sa-api-mente-listagem-e-limit.md`
(a API do SA mente: listagem trunca lista aninhada — só o data_volume mais recente;
limit=-1 vem incompleto e o `total` mente junto — sempre paginado; listagem é índice,
documento é a verdade; vínculo por posição desliza — vincule pelo _id) e atualiza
`sa-single-session-452.md` com a cura estrutural EM PRODUÇÃO (mana-sa-gateway:
credencial própria, portão 2s, zero 452 desde a migração do TMS) + o gotcha do
token que já vem com "Bearer " (duplicar = 401 com login ok). Origem: migração
do agente-tms pro gateway, caso do agendamento de 52 bags invisível e caminhão
#12 vinculado errado (21/08).
v1.8.0 — 2026-08-19. v1.8 acrescenta `memorias/descartar-no-escuro.md`: `git restore .`
e a familia toda (`checkout -- .`, `reset --hard`, `clean -fd`) apagam trabalho nao
commitado sem volta — dois casos reais, mais push rejeitado por commitar de dois lugares
e committer com e-mail inventado.
v1.7.0 — 2026-08-19. v1.7 promove pra cá a regra dos três pontos do marketplace
(seção 14) — espelho, versão nos dois JSONs, card do cockpit e a vitrine de 1024
caracteres. Motivo: a regra existia só na memória local de uma máquina e foi violada
seis vezes num dia; quem pegou foi o Claude de outra conta.
v1.6.1 — 2026-08-19. v1.6.1 corrige a vitrine (a `description` parava na v1.4,
e o catálogo anunciava versão velha com o corpo novo) e acrescenta à memória do CRLF
que na sessão Cowork remota o `core.autocrlf` é **por sessão** — container efêmero.
Achados do Claude do Maná-Dev na verificação cruzada.
v1.6.0 — 2026-08-19. v1.6 acrescenta a seção 13 (fechamento é push) e a memória
`documentacao-a-frente-do-codigo.md`, tiradas da varredura dos 62 repos do parque.
v1.5.0 — 2026-08-18. v1.5 acrescenta a seção 12 (diff fantasma de CRLF: nunca
commitar varredura suja em lote) e reescreve a memória do CRLF com a cura sem
checkout (`core.autocrlf input`), depois da varredura dos 61 repos do parque.
v1.4.0 — 2026-08-18. v1.1 adiciona seção 0 (CLAUDE.md do dono + instruções de
projeto); v1.2, seção 7 (repo-vizinho-como-referência + conectores); v1.3, o
diretório `memorias/` (memória viva que propaga pelo marketplace); **v1.4**
promove para a skill o que estava só na máquina-hub — seção 8 (falha nunca vira
dado + 452 do SA + ordem de leitura), seção 9 (conferir por conjunto), seção 10
(Cowork remoto pela bridge), seção 11 (repo ≠ plugin ≠ serviço), 4 seeds novos e
5 memórias vivas. Origem: incidentes reais — painel branco por `[]` cacheado
(13/08), apagão 452 do Simple Agro, healthcheck morto por `$PORT` literal
(agente-governanca, 07/08), truncamento pela bridge (gestor-comercial, 14/07) e
a conferência que fechou a conta com 1 link quebrado (transplante de memória
para a org Team, 18/08).*
