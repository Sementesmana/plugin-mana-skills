---
name: onboarding-dono-agente
description: >-
  Setup completo para colocar colaborador (dev ou nao-dev) como dono de agente
  Mana no modelo multi-maquina (Cowork + GitHub + Railway + ManaVault). Use
  SEMPRE que onboardar dono de agente Sementes Mana, passar bastao, repassar
  agente, ou CONTINUAR um piloto pelo hub (creditos do dono acabaram / dono
  travado). Cobre as 4 fases (acessos, setup maquina, Cowork, smoke test),
  as 4 variacoes de handoff (migrar existente; dono propoe agente novo;
  build-then-handoff; continuacao-pelo-hub), dono nao-dev, padrao do
  intermediario (1 passo de cada vez), kit mana-memoria-operacional
  (CLAUDE.md do dono + memoria semeada em 1 install), correcoes de contexto
  do hub, rede de seguranca hub-compila. Pilotos: Dayan/precificacao,
  Lorena/auditoria-ponto, Dayan-2/comercio-revendas. Tambem quando mencionar:
  passagem de bastao, multi-maquina, replicar piloto, segundo dev, handoff,
  sync GitHub, vault compartilhado, index.lock, stash antes de pull, drift
  de sessoes paralelas, semeia a memoria operacional.
---

# Skill: Onboarding de Novo Dono de Agente (Multi-Máquina Maná) — v2

> Procedimento validado para colocar um novo colaborador como dono de um agente Maná.
> **Pilotos validados:**
> - 1º — **Dayan / agente-precificacao** (2026-05-20) — dono **dev**, agente novo proposto pelo dono.
> - 2º — **Lorena / agente-auditoria-ponto** (2026-06-11) — dono **não-dev**, **build-then-handoff**.
> - 3º — **Dayan-2 / agente-comercio-revendas** (2026-07-03) — **continuação-pelo-hub** + kit
>   `mana-memoria-operacional` (novo caminho rápido das Fases 3).
> **ADRs:** `08-Decisoes/2026-05-19-piloto-multi-maquina-dayan-precificacao` ·
> `2026-06-11-handoff-agente-auditoria-ponto-lorena` · `2026-06-24-sementesmana-virou-organization-github`

---

## Quando usar

- Novo colaborador vai assumir UM agente Maná (qualquer perfil: dev ou não-dev)
- Continuar um piloto pelo hub quando o dono travou (créditos, máquina, bug)
- Replicar a arquitetura multi-máquina / padronizar setup

## Quem conduz — hub OU o próprio dono (auto-condução)

Esta skill serve pros dois. **O dono pode se auto-conduzir** nas Fases 2, 3 e 4
(máquina, Cowork, smoke test) — são todas executáveis por ele. A ÚNICA coisa que
exige o hub é a **Fase 1** (convites GitHub/Railway — só admin da org convida).

**Auto-condução:** o dono instala esta skill + a `mana-memoria-operacional`, e manda
UMA mensagem ao hub pedindo exatamente isto:
```
Preciso de acesso pra assumir o <agente>:
1. GitHub: Collaborator (Write) em Sementesmana/<agente> e Sementesmana/mana-vault
   — meu username REAL é: <username>
2. Railway: convite Member — meu email: <email>
3. Ativa o Watch → All Activity nos repos (pro teu acompanhamento)
```
Recebeu os convites e aceitou → segue as Fases 2-4 sozinho com o Claude dele.
Claude do dono: ao conduzir, siga o padrão 1-passo-por-vez com critério de
"deu certo" observável em cada passo.

## Pré-decisões obrigatórias (perguntar ao hub antes)

1. **Qual agente**? 2. **Username GitHub REAL** do dono (confirmar — erro aqui dá acesso
a repo privado pra pessoa errada)? 3. **Email Railway**? 4. **Push direto ou PR**?
5. **Perfil:** dev ou não-dev? 6. **Background**? 7. **Data de início** (revisão +4 semanas).

## As 4 variações de handoff

| Variação | Quando | Engenharia | Validado em |
|---|---|---|---|
| **A — Migrar existente** | Agente em produção muda de dono | já existe | (padrão base) |
| **B — Agente novo com handoff** | Dono propõe agente novo | dono propõe, hub cria esqueleto | Dayan/precificacao |
| **C — Build-then-handoff** | Hub constrói+valida em prod, depois repassa | hub faz tudo | Lorena/auditoria-ponto |
| **D — Continuação-pelo-hub** | Dono travou no meio (créditos/máquina); hub assume a EXECUÇÃO mantendo o dono nas DECISÕES | hub executa, dono decide | **Dayan-2/comercio-revendas** |

### Variação D — Continuação-pelo-hub (novo, 2026-07-03)

Quando o Cowork do dono para no meio do trabalho (créditos acabaram, sessão estourou, VM fora):

1. **Dono manda o contexto** — export/Word da última sessão dele + logs. O hub lê TUDO antes de agir.
2. **Hub executa, dono decide** — toda decisão de produto/negócio continua sendo do dono
   (por mensagem relayada). O hub não muda escopo por conta própria.
3. **Cuidado nº 1: sobras não commitadas na máquina do dono.** A sessão que morreu
   provavelmente deixou edições soltas. Quando o dono voltar: `git status` → `git stash`
   → `git pull` (NUNCA pull por cima de árvore suja; NUNCA `deploy.sh`/`add -A` antes
   do pull — empurra código velho por cima da produção).
4. **Cuidado nº 2: um motorista por vez.** Se o hub e a máquina do dono (ou 2 chats) mexem
   no mesmo repo em paralelo, aparece "trabalho fantasma" não commitado. Ao detectar drift
   inesperado no working tree → PARAR e perguntar quem está dirigindo.
5. **Devolução do bastão:** dono roda `git stash && git pull`, e o hub manda as
   **correções de contexto** (ver seção abaixo) pro Cowork do dono não refazer trabalho.

**Correções de contexto (padrão validado):** mensagem única que o dono cola no Cowork dele
listando: commits que JÁ estão no main (hash + o quê), o que JÁ foi validado em produção
(logs/valores), pendências que já fecharam, e a próxima tarefa. Sem isso o Claude do dono
re-propõe trabalho feito.

**Rede de segurança hub-compila:** quando o Claude do dono edita código sem conseguir
validar (VM fora), o dono pusha → o hub roda `git pull` no clone dele → `py_compile` +
smoke → "verde" ou fix imediato. Custa 30s e evita produção quebrada no boot.

## Dono não-dev — ajustes (validado Lorena)

- **1 passo de cada vez**, cada um com critério de "deu certo" observável.
- **Padrão do intermediário:** dono remoto → hub pede o passo ao Claude, repassa por
  WhatsApp, dono executa e devolve o output (print/paste).
- **CLAUDE.md em linguagem de negócio** — dono decide o "o quê".
- **Tudo copy-paste:** comandos completos com `cd` embutido, um bloco por passo.

---

## Arquitetura

```
Cada dono opera da própria máquina via Cowork.
GitHub = cérebro compartilhado (Sementesmana = ORGANIZATION desde 2026-06-24):
  Sementesmana/<agente>    → código + CLAUDE.md do dono + SKILL.md (nota canônica)
  Sementesmana/mana-vault  → vault (ADRs, runbooks, transversal)
Sync on-demand: pull antes de mexer, push depois. 1 motorista por solução.
Deploy: git push → Railway auto-deploya (~2min). NUNCA railway up.
```

---

## Procedimento (4 fases)

> ⚡ **Caminho rápido (desde 2026-07-03):** a Fase 3 caiu de ~20min pra ~5min com o kit
> **`mana-memoria-operacional` v1.2** do cockpit — 1 install + 1 frase substitui o
> CLAUDE.md manual + memory modular manual. O kit `mana-onboarding`
> (`ManaVault/_kits/mana-onboarding/`) segue automatizando a Fase 1 (convites via gh CLI).

### Fase 1 — Hub prepara acessos (~10min)

**1.1 GitHub** — `Sementesmana` é **Organization**: convidar como Collaborator (Write) nos
repos do escopo — `https://github.com/Sementesmana/<agente>/settings/access` — ou Member
da org se o dono vai ter vários repos. **Sempre** incluir `mana-vault`. Ativar
**Watch → All Activity** em cada repo (hub recebe notificação de push).

**1.2 Railway** — Workspace → People → Invite (email, role Member — na prática Deployer).

### Fase 2 — Máquina do dono (~20min)

1. **Cowork** logado na conta dele; **Git for Windows** com Git Credential Manager.
2. `git config --global user.name "..."` e `user.email "..."` no Git Bash.
3. **Aceitar os convites** (GitHub + Railway) ANTES do clone (senão "Repository not found").
4. Clonar:
   ```bash
   mkdir -p ~/Desktop/ORQUESTRADOR && cd ~/Desktop/ORQUESTRADOR
   git clone https://github.com/Sementesmana/mana-vault.git ManaVault
   git clone https://github.com/Sementesmana/<agente>.git
   ```
5. ⚠️ **OneDrive + Git é antipattern** — se o Desktop sincroniza com OneDrive, usar
   `C:\Users\<dev>\ORQUESTRADOR\`.
6. ⚠️ **Máquina já usada:** backup de CLAUDE.md/memory antigos (`.bak`) antes do novo setup.

### Fase 3 — Cowork do dono (~5min, caminho novo)

1. Conectar a pasta `~/Desktop/ORQUESTRADOR/` no Cowork (**conferir que o path bate** com o clone).
2. Cockpit (`painel-monitor .../portfolio`) → card Skills → **`mana-memoria-operacional`**
   → 📥 Copiar SKILL.md → Cowork > Personalizar > Habilidades > Adicionar.
3. Instalar também a skill do agente dele (se existir) e as do escopo (wf-ws se SOAP, akita).
4. Primeira conversa no Cowork:
   ```
   semeia a memória operacional e configura o repo do <agente>
   ```
   → cria os 5 seeds de memória + CLAUDE.md do dono na raiz do repo + texto das
   instruções de projeto. Dono cola as instruções em Projeto → instruções.
5. Push do CLAUDE.md: `git add CLAUDE.md && git commit -m "chore: CLAUDE.md do dono" && git push`.

*(Caminho manual antigo — CLAUDE-template + memory modular — continua nos templates da
skill fonte, como fallback/troubleshooting.)*

### Fase 4 — Smoke test (~10min)

1. *"Leia o CLAUDE.md e o SKILL.md do repo e me resuma seu escopo"*
2. *"Consulta a nota do agente e me diz o estado atual + pendências"* (valida contexto)
3. Mudança trivial → dono aprova → push → Railway deploy verde → /health OK
4. Atualizar `ultima-revisao` da nota (mesmo push)
5. Hub valida: watch (commits) + deploy + health. **Extra validado no Dayan-2:** teste de
   raio-x — se o Claude do dono descreve corretamente o que mudou e o que está pendente,
   a máquina está clonada.

---

## Critérios de sucesso do piloto (revisão +4 semanas)

Passa se TODOS: (1) ciclo completo ≥3× sem hub no meio; (2) zero drift vault/Railway;
(3) zero quebra de produção sem rollback <5min; (4) zero ADR sem alinhamento.
Falha parcial → ajustar e estender +4 semanas. Falha ≥3 → volta pro modelo via-hub + ADR retrospectiva.

---

## Limitações e gotchas acumulados (3 pilotos)

**Dayan-1:** (1) sandbox não autentica GitHub — git no Git Bash do dono; (2) memória:
usar o kit do cockpit (auto-memory nativa pode não existir); (3) OneDrive; (4) convite
antes do clone.
**Lorena:** (5) username GitHub errado — confirmar o real; (6) `index.lock` preso →
fechar Cowork + `rm -f .git/index.lock`; (7) máquina usada → backup .bak; (8) clone
velho faz nota "sumir" → pull do origin, NUNCA criar nota nova; (9) não-dev remoto →
1 passo por vez.
**Dayan-2 (2026-07-03):** (10) sobras não commitadas da sessão morta → stash antes de
pull; (11) `deploy.sh`/`add -A` proibidos até a árvore estar reconciliada com o main;
(12) sessões/chats paralelos criam "trabalho fantasma" → 1 motorista, parar ao detectar
drift; (13) mount trunca arquivo recém-editado → validar em /tmp (detalhe na skill
`mana-memoria-operacional`); (14) endpoint protegido exige login no MESMO navegador
(cookie httponly) — "abrir logado"; (15) correções de contexto do hub evitam retrabalho;
(16) rede de segurança hub-compila quando a VM do dono está fora.

---

## Recursos

- **Esta skill no cockpit:** card Skills → `onboarding-dono-agente` (📥 Copiar SKILL.md).
- **Skill irmã (instala no DONO):** `mana-memoria-operacional` v1.2 — memória + CLAUDE.md.
- **Templates/references completos:** skill fonte no Cowork do hub + `ManaVault/_kits/mana-onboarding/`
  (convidar-dev.sh, gerar-config.py, briefing-template, smoke-test-5-etapas,
  lessons-learned dos pilotos).
- **Vault:** `10-Governanca/clone-capacidade-cowork-dev.md` (as 7 camadas) ·
  `10-Governanca/modelo-federado-construcao.md` · `09-Runbooks/repo-vizinho-como-referencia.md`.

---
*v2.0.0 — 2026-07-03. Mudanças: Sementesmana é Organization (corrige drift);
variação D continuação-pelo-hub; Fase 3 via mana-memoria-operacional (20→5min);
correções de contexto + rede hub-compila; gotchas do piloto Dayan-2. Publicada
no cockpit pra hub e futuros condutores de handoff.*
