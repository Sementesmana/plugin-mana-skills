# plugin-mana-skills — Maná Builder

> **Marketplace de skills da Maná Builder.** Distribui as skills que orientam o Cowork/Claude Code dos devs Maná (Xayer, Dayan, Lorena, futuros) na construção de artefatos no ecossistema Sementes Maná LTDA.

## Como o dev usa

### 1. Baixa a skill que precisa

Cada skill mora em `_kits/skills/<categoria>/<nome>/SKILL.md`. Abre o arquivo no GitHub, copia o conteúdo inteiro (do `---` frontmatter até o fim).

### 2. Cola no Cowork

- **Cowork:** Settings > Capabilities > Create Skill (ou similar)
- Cola o conteúdo
- Salva

A skill fica disponível toda sessão nova.

### 3. Invoca

Digite a frase de ativação (ver `ativacao:` no frontmatter da skill). O Cowork consulta a skill automaticamente.

## Skills disponíveis

### 📚 Governança (skills de processo Maná)

| Skill | O que faz | Quem usa |
|---|---|---|
| [`mana-builder-guia`](_kits/skills/governanca/mana-builder-guia/SKILL.md) | Guia de ENTRADA — orienta dev na criação de artefato novo | Todo dev novo criando qualquer coisa |

### 🛠 Templates (a adicionar em Onda 1)

- `novo-agente-mana` (existe hoje instalado por dev, migrar pra cá)
- `nova-habilidade-mana` (a criar)

### ⚙️ Habilidades (a adicionar em Onda 1)

Referência às habilidades publicadas em `Sementesmana/mana-habilidade-*`:

- `se-dataset-reader` v0.1.0 (publicada 2026-06-30)
- `data-lake-pg` v0.1.0 (publicada 2026-06-30)
- `gerar-pdf-timbrado` v0.3.0
- `transcrever-audio` v0.1.0
- `pseudonimizar-pii` v0.1.0
- `enriquecer-sa` v0.1.0
- `extrair-pdf` v0.1.0

### 🌐 Hubs (a adicionar)

- `mana-llm-gateway`
- `mana-llm-gateway-v2`
- `agente-whatsapp`
- `agente-router`

## Como o dev consome as HABILIDADES (código Python)

Skills são só **guias/manuais** — a IA usa pra orientar. As habilidades reais (código Python instalável) moram nos repos `Sementesmana/mana-habilidade-*` e instalam via pip:

```bash
pip install "git+https://github.com/Sementesmana/mana-habilidade-<nome>.git@v<X.Y.Z>"
```

## Como contribuir com skill nova

1. Fork ou branch neste repo
2. Adiciona `_kits/skills/<categoria>/<nome>/SKILL.md`
3. PR pra Xayer revisar
4. Merge → dev novo já tem acesso

## ADRs aplicáveis

- `2026-06-26-plugin-mana-skills-cowork` (vault)
- `2026-06-26-mana-builder-matriz-cobertura` (vault)
- `2026-06-30-stack-dados-mana-builder` (vault)

## Dono

Xayer (@xayer-mana) + CODEOWNERS por categoria conforme skills crescem.
