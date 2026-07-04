---
name: mana-memoria-operacional
description: >-
  Memória operacional destilada da máquina-hub da Sementes Maná pra qualquer
  dev do modelo federado (Dayan, Lorena, futuros). Use SEMPRE na PRIMEIRA
  sessão numa máquina nova de dono de agente — ela semeia a memória do Cowork
  com os gotchas que custam horas: git não autentica no sandbox, index.lock
  órfão, mount que trunca arquivo recém-editado, heredoc como escrita
  confiável, validação em /tmp antes do push, pool Postgres remoto com
  keepalives, guard de thread com validade. Também use quando o dev travar
  com: git pull/push falhando, arquivo que "não salva", SyntaxError fantasma,
  sync pendurado, deploy que não sobe, Railway, banco-mana remoto. Se a
  conversa é "por que isso não funciona na minha máquina?" — use esta skill.
  v1.1: além da memória, GERA o CLAUDE.md do repo do agente (contrato de
  trabalho que viaja no Git) — peça "semeia a memória e configura o repo".
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
*v1.1.0 — 2026-07-03. v1.1 adiciona seção 0 (CLAUDE.md do dono + instruções
de projeto). Origem: memória acumulada da máquina-hub (Xayer) + incidentes
reais (index.lock e truncamento de mount no piloto Dayan 2; sync pendurado
por socket morto 2026-07-03; vazamento de pool 2026-07-03).*
