---
name: onboarding-dono-agente
description: Setup completo para colocar colaborador (dev ou nao-dev) como dono de agente Mana no modelo multi-maquina (Cowork + GitHub + Railway + ManaVault). Use SEMPRE que onboardar membro da equipe Sementes Mana responsavel por agente especifico (Mana Price, agente-cpr, agente-nf, agente-comercial, agente-km, agente-documentos, etc.) OU quando criar agente novo com handoff (Xayer cria esqueleto via novo-agente-mana, dono herda). Cobre 4 fases (acessos GitHub/Railway, setup maquina, configurar Cowork, smoke test), variacao handoff de agente novo, templates CLAUDE.md customizado, memory modular em ORQUESTRADOR/memory/, briefing pronto pra novo dev, smoke test 5 etapas, criterios de piloto 4 semanas. Tambem quando mencionar: novo dev Mana, onboardar, multi-maquina, dono de agente, piloto Dayan, escalar manutencao, replicar piloto, adicionar dev, segundo dev, criar agente novo, agente do zero, handoff, Xayer cria Dayan herda, sync GitHub, vault compartilhado.
---

# Skill: Onboarding de Novo Dono de Agente (Multi-Máquina Maná)

> Procedimento validado para colocar um novo colaborador como dono de um agente Maná no modelo multi-máquina.
> **Origem:** piloto Dayan/agente-precificacao em 2026-05-20.
> **ADR:** `ManaVault/08-Decisoes/2026-05-19-piloto-multi-maquina-dayan-precificacao.md`
> **Runbook canônico:** `ManaVault/09-Runbooks/onboarding-novo-dev.md`

---

## Quando usar esta skill

- Um novo colaborador vai assumir responsabilidade por UM agente Maná
- Precisar replicar a arquitetura multi-máquina pra escalar manutenção
- Padronizar setup pra qualquer dev (não-dev usando Cowork como interface OU dev experiente)
- Substituir documentação dispersa por um fluxo único e validado

## Pré-decisões obrigatórias

Antes de invocar o procedimento, perguntar ao Xayer:

1. **Qual agente** sob responsabilidade do novo dev? (ex: agente-cpr, agente-nf, agente-comercial)
2. **Username GitHub** do novo dev?
3. **Email Railway** do novo dev?
4. **Push direto pra main ou via PR?** (Dayan teve direto; conservador é PR)
5. **Perfil técnico:** dev ou não-dev (Cowork como interface)?
6. **Background relevante** do dev (conhece negócio? veio do código?)
7. **Data de início do piloto** (geralmente hoje) — define revisão em +4 semanas

Sem essas respostas, **não prossiga** — vai gerar artefatos genéricos demais.

---

## Visão geral da arquitetura

```
Cada dev opera de máquina própria via Cowork (Claude desktop).

GitHub é o cérebro compartilhado:
- Sementesmana/<agente>       → código do agente
- Sementesmana/mana-vault     → vault (knowledge graph corporativo)

Sync on-demand pelo Cowork (NÃO Obsidian Git auto-commit/auto-pull):
- Antes de qualquer ação: git pull no vault + no agente
- Depois de qualquer mudança: git push em ambos

Push autônomo direto pra main (sem PR no padrão piloto Dayan).
Acesso de equipe (Collaborator GitHub + Member Railway + clone do vault).
Disciplina substitui trava física — convenção + monitoria.
```

---

## Procedimento (4 fases, ~1h total)

> ⚡ **Atalho — kit de automação `mana-onboarding`** (em `ManaVault/_kits/mana-onboarding/`, sincroniza via vault). Automatiza ~80% das fases abaixo, caindo de ~1h pra ~25-30min: `convidar-dev.sh` (convites GitHub + Watch via gh CLI), `gerar-config.py` (gera CLAUDE.md + memory + briefing de um config.json), `setup-dev.sh` (dev clona + estrutura). O passo a passo manual abaixo continua como referência e troubleshooting. Detalhes: `_kits/mana-onboarding/README.md`.

### Fase 1 — Xayer prepara acessos (~10min)

**1.1 GitHub — Member da Org OU collaborator por repo (decidir ANTES)**

> ℹ️ Desde 2026-06-24 `Sementesmana` é **GitHub Organization** (ADR `2026-06-24-sementesmana-virou-organization-github`). Owner: `xayer-mana`.

🚨 **A decisão mais importante da Fase 1 — e a que já queimou (Pablo, 2026-08-03):**

| | Collaborator por repo | **Member da Organization** |
|---|---|---|
| Como convida | `.../<repo>/settings/access` → Add people | `https://github.com/orgs/Sementesmana/people` → **Invite member** |
| Acessa | só os repos que você liberar | **todos** os repos (herda a Base permission = Read) |
| **Cria repo novo** | ❌ **NUNCA** — nem com Repository creation liberado | ✅ sim (se 1.3 estiver configurado) |

O GitHub é explícito: *"Outside collaborators can never create repositories."* Não existe configuração que libere.

**Regra prática:**
- Dono vai **só manter** agente existente (variação A/C) → collaborator por repo basta
- Dono vai **criar** agente novo (variação B/D, ou qualquer um que use `gh repo create`) → **tem que ser Member da Org**

Em qualquer dos dois casos, garantir acesso a:
- `mana-vault` (**sempre** — pré-requisito do contexto)
- `plugin-mana-skills` (**sempre** — marketplace; Write livre pra donos federados, decisão 2026-07-20)
- o(s) repo(s) do escopo dele

Ativar **Watch → All Activity** nos repos que importam (hub recebe notificação a cada push).

⚠️ Se o dono virar Member e a Base permission da Org for `Read`, ele passa a **ler todo o portfólio**. Decidir conscientemente — pra funcionário interno costuma ser aceitável; pra terceiro, não.

**1.2 Railway Member**

- Workspace level (sidebar) → **People** → **Invite Member**
- Email do dev → Role: **Member**
- Confirmar alertas de deploy ativos em **Settings → Notifications**

**1.3 Permitir que Members criem repositórios (1x pra Org inteira)**

> 🔑 **Só tem efeito sobre Members** (ver 1.1). Se o dono for outside collaborator, esta config não muda nada — ele continua sem conseguir criar repo.
> Por padrão, GitHub Orgs só deixam Owners criarem repos.

- `https://github.com/organizations/Sementesmana/settings/member_privileges`
- Seção **Repository creation** → marcar **Private** (padrão Maná, ADR `2026-08-03-repos-privados-por-padrao`)
- Salvar

Feito uma vez, vale pra todos os devs presentes e futuros.

> 🔒 **Repos Maná são PRIVADOS por padrão.** Público é exceção consciente com justificativa na nota do agente. Motivo: os repos carregam inteligência comercial (metas por cultivar, política de crédito, estrutura de integração) — não credenciais, mas o desenho da operação. Ver ADR.

**1.4 Ligar Secret scanning + Push protection (1x pra Org)**

- `https://github.com/organizations/Sementesmana/settings/security_analysis`
- **Secret scanning** → Enable all · **Push protection** → Enable all

O GitHub passa a **bloquear o push** que contenha chave/token/senha em formato reconhecido. É a rede de segurança que impede segredo de entrar no histórico (onde ficaria pra sempre).

### Fase 2 — Setup da máquina do novo dev (~20min)

**2.1 Instalações base**

1. **Cowork** (Claude desktop) — instalar e logar com conta dele
2. **Git for Windows** — durante o setup, marcar **"Git Credential Manager"** (vem com Git Bash + login GitHub persistido)
3. **GitHub CLI (`gh`)** — é o que dá **autonomia pra criar repositório novo por comando**, sem browser e sem copiar/colar arquivo na mão:
   ```bash
   winget install --id GitHub.cli
   ```
   Fechar e reabrir o Git Bash depois de instalar (pra o PATH atualizar).
4. Configurar Git no Git Bash:
   ```bash
   git config --global user.name "Nome do Dev"
   git config --global user.email "email@dominio.com"
   ```

**2.1b Autenticar o `gh` (1x por máquina)**

```bash
gh auth login
#   → GitHub.com
#   → HTTPS
#   → Authenticate Git with your GitHub credentials? Yes
#   → Login with a web browser  (copia o código, cola no browser que abrir)

gh auth status   # confirma: "Logged in to github.com as <username>"
```

> Sem `gh` autenticado, o Claude do dev não consegue criar repo por comando — ele acaba mandando o dev criar no browser e colar arquivo por arquivo. Com `gh`, vira 1 comando (ver `novo-agente-mana`, seção de publicação).

**2.2 Aceitar convites**

O dev aceita os emails de convite (GitHub Collaborator x N repos + Railway Member). **IMPORTANTE:** sem aceitar o convite GitHub, o `git clone` retorna "Repository not found".

**2.3 Clonar repos**

```bash
mkdir -p ~/Desktop/ORQUESTRADOR
cd ~/Desktop/ORQUESTRADOR
git clone https://github.com/Sementesmana/mana-vault.git ManaVault
git clone https://github.com/Sementesmana/<agente>.git
```

Na primeira clonagem, GCM abre browser pedindo login GitHub. Dev autoriza. Depois fica salvo.

> ⚠️ **OneDrive + Git é antipattern.** Se o Desktop do dev está sincronizado com OneDrive (caminho tipo `OneDrive/Área de Trabalho/`), considere mover ORQUESTRADOR pra fora (`C:\Users\<dev>\ORQUESTRADOR\`). OneDrive pode bloquear arquivos enquanto Git mexe e em casos raros corromper o `.git/`. Não bloqueia setup mas vira TODO de segurança.

### Fase 3 — Configurar Cowork (~20min)

**3.1 Conectar pasta ao Cowork**

Cowork pede pra conectar uma pasta. Dev seleciona a raiz `~/Desktop/ORQUESTRADOR/` (onde estão `ManaVault/` e `<agente>/`).

> ⚠️ **Verificar path absoluto.** Cowork pode criar/conectar a uma pasta DIFERENTE de onde o dev clonou. Sempre confirmar que o path do Cowork bate com o path do clone. Se divergir → mover arquivos ou reconectar.

**3.2 Colocar CLAUDE.md customizado**

Use `templates/CLAUDE-template.md` da skill. Customize os placeholders. Salve em `~/Desktop/ORQUESTRADOR/CLAUDE.md` na máquina do dev (não no vault — é local de cada dev).

**3.3 Configurar memory inicial modular**

O Cowork do dev cria estrutura local em `~/Desktop/ORQUESTRADOR/memory/` baseada em `templates/memory-modular-template.md`:

```
ORQUESTRADOR/memory/
├── MEMORY.md                       (índice)
├── user_<dev>.md                   (perfil)
├── regras_criticas.md              (7 regras inegociáveis)
├── feedback_linguagem_negocio.md   (traduzir técnico→negócio)
├── project_piloto_<agente>.md      (piloto + critérios)
├── comunicacao_xayer.md            (WhatsApp/Inbox/ADR)
├── stack_<agente>.md               (stack do agente)
└── documentos_mestre.md            (paths do vault)
```

CLAUDE.md instrui Claude a ler `memory/MEMORY.md` no início de cada sessão. É "auto-load via convenção de prompt" — não auto-memória nativa do Cowork (que pode não existir nessa instalação).

**3.4 Instalar skills no Cowork do dev**

Instalar APENAS skills relevantes ao escopo (NÃO instalar skills de outros agentes):

| Skill | Necessidade |
|---|---|
| `<agente-do-dev>` | ESSENCIAL — base de conhecimento |
| `obsidian-manavault` | ESSENCIAL — disciplina do vault |
| `softexpert-wf-ws` | Se agente integra SOAP SoftExpert |
| `akita` | RECOMENDADO — segurança |
| `docx`, `xlsx`, `pdf` | Conforme necessidade |

### Fase 4 — Smoke test (~10min)

Procedimento completo em `templates/smoke-test-5-etapas.md`. Resumo:

1. **Validar contexto carregado** — *"Leia o CLAUDE.md e me resuma seu escopo"*
2. **Validar leitura do vault** — *"Consulta a nota do <agente> e me resume 3 pontos"* (Cowork faz git pull + lê + reporta hash)
3. **Mudança trivial no código** — adicionar comentário; Cowork explica em linguagem de negócio → dev aprova → push
4. **Atualizar nota do vault** — `ultima-revisao` + push no vault
5. **Xayer valida** — GitHub watch (2 commits) + Railway deploy verde + health endpoint OK

---

## Critérios de sucesso do piloto (revisão em 4 semanas)

Piloto **passa** se TODOS forem atendidos:

1. Ciclo completo executado **≥3 vezes** sem envolver Xayer no meio
2. **Zero drift** entre vault e Railway
3. **Zero quebra de produção** sem rollback em <5min
4. **Zero ADR sem alinhamento**

**Se passa:** modelo vira padrão replicável.
**Se falha parcialmente (1-2 critérios):** ajustar (push via PR? mais skills? check-in semanal?) e estender piloto +4 semanas.
**Se falha em ≥3 critérios:** reverter dev pra modelo "via Xayer" e abrir ADR de retrospectiva.

---

## Briefing pronto pra mandar pro novo dev

Use `templates/briefing-template.md`. Substitua placeholders (`<NOME_DO_DEV>`, `<NOME_AGENTE>`, etc.) e envie via WhatsApp/Drive/email.

---

## Variação: Criar agente NOVO com handoff

> Quando o dono potencial (Dayan, ou futuro dev) **propõe um agente Maná NOVO** (não migração de agente existente).

**Princípio:** Xayer cria o esqueleto (limitação: `Sementesmana` é conta pessoal GitHub, só ele cria repos), dono herda via mesmos artefatos.

**Divisão:**
- **Xayer (~30min):** repo GitHub + projeto Railway + scaffold via skill `novo-agente-mana` + nota no vault + convite Collaborator + Watch
- **Dono (~15min):** clona repo + atualiza CLAUDE.md + atualiza memory + smoke test

**Quando usar:** dono propõe agente novo, modelo multi-máquina vigente.

**Quando NÃO usar:**
- Single-dev (usa só `novo-agente-mana` direto)
- Xayer vai ser dono do agente novo (sem handoff)
- Agente experimental (não vale overhead)

**Detalhes operacionais:** `templates/criar-novo-agente-handoff.md` (resumo) + runbook canônico `ManaVault/09-Runbooks/criar-agente-novo-handoff-multi-maquina.md` (passo a passo completo).

**Decisão arquitetural:** `ManaVault/08-Decisoes/2026-05-20-handoff-criacao-agente-xayer-cria-dev-herda.md` (rationale + alternativas consideradas).

---

## Limitações operacionais conhecidas

5 pontos que mordem (detalhes em `references/lessons-learned-piloto-dayan.md`): (1) Cowork sandbox não autentica GitHub — git roda no Git Bash do dev, Cowork só prepara comandos; (2) auto-memory nativa pode não existir — usar memory modular em `ORQUESTRADOR/memory/`; (3) OneDrive sincroniza Desktop por padrão — usar `~/ORQUESTRADOR`; (4) convite GitHub aceito ANTES do clone (senão "Repository not found"); (5) `Sementesmana` é conta pessoal — Collaborator por repo, não Org Member.

---

## Recursos da skill

```
onboarding-dono-agente/
├── SKILL.md (este arquivo)
├── templates/
│   ├── CLAUDE-template.md
│   ├── memory-modular-template.md
│   ├── briefing-template.md
│   ├── smoke-test-5-etapas.md
│   └── criar-novo-agente-handoff.md      ← variação agente novo
└── references/
    └── lessons-learned-piloto-dayan.md
```

---

## Documentos relacionados no ManaVault

- **ADR piloto multi-máquina:** `ManaVault/08-Decisoes/2026-05-19-piloto-multi-maquina-dayan-precificacao.md`
- **ADR handoff de criação:** `ManaVault/08-Decisoes/2026-05-20-handoff-criacao-agente-xayer-cria-dev-herda.md`
- **Runbook onboarding existente:** `ManaVault/09-Runbooks/onboarding-novo-dev.md`
- **Runbook criação handoff:** `ManaVault/09-Runbooks/criar-agente-novo-handoff-multi-maquina.md`
- **Inbox: drift Sementesmana:** `ManaVault/00-Inbox/2026-05-19-drift-sementesmana-personal-account.md`
- **Disciplina do vault:** skill `obsidian-manavault`
- **Padrões de segurança:** skill `akita`
- **Scaffold agente novo:** skill `novo-agente-mana` (centralizada no Cowork do Xayer — usada na variação handoff)
