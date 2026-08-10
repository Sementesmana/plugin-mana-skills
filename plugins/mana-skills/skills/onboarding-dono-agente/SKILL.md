---
name: onboarding-dono-agente
description: >-
  Passagem de bastão COMPLETA para dono de agente Maná (dev ou não-dev),
  modelo multi-máquina (Cowork + GitHub Org + Railway + ManaVault). Use SEMPRE
  que: onboardar dono novo, repassar agente, dar agente ADICIONAL a dono
  veterano, ou continuar piloto pelo hub (dono travado/créditos). v3 consolida
  os 4 pilotos (Dayan, Lorena, Dayan-2, Pablo): 4 fases com POP imprimível
  (09-Runbooks/pop-passagem-bastao-dono-agente.md), caminho VETERANO (máquina
  já configurada, ~15min), 4 variações de handoff (migrar, agente novo,
  build-then-handoff, continuação-pelo-hub), decisão Member vs Collaborator
  (collaborator NUNCA cria repo), repos privados por padrão, gh CLI, autocrlf
  na Fase 2, Fase 3 em 5min via mana-memoria-operacional v1.3 (memória viva),
  19 gotchas acumulados. Também quando mencionar: passagem de bastão,
  handoff, novo dev, multi-máquina, replicar piloto, semeia a memória.
---

# Passagem de bastão — dono de agente Maná (v3, consolidada)

> Procedimento validado em **4 pilotos**:
> - 1º **Dayan / agente-precificacao** (2026-05-20) — dev, agente novo proposto pelo dono
> - 2º **Lorena / agente-auditoria-ponto** (2026-06-11) — não-dev, build-then-handoff
> - 3º **Dayan-2 / agente-comercio-revendas** (2026-07-03) — continuação-pelo-hub
> - 4º **Pablo / agente-bartermanager** (2026-08-03) — não-dev CRIANDO repo (Member da Org + gh CLI)
>
> **POP imprimível (1 página, é por ele que o repasse roda):**
> `ManaVault/09-Runbooks/pop-passagem-bastao-dono-agente.md`
>
> ADRs: `2026-05-19-piloto-multi-maquina-dayan-precificacao` ·
> `2026-06-11-handoff-agente-auditoria-ponto-lorena` ·
> `2026-06-24-sementesmana-virou-organization-github` ·
> `2026-08-03-repos-privados-por-padrao`

---

## Quando usar

- Colaborador novo vai assumir um agente Maná (qualquer perfil)
- Dono **veterano** vai receber um agente ADICIONAL (caminho curto — ver Fase 2-V)
- Continuar um piloto pelo hub (dono travou: créditos, máquina, bug)
- Padronizar/replicar o setup multi-máquina

## Quem conduz — hub OU o próprio dono

O dono pode **se auto-conduzir** nas Fases 2–4. Só a **Fase 1** (convites) exige o
hub. Auto-condução: dono instala esta skill + `mana-memoria-operacional` e manda ao
hub UMA mensagem:

```
Preciso de acesso pra assumir o <agente>:
1. GitHub: meu username REAL é <username> — acesso a Sementesmana/<agente>,
   mana-vault e plugin-mana-skills (Member da Org se eu for CRIAR repos)
2. Railway: convite Member — meu email: <email>
3. Ativa Watch → All Activity nos repos (teu acompanhamento)
```

## Pré-decisões obrigatórias (responder ANTES de começar)

1. **Qual agente?** 2. **Username GitHub REAL** (confirmar por print — erro dá acesso
a repo privado pra pessoa errada)? 3. **Email Railway?** 4. **Push direto ou PR?**
5. **Perfil: dev ou não-dev?** 6. **Background?** 7. **Data de início** (revisão +4
semanas). 8. **Máquina nova ou dono veterano?** — veterano pula quase toda a Fase 2.

## As 4 variações de handoff

| Variação | Quando | Engenharia | Validado em |
|---|---|---|---|
| **A — Migrar existente** | Agente em produção muda de dono | já existe | padrão base |
| **B — Agente novo** | Dono propõe e CRIA o agente | dono cria (exige Member da Org + gh) | Dayan; **Pablo (não-dev!)** |
| **C — Build-then-handoff** | Hub constrói e valida em prod, depois repassa | hub faz tudo | Lorena |
| **D — Continuação-pelo-hub** | Dono travou no meio; hub EXECUTA, dono DECIDE | hub executa | Dayan-2 |

### Variação D — regras que salvam produção

1. Dono manda o contexto (export da sessão + logs); hub lê TUDO antes de agir.
2. Hub executa, dono decide — escopo não muda sem o dono.
3. **Sobras não commitadas na máquina do dono:** quando ele voltar,
   `git status` → `git stash` → `git pull`. NUNCA pull por cima de árvore suja;
   NUNCA `deploy.sh`/`add -A` antes de reconciliar com o main.
4. **1 motorista por repo.** Drift inesperado no working tree → PARAR e perguntar
   quem está dirigindo.
5. Devolução: dono roda stash+pull e o hub manda as **correções de contexto**
   (commits que já estão no main, o que já foi validado, próxima tarefa) — sem
   isso o Claude do dono re-propõe trabalho feito.
6. **Rede hub-compila:** dono pusha sem conseguir validar → hub roda pull +
   `py_compile` + smoke no clone dele. 30s, evita boot quebrado em produção.

## Dono não-dev (validado Lorena e Pablo)

- **1 passo por mensagem**, cada um com critério de "deu certo" observável.
- Tudo **copy-paste**: comando completo com `cd` embutido, um bloco por passo.
- Intermediário: dono remoto → hub pede o passo ao Claude, repassa por WhatsApp,
  dono devolve o output (print/paste).
- CLAUDE.md do repo em **linguagem de negócio** — o dono decide o "o quê".

---

## Arquitetura

```
Cada dono opera da própria máquina via Cowork.
GitHub = cérebro compartilhado (Sementesmana = ORGANIZATION desde 2026-06-24):
  Sementesmana/<agente>       → código + CLAUDE.md do dono + SKILL.md (nota canônica)
  Sementesmana/mana-vault     → vault (ADRs, runbooks, transversal)
  Sementesmana/plugin-mana-skills → marketplace + MEMÓRIA VIVA (memorias/)
Sync: pull antes de mexer, push depois. 1 motorista por solução.
Deploy: git push → Railway auto-deploya ~2min. NUNCA railway up.
Repos PRIVADOS por padrão (ADR 2026-08-03). Público = exceção justificada.
```

---

## Procedimento (4 fases) — checklist executável no POP

### Fase 1 — Hub prepara acessos (~10min)

**1.1 GitHub — Member da Org OU Collaborator por repo (a decisão que já queimou — Pablo):**

| | Collaborator por repo | **Member da Organization** |
|---|---|---|
| Convite | `.../<repo>/settings/access` | `github.com/orgs/Sementesmana/people` → Invite |
| Acessa | só os repos liberados | todos (Base permission = Read) |
| **Cria repo novo** | ❌ **NUNCA** (GitHub: *"Outside collaborators can never create repositories"* — não existe config que libere) | ✅ (com 1.3 configurado) |

Regra: só **manter** agente existente (A/C) → Collaborator basta. Vai **criar**
repo (B/D, `gh repo create`) → **Member da Org**. Member com Base=Read lê o
portfólio inteiro — ok pra funcionário, não pra terceiro.

Em qualquer caso, garantir acesso a: `mana-vault` (**sempre**),
`plugin-mana-skills` (**sempre** — marketplace + memória viva; Write livre pra
donos federados, decisão 2026-07-20) e o(s) repo(s) do escopo.
Ativar **Watch → All Activity** nos repos (o hub também acompanha pela aba
**Versionamento do cockpit**, 2026-08-09).

**1.2 Railway** — Workspace → People → Invite (email, role Member).

**1.3 Members criam repos (1× pra Org):**
`github.com/organizations/Sementesmana/settings/member_privileges` →
Repository creation → marcar **Private** (só Private — ADR repos privados).

**1.4 Secret scanning + Push protection (1× pra Org):**
`github.com/organizations/Sementesmana/settings/security_analysis` → Enable all
nos dois. O GitHub bloqueia push com chave/token reconhecido.

### Fase 2 — Máquina do dono NOVO (~20min)

1. **Cowork** logado na conta dele.
2. **Git for Windows** com **Git Credential Manager** marcado.
3. **GitHub CLI**: `winget install --id GitHub.cli` (fechar/reabrir Git Bash).
4. Configurar Git — **as 3 linhas, a terceira evita as "modificações fantasma"
   de CRLF que assombram toda máquina Windows** (memória viva:
   `git-crlf-fantasma-e-checkout.md`):
   ```bash
   git config --global user.name "Nome do Dono"
   git config --global user.email "email@dominio.com"
   git config --global core.autocrlf true
   ```
5. **Autenticar o gh** (1× por máquina): `gh auth login` → GitHub.com → HTTPS →
   browser. Confirmar com `gh auth status`.
6. **Aceitar os convites** (GitHub + Railway) ANTES do clone — senão
   "Repository not found".
7. Clonar (o marketplace entra SEMPRE — é a memória viva):
   ```bash
   mkdir -p ~/Desktop/ORQUESTRADOR && cd ~/Desktop/ORQUESTRADOR
   git clone https://github.com/Sementesmana/mana-vault.git ManaVault
   git clone https://github.com/Sementesmana/plugin-mana-skills.git
   git clone https://github.com/Sementesmana/<agente>.git
   ```
8. ⚠️ **OneDrive + Git é antipattern** — Desktop sincronizado? Usar
   `C:\Users\<dono>\ORQUESTRADOR\`.
9. ⚠️ **Máquina já usada por outra função:** backup `.bak` de CLAUDE.md/memory
   antigos antes do setup novo.

### Fase 2-V — Dono VETERANO recebendo agente adicional (~5min)

Máquina já configurada (git, gh, Cowork, vault clonado)? A Fase 2 vira só:

```bash
cd ~/Desktop/ORQUESTRADOR && \
git -C ManaVault pull && git -C plugin-mana-skills pull && \
git clone https://github.com/Sementesmana/<agente-novo>.git
```

(+ hub confere na Fase 1 se o acesso ao repo novo existe; + se a máquina é
antiga, conferir `git config --global core.autocrlf` — se vazio, setar `true`.)
Pular direto pra Fase 3, itens 3 e 4.

### Fase 3 — Cowork do dono (~5min)

1. Conectar `~/Desktop/ORQUESTRADOR/` no Cowork (**path tem que bater** com o clone).
2. Instalar o marketplace `plugin-mana-skills` no Cowork (ou, avulso: cockpit →
   card Skills → 📥 Copiar SKILL.md da `mana-memoria-operacional`).
3. Instalar a skill do agente dele + as do escopo (wf-ws se SOAP, akita).
4. Primeira conversa:
   ```
   semeia a memória operacional e configura o repo do <agente>
   ```
   → 5 seeds de memória + CLAUDE.md do dono na raiz do repo + instruções de
   projeto (dono cola em Projeto → instruções). **v1.3:** o Claude dele passa a
   consultar a **memória viva** (`memorias/_INDICE.md`) e conhece a **via de
   retorno** — aprendizado da máquina dele volta pro marketplace via commit.
5. Push do CLAUDE.md:
   `git add CLAUDE.md && git commit -m "chore: CLAUDE.md do dono" && git push`.

### Fase 4 — Smoke test (~10min)

1. *"Leia o CLAUDE.md e o SKILL.md do repo e me resuma seu escopo"*
2. *"Consulta a nota do agente e me diz o estado atual + pendências"*
3. Mudança trivial → dono aprova → push → deploy verde → /health OK
4. `ultima-revisao` da nota no mesmo push
5. Hub valida: Watch/aba Versionamento + deploy + health. **Teste de raio-x**
   (Dayan-2): se o Claude do dono descreve certo o que mudou e o que está
   pendente, a máquina está clonada.

---

## Critérios de sucesso do piloto (revisão +4 semanas)

Passa se TODOS: (1) ciclo completo ≥3× sem hub no meio; (2) zero drift
vault/Railway; (3) zero quebra de produção sem rollback <5min; (4) zero ADR sem
alinhamento. Falha parcial → ajustar e estender +4 semanas. Falha ≥3 → volta
pro modelo via-hub + ADR de retrospectiva.

---

## Gotchas acumulados (4 pilotos — 19 itens)

**Dayan-1:** (1) sandbox não autentica GitHub — git no Git Bash do dono;
(2) memória: usar o kit (auto-memory nativa pode não existir); (3) OneDrive;
(4) convite ANTES do clone.
**Lorena:** (5) username GitHub errado — confirmar o REAL; (6) `index.lock`
preso → fechar Cowork + `rm -f .git/index.lock`; (7) máquina usada → backup
.bak; (8) clone velho faz nota "sumir" → pull, NUNCA criar nota nova;
(9) não-dev remoto → 1 passo por vez.
**Dayan-2:** (10) sobras não commitadas da sessão morta → stash antes de pull;
(11) `deploy.sh`/`add -A` proibidos até reconciliar com o main; (12) sessões
paralelas criam "trabalho fantasma" → 1 motorista; (13) mount trunca arquivo
recém-editado → validar em /tmp; (14) endpoint protegido exige login no MESMO
navegador; (15) correções de contexto evitam retrabalho; (16) rede hub-compila.
**Pablo:** (17) **collaborator NUNCA cria repo** — nem com Repository creation
liberado; quem cria tem que ser Member (a config 1.3 só afeta Members);
(18) `gh` de outra conta na máquina (`propinova`) — `gh auth status` ANTES de
criar repo, senão o repo nasce na conta errada; (19) instrução ao dono tem que
ser UMA mensagem executável — "melhora esse repasse": duas instruções que não
se conversam (collaborator + liberar criação) queimaram uma tarde.

**Detalhe vivo dos gotchas de máquina:** memória viva da
`mana-memoria-operacional` (`memorias/_INDICE.md`) — CRLF fantasma, checkout
perigoso, gitignore dia 1, create_all, carga em lote.

---

## Recursos

- **POP imprimível:** `ManaVault/09-Runbooks/pop-passagem-bastao-dono-agente.md`
- **Skill irmã (instala no DONO):** `mana-memoria-operacional` v1.3 — memória
  viva + CLAUDE.md do repo
- **Cockpit:** card Skills (📥 Copiar SKILL.md) + aba Versionamento (acompanhar
  os pushes do dono sem abrir o GitHub)
- **Kit de automação:** `ManaVault/_kits/mana-onboarding/` (convidar-dev.sh,
  gerar-config.py, briefing-template, smoke-test-5-etapas)
- **Vault:** `10-Governanca/modelo-federado-construcao.md` ·
  `10-Governanca/clone-capacidade-cowork-dev.md` ·
  `09-Runbooks/criar-agente-novo-handoff-multi-maquina.md`

---
*v3.0.0 — 2026-08-09. Consolida as duas linhas que divergiram (v2 de
2026-07-03: 4 variações + Fase 3 rápida; ajustes Pablo de 2026-08-03: Member
vs Collaborator + repos privados + gh CLI) e adiciona: POP imprimível,
caminho VETERANO (Fase 2-V), autocrlf na Fase 2, memória viva v1.3 na Fase 3,
aba Versionamento na validação do hub, gotchas 17–19 do piloto Pablo.*
