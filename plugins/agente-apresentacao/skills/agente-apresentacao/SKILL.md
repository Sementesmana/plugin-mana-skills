---
name: agente-apresentacao
description: Servidor dos decks estratégicos da Sementes Maná LTDA (painel N1, produção) — Flask estático de 49 linhas no Railway que hospeda 12 HTMLs single-file em static/, com a raiz redirecionando para o deck principal (Apresentacao-Planejamento-Estrategico-Mana.html). Sem autenticação por decisão (ADR 2026-06-07, link aberto), sem banco, sem integração nenhuma - os HTMLs carregam imagens em base64 embutido, por isso alguns passam de 1MB (Maná 5.0 tem 4,2MB). Serve também os decks de IA-Governança, Nova Sede, GreenCore, Estruturação-Números, os explicadores de arquitetura IA-First, o Panorama de Mercado e o cockpit de portfólio. Use SEMPRE em tarefas do agente-apresentacao — adicionar ou trocar deck, mexer no redirect da raiz, imagens embutidas, peso do HTML, deploy do servidor estático. Também quando mencionar deck BSC, apresentação estratégica, DECK_PRINCIPAL, Apresentacao-Mana-5-0, Apresentacao-Nova-Sede, portfolio-ia-cockpit.html, link aberto sem senha.
---

# agente-apresentacao — servidor dos decks estratégicos

> **Painel N1, produção** · `https://agente-apresentacao-production.up.railway.app` ·
> **dono Leonardo** (desde 26/08/2026) · comportamento **D**.
>
> Nota canônica desta solução. Espelho em
> `plugin-mana-skills/plugins/agente-apresentacao/skills/agente-apresentacao/SKILL.md` —
> os dois andam juntos no mesmo push.

## O que é

O serviço mais simples do parque: **49 linhas de Flask** servindo a pasta `static/`. Toda a
inteligência está nos HTMLs — cada deck é um arquivo único, autossuficiente, com CSS/JS inline e
imagens em base64. Sem banco, sem LLM, sem WhatsApp, sem SoftExpert, sem Simple Agro.

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

**Sem autenticação, por decisão** (ADR da sessão de 07/06/2026 — link aberto, feito para ser
compartilhado). Não colocar senha sem revisar essa decisão; **não colocar conteúdo sensível nesses
decks** — sem PII, sem CPF, sem valor de contrato individual, sem documento de comitê de crédito.

## O acervo (12 decks em `static/`, conferido em 26/08/2026)

- **Planejamento Estratégico Maná** — o principal (BSC), 1,5 MB
- **Maná 5.0** (4,2 MB) · **IA-Governança** (1,1 MB) · **Nova Sede** (583 KB)
- **portfolio-ia-cockpit.html** (134 KB) · **Estruturação-Números** · **GreenCore**
- **Arquitetura IA-First**: Explicador, Estado & Roadmap, Comparativo, Detalhado
- **Panorama de Mercado IA-First**

A contagem não está fixa no código: adicionar ou remover deck não exige tocar em `app.py`, e o
`/health` passa a reportar o número novo sozinho.

## Peso: cuidado ao editar

Imagem embutida em base64 é o que faz um HTML de 800 linhas pesar 1,5 MB. Ao trocar imagem,
**redimensionar antes de embutir** — foi exatamente o que os commits de 11–12/08/2026 fizeram
("sede oficial embutida e redimensionada"). Editar esses arquivos pelo mount tem risco de
truncamento: gravar via ferramenta de escrita / `device_commit_files`, nunca por `sed` ou
redirecionamento no mount. Sintoma de truncamento: o deck abre e para no meio, ou o final do
arquivo desaparece.

## Deploy

`git push` → Railway (NIXPACKS, healthcheck `/health`, gunicorn 2 workers/timeout 30). Existe
também `deploy.bat` (script Windows de push). **Nunca `railway up`.** Se o healthcheck do deploy
novo falhar, o Railway mantém o anterior ACTIVE — conferir qual está ativo antes de concluir que
"o push não subiu".

## Publicar ou trocar um deck (o trabalho do dia a dia)

1. `git pull` antes de mexer.
2. Colocar o HTML novo em `static/` com nome descritivo e sem acento no arquivo.
3. Trocar deck existente: substituir o arquivo mantendo o nome (o link que já circula continua
   valendo). Nome novo = link novo, e o antigo passa a dar 404.
4. Mudou o deck principal? Só então `DECK_PRINCIPAL` em `app.py` muda.
5. `git push` → esperar ~2min → abrir `/health` e conferir a contagem de `decks`.
6. Atualizar a seção do acervo aqui e o `ultima-revisao` da nota do vault **no mesmo push**.

## Disciplina de dono (modelo federado)

- **`git pull` antes de mexer, `git push` depois.** As duas únicas coisas que quebram o fluxo são
  esquecer o pull e editar pasta que não é clone git.
- **Um motorista por vez.** Leonardo é o dono; quem for mexer avisa antes.
- Nota do agente no vault: `ManaVault/06-Agentes-e-Skills/agente-apresentacao.md` (ponteiro do
  grafo — esta skill é a fonte).
- POP da passagem de bastão: `ManaVault/09-Runbooks/pop-handoff-agente-apresentacao-leonardo.html`.

## Histórico de drift (resolvido)

- ~~Docstring do `app.py` dizia "5 HTMLs (principal + 4 sub-decks)"~~ → corrigido em 21/08/2026,
  hoje descreve os 12 e a contagem dinâmica.
- ~~"Sem nota no ManaVault/06 — drift documental" (acusado pelo cockpit desde 13/06/2026)~~ → nota
  criada em 26/08/2026, no handoff para o Leonardo.
