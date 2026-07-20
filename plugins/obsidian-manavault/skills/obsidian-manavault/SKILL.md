---
name: obsidian-manavault
description: "Cérebro estruturado da Sementes Maná em Obsidian. Vault knowledge graph com hiperautomação 3 níveis (N1/N2/N3), 16 agentes em produção, ADRs imutáveis, runbooks e pesquisa genética (34 cultivares de soja). Sync GitHub via Obsidian Git (OAuth/GCM, auto-commit 10min). Use SEMPRE que mexer no ManaVault — adicionar nota, popular variedade, criar ADR, atualizar agente, configurar plugin, CSS cores, color groups graph, separar knowledge×behavior. Também quando mencionar: ManaVault, vault Obsidian, pesquisa-genetica, portfolio-cultivares, system-prompt agronomo, libraries-meta, ADR Maná, frontmatter rico, Dataview, CSS snippet manavault-cores, Obsidian Git OAuth, knowledge×behavior, build-time export."
---

# ManaVault — Cérebro Estruturado da Sementes Maná LTDA

> Vault Obsidian que serve como **fonte canônica única** do conhecimento corporativo da Maná. Espelha a arquitetura completa de hiperautomação (N1/N2/N3), todos os 16 agentes em produção, 34 cultivares de soja com cross-links, decisões arquiteturais imutáveis (ADRs) e regras de governança.

---

## Quando usar esta skill

- "Adicionar nota X no vault" / "Criar ADR" / "Documentar decisão" → use
- "Popular variedade de soja Y" / "Atualizar portfolio-cultivares" → use
- "Como organizar o vault?" / "Disciplina do vault" → use
- "Cores do Obsidian estão erradas" / "Color groups do graph" → use
- "Sync GitHub do vault" / "Plugin Obsidian Git" → use
- "Knowledge vs behavior" / "Onde fica o system-prompt do bot" → use
- "Frontmatter da nota" / "Dataview query no vault" → use
- "Build-time export" / "Caminho 1 GitHub Action" → use

---

## Localização

**Filesystem:** `C:\Users\Sementes Mana\Desktop\ORQUESTRADOR\ManaVault\`
**GitHub:** `Sementesmana/mana-vault` (private repo)
**Sync:** plugin Obsidian Git (Vinzent03) — auto-commit/push 10min, auto-pull 30min, OAuth via Git Credential Manager (não usa PAT-in-URL)

---

## Estrutura macro — 11 pastas + dashboard

```
ManaVault/
├── HOME.md                              ← dashboard navegável
├── README.md
├── _Templates/                          ← 7 templates (ADR, agente, framework, API, processo, runbook, dicionário)
├── 00-Inbox/                            ← capturas a triar
├── 01-Estrategia-e-Modelos-de-Negocio/  ← Playing to Win, BMC, OKRs
├── 02-Cadeia-de-Valor/                  ← Apoio + Negócio + Gestão
│   └── 02-Processos-Negocio/
│       └── pesquisa-genetica/           ← KNOWLEDGE canônico portfólio Maná
├── 03-Sistemas/                         ← Protheus, Simple Agro, SoftExpert
├── 04-Frameworks-e-Metodologias/        ← BSC, BPMN, COSO, ISOs (a popular)
├── 05-Hiperautomacao/                   ← N1, N2, N3 (IA transversal)
├── 06-Agentes-e-Skills/                 ← 16 agentes em produção + libraries-meta
├── 07-Agentes-Pesquisadores/            ← camada meta (futuro)
├── 08-Decisoes/                         ← 4 ADRs principais (imutáveis)
├── 09-Runbooks/                         ← procedimentos validados
└── 10-Governanca/                       ← chapéu CTIO
```

---

## Princípio fundador: Single Source of Truth

Vault é **fonte canônica única**. Quando há divergência entre vault e código/produção:
- Se vault está mais novo → **vault é a verdade**, código será atualizado via build-time export (Caminho 1, futuro GitHub Action)
- Se realidade está mais nova que vault → **drift detectado, sinalizar a Xayer ANTES de prosseguir**

Agentes pesquisadores (futuro) alimentam SOMENTE o vault. Vault propaga pra repos via build-time export.

---

## Princípio: Knowledge × Behavior (separação obrigatória)

```
KNOWLEDGE (o que o bot SABE) → vault em
   02-Cadeia-de-Valor/02-Processos-Negocio/pesquisa-genetica/
   (conteúdo: 34 variedades de soja, microrregiões, tecnologias, nematoides, doenças, manejo)

BEHAVIOR (como o bot AGE) → vault em
   06-Agentes-e-Skills/agente-X/system-prompt.md
   (conteúdo: identidade, regras de recomendação, tom, limitações)
```

**Adicionar variedade nova** → editar **knowledge** (`pesquisa-genetica/variedades/`)
**Mudar tom/regras de resposta** → editar **behavior** (`06-Agentes-e-Skills/agente-X/system-prompt.md`)

System prompt operacional vive no código do repo — futuramente sincronizado via build-time export.

---

## Disciplina obrigatória — REGRAS INEGOCIÁVEIS

```
Antes de mexer em agente  →  ler nota dele em 06-Agentes-e-Skills/agente-X.md
Durante                    →  consultar ADRs (08-Decisoes/) e frameworks (04-)
Depois de mexer           →  atualizar nota (ultima-revisao + seções afetadas)
Decisão arquitetural      →  criar ADR em 08-Decisoes/YYYY-MM-DD-titulo.md
Captura solta             →  jogar em 00-Inbox/
Drift detectado           →  sinalizar a Xayer ANTES de prosseguir
```

**ADRs são imutáveis.** Se mudou de ideia, criar novo ADR que `supersede` o anterior. Nunca editar ADR antigo.

---

## Tipos de nota e frontmatter

Cada nota tem `tipo:` no frontmatter, que indica o esquema esperado:

### `tipo: agente` (06-Agentes-e-Skills/agente-X.md)

```yaml
---
tipo: agente
nome: agente-X
selo-agente:
  loop-autonomo: bool        # tem loop autônomo?
  estado-persistente: bool   # mantém estado entre invocações?
  decisao-proxima-acao: bool # decide o que fazer depois?
nivel-hiperautomacao: 1|2|3
autoridade: sugere|age|decide
status: producao|deploy|backlog
deploy: railway
github: Sementesmana/agente-X
url-producao: https://...
ultima-revisao: YYYY-MM-DD
tags: [...]
---
```

### `tipo: variedade` (pesquisa-genetica/variedades/X.md)

```yaml
---
tipo: variedade
nome: NEO680 IPRO
codigo: NEO680
fabricante: Mana|Neogen|Bayer
gm: 6.8
ciclo-dias: 108                       # ou range "108-115"
pmg-gramas: 163
flor: roxa|branca
ramificacao: baixo|medio|alto
tecnologia: IPRO|I2X|CE|ENLIST-E3|STS
sts: bool                              # tem tolerância a sulfonilureias?
ncisto: S|R|MR
ncisto-racas: [3, 9, 14]               # quais raças (se R/MR)
ncisto-mr-racas: [9, 10]               # raças onde é MR (parcial)
ngalha: S|R|MR
nreniforme: S|R|MR
nlesoes: S|R|MR
microregioes-recomendadas: [M3, M4, M5, MATOPIBA]
fortes: [...]
fracos: [...]
status: ativo|contexto-comparativo|descontinuado
no-portfolio-mana: bool                # se false → bot NÃO recomenda
ultima-revisao: YYYY-MM-DD
tags: [variedade, ...]
---
```

### `tipo: adr` (08-Decisoes/YYYY-MM-DD-titulo.md)

```yaml
---
tipo: adr
status: vigente|substituido
data: YYYY-MM-DD
supersede: [adr-anterior]              # se for substituição
substituido-por: [adr-novo]            # se foi substituído
ultima-revisao: YYYY-MM-DD
tags: [adr, ...]
---
```

### Outros tipos

`tipo: index` (pasta), `tipo: framework`, `tipo: api`, `tipo: processo`, `tipo: runbook`, `tipo: dicionario-tabela`, `tipo: system-prompt`, `tipo: redirect` (stub que aponta pra outra nota).

---

## Convenção de wiki-links

Sempre relativos ao path da nota atual:

```markdown
<!-- de variedades/NEO680-IPRO.md, linkando pra microrregião M3 -->
[[../microregioes/M3-Brasil-Central|M3]]

<!-- de 06-Agentes-e-Skills/agente-agronomo.md linkando pra agente-router -->
[[agente-router]]

<!-- de pesquisa-genetica/_index.md linkando pra agente-agronomo -->
[[../../../06-Agentes-e-Skills/agente-agronomo]]
```

Pipe `|` permite alias visual (texto exibido) diferente do path.

---

## Estado canônico atual (2026-05-03)

### Pesquisa Genética — 34 cultivares populadas

**Portfólio Maná (20) — bot RECOMENDA** (`status: ativo`, `no-portfolio-mana: true`):

Maná: ST711-I2X ⭐, ST745-I2X, ST828-I2X
Neogen comercializadas pela Maná: NEO680-IPRO, NEO690-I2X, NEO700-I2X, NEO760-CE, NEO761-I2X, NEO771-I2X, NEO780-CE, NEO790-IPRO, NEO791-CE, NEO800-I2X, NEO802-I2X, NEO821-I2X, GNS-7901-IPRO ★
Bayer comercializadas pela Maná: 76KA72, 78KA42, 80KA72, 84KA92 ★

**Contexto comparativo (14) — bot NÃO recomenda** (`status: contexto-comparativo`):

Neogen (8): NEO550-I2X, NEO640-I2X, NEO720-I2X, NEO801-CE, NEO810-I2X, NEO811-I2X, NEO820-IPRO, NEO840-IPRO
Bayer (6): 53KA33, 60KA32, 62EA12, 68KA49, 71KA72, 79KA72

Toda concorrente tem bloco "Alternativa equivalente Maná" no fim — facilita o bot trocar a recomendação.

### 16 agentes em produção (todos com nota em 06-Agentes-e-Skills/)

Gateways (entrada/saída WhatsApp): agente-router, agente-whatsapp
Connectors (sistemas): agente-pedidos, agente-protheus
Skills de geração: agente-cpr, agente-nf, agente-documentos
Apps: agente-km, agente-precificacao
Services: agente-agro
Dashboards N2: agente-monitor, agente-financeiro-sa, agente-estoque
Chatbots: agente-comercial, agente-agronomo, agente-whatsapp-pa

### Libraries-meta (skills meta — não agentes de produção)

Em `06-Agentes-e-Skills/libraries-meta/`:
- `akita.md` — princípios de arquitetura defensiva
- `softexpert-orchestrator.md` — biblioteca SOAP reutilizável
- `novo-agente-mana.md` — gerador/scaffold de novos agentes

### 4 ADRs principais em 08-Decisoes/

1. `2026-05-02-vault-como-cerebro-estruturado` — fundação
2. `2026-05-02-arquitetura-3-niveis-hiperautomacao` — N1/N2/N3
3. `2026-05-02-saneamento-monorepo-9-migracoes` — saneamento completo (monorepo extinto)
4. `2026-05-02-caminho-A-padrao-migracao` — Caminho A (trocar Source mantendo URL)

---

## Customização visual aplicada

### CSS Snippet — cores na sidebar

Arquivo: `.obsidian/snippets/manavault-cores.css`
Status: ✅ ativo (Settings → Aparência → CSS snippets → manavault-cores ON)

Cores por camada:
| Pasta | Cor | Hex |
|---|---|---|
| 01 Estratégia | Ouro Maná | `#B8860B` |
| 02 Cadeia de Valor | Verde Maná | `#1D6B3E` |
| 03 Sistemas | Azul | `#2563eb` |
| 04 Frameworks | Roxo | `#7c3aed` |
| 05 Hiperautomação | Laranja | `#ea580c` |
| 06 Agentes | Verde-azulado | `#0d9488` |
| 07 Pesquisadores | Magenta | `#c026d3` |
| 08 Decisões (ADRs) | Vermelho | `#b91c1c` |
| 09 Runbooks | Marrom | `#92400e` |
| 10 Governança | Grafite | `#1e293b` |
| _Templates | Ciano | `#0891b2` |
| 00 Inbox | Cinza claro | `#64748b` |

Aplica `border-left: 3px solid var(--mv-X)` + nome em cor + bold.

Pastas especiais com fundo tingido: `pesquisa-genetica/` (KNOWLEDGE), `agente-agronomo/` (BEHAVIOR), `libraries-meta/`.

### Graph View — Color Groups

Arquivo: `.obsidian/graph.json`
Configurados 12 color groups com mesmas cores via path query:

```json
{ "query": "path:\"01-Estrategia-e-Modelos-de-Negocio\"", "color": { "a": 1, "rgb": 12091915 } }
```

Onde `rgb` é o valor hex convertido pra integer. Reiniciar Obsidian após editar `graph.json` pra carregar.

---

## Setup do Obsidian Git Plugin

Plugin instalado: **Vinzent03/obsidian-git** (Plugins não oficiais → Buscar → "Git" → Instalar → Ativar)

Configuração atual:
- Auto-commit/push: **10 min**
- Auto-pull: **30 min**
- Auth: OAuth via Git Credential Manager (NÃO usa PAT-in-URL)
- Vault sincronizado: `Sementesmana/mana-vault` (private)

### Setup OAuth (uma vez)

1. Plugin Git → Settings → "Authentication" → escolher autenticar via GCM
2. Primeiro push abre popup do navegador → autorizar como Sementesmana
3. GCM armazena token no Windows Credential Manager
4. Cache permanente — não precisa repetir

Se o popup OAuth não abrir, limpar credenciais antigas:
```cmd
cmdkey /list                                     # ver entradas
cmdkey /delete:LegacyGeneric:target=git:https://github.com
```
Próximo `git push` aciona popup correto.

### Não confundir

- **Auth via GCM** (necessário): faz commit/push/pull funcionar
- **"Connect to GitHub" no plugin** (opcional): integração com GitHub Issues/PRs no Obsidian — feature secundária, pode ignorar

---

## Templates em `_Templates/`

7 templates pré-prontos (com frontmatter rico):

- `nota-agente.md` — esqueleto de agente em produção
- `nota-framework.md` — esqueleto de framework/metodologia (BSC, BPMN, etc)
- `nota-api.md` — esqueleto de API externa (SOAP/REST)
- `nota-processo.md` — esqueleto de processo de negócio (BPMN)
- `nota-runbook.md` — esqueleto de procedimento operacional
- `nota-dicionario-tabela.md` — esqueleto de tabela de banco
- `nota-adr.md` — esqueleto de ADR (Architecture Decision Record)

Para usar: `Ctrl+P → Templates: Insert template → escolher`

---

## Pendências do roadmap (em ordem de prioridade)

1. **Bug fluxo CAR/Localização** — adicionar relay no agente-router (regex `[A-Z]{2}-\d{7}-[A-F0-9]{32}` + LocationMessage → agente-whatsapp/webhook-incoming)
2. **Decisão arquitetural protheus IP shared** (mitigações vs VPN/Tailscale/Dedicated IP)
3. **Sobreposição funcional** financeiro-sa vs pedidos (`/painel-financeiro` em ambos)
4. **Atualizar SKILL.md** dos agentes (Xayer faz manual via skill-creator copiando do vault)
5. **Detalhar sistemas** em `03-Sistemas/` (Protheus/SA/SE — APIs, dicionário, queries)
6. **Popular frameworks** em `04-Frameworks-e-Metodologias/` (BSC, BPMN, COSO, OKR)
7. **Implementar agentes pesquisadores** em `07-Agentes-Pesquisadores/` (projeto trimestral)
8. **Build-time export** (Caminho 1: GitHub Action vault → repos dos agentes)

---

## Comportamento esperado em sessão nova

Quando o Claude inicia uma sessão e o usuário menciona qualquer coisa do ManaVault:

1. **Primeiro:** ler `MEMORY.md` da memória persistente (carrega automaticamente)
2. **Se sessão nova:** ler `project_manavault_estado_atual.md` da memória pra contexto consolidado
3. **Se vai mexer em agente X:** ler `06-Agentes-e-Skills/agente-X.md` ANTES de qualquer ação
4. **Se vai criar nota:** copiar template apropriado de `_Templates/` e preencher frontmatter rico
5. **Se decisão arquitetural grande:** criar ADR em `08-Decisoes/`
6. **Após qualquer mudança:** atualizar `ultima-revisao` no frontmatter da nota afetada

---

## Anti-patterns a evitar

❌ **Editar ADR antigo** → criar novo ADR que `supersede` o anterior
❌ **Adicionar conhecimento novo direto no system-prompt** → editar pesquisa-genetica e deixar bot herdar
❌ **Criar pasta sem `_index.md`** → toda pasta no vault tem `_index.md`
❌ **Wiki-links absolutos** → sempre relativos ao path da nota
❌ **Frontmatter sem `ultima-revisao`** → toda nota tem data de última edição
❌ **Renomear ADR** → ADRs são imutáveis no path
❌ **Mexer em código de agente sem ler a nota dele primeiro** → quebra a disciplina

---

## Onde aprender mais

- `HOME.md` — dashboard com links pra tudo
- `README.md` — visão completa do vault
- `08-Decisoes/_index.md` — todos os ADRs
- `_Templates/` — templates prontos
- `09-Runbooks/saneamento-zumbi-monorepo.md` — exemplo de runbook validado

---

## Referências cruzadas em sessões

Esta skill **trabalha em conjunto com**:

- **`agente-agronomo`** skill — quando bot agronomo precisa atualizar knowledge_base, vault é a fonte
- **`novo-agente-mana`** skill — agente novo = nota nova em `06-Agentes-e-Skills/`
- **`akita`** skill — princípios de defesa em camadas aplicados em todo agente Maná
- **`softexpert-orchestrator`** skill — biblioteca SOAP referenciada em `libraries-meta/`

---

*Última atualização: 2026-05-03 — 34 cultivares populados, separação knowledge/behavior aplicada, CSS de cores + color groups do graph ativos, OAuth/GCM funcionando.*
