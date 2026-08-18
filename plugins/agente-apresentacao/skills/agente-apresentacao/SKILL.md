---
name: agente-apresentacao
description: Servidor dos decks estratégicos da Sementes Maná LTDA (painel N1, produção) — Flask estático de 49 linhas no Railway que hospeda 12 HTMLs single-file em static/, com a raiz redirecionando para o deck principal (Apresentacao-Planejamento-Estrategico-Mana.html). Sem autenticação por decisão (ADR 2026-06-07, link aberto), sem banco, sem integração nenhuma - os HTMLs carregam imagens em base64 embutido, por isso alguns passam de 1MB (Maná 5.0 tem 4,2MB). Serve também os decks de IA-Governança, Nova Sede, GreenCore, Estruturação-Números, os explicadores de arquitetura IA-First, o Panorama de Mercado e o cockpit de portfólio. Use SEMPRE em tarefas do agente-apresentacao — adicionar ou trocar deck, mexer no redirect da raiz, imagens embutidas, peso do HTML, deploy do servidor estático. Também quando mencionar deck BSC, apresentação estratégica, DECK_PRINCIPAL, Apresentacao-Mana-5-0, Apresentacao-Nova-Sede, portfolio-ia-cockpit.html, link aberto sem senha.
---

# agente-apresentacao — servidor dos decks estratégicos

> **Painel N1, produção** · `https://agente-apresentacao-production.up.railway.app` · dono Xayer · comportamento **D**.

## O que é

O serviço mais simples do parque: **49 linhas de Flask** servindo a pasta `static/`. Toda a inteligência está nos HTMLs — cada deck é um arquivo único, autossuficiente, com CSS/JS inline e imagens em base64.

```python
DECK_PRINCIPAL = "Apresentacao-Planejamento-Estrategico-Mana.html"
```

## Rotas

| Rota | O que faz |
|---|---|
| `GET /` | redireciona (302) para o deck principal |
| `GET /apresentacao` | mesmo redirect, atalho mnemônico |
| `GET /<arquivo>` | serve qualquer HTML de `static/` |
| `GET /health` | conta os `.html` e devolve `{status, agente, decks, principal}` |

**Sem autenticação, por decisão** (ADR da sessão de 07/06/2026 — link aberto, feito para ser compartilhado). Não colocar senha sem revisar essa decisão; não colocar conteúdo sensível nesses decks.

## O acervo (12 decks em `static/`)

- **Planejamento Estratégico Maná** — o principal (BSC)
- **Maná 5.0** (4,2 MB) · **Nova Sede** · **GreenCore** · **Estruturação-Números**
- **IA-Governança** · **Arquitetura IA-First**: Estado & Roadmap, Explicador, Comparativo, Detalhado
- **Panorama de Mercado IA-First** · **portfolio-ia-cockpit.html**

## Peso: cuidado ao editar

Imagem embutida em base64 é o que faz um HTML de 800 linhas pesar 1,5 MB. Ao trocar imagem, **redimensionar antes de embutir** — foi exatamente o que os commits de 11–12/08/2026 fizeram ("sede oficial embutida e redimensionada"). Editar esses arquivos pelo mount tem risco de truncamento: gravar via ferramenta de escrita/`device_commit_files`, nunca por `sed`/redirecionamento no mount.

## Deploy

`git push` → Railway (NIXPACKS, healthcheck `/health`, gunicorn 2 workers/timeout 30). Existe também `deploy.bat` (script Windows de push). Nunca `railway up`.

## Drift conhecido

- O docstring do `app.py` diz **"5 HTMLs (principal + 4 sub-decks)"** — hoje são **12**.
- O cockpit registra: *"⚠️ Sem nota no ManaVault/06 — criar nota (drift documental)"*. Ao evoluir o agente, criar a nota canônica seguindo `_Templates/nota-agente.md`.
