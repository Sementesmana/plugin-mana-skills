---
data: 2026-08-09
origem: agente-monitor (8 .pyc versionados, sem .gitignore)
verificado: sim
---

# .gitignore existe antes do primeiro commit — sem exceção

## Sintoma

`__pycache__/` e `.pyc` aparecendo em todo diff; um `.pyc` entrou de carona
num commit de feature. O agente-monitor viveu meses assim.

## Regra

Repo novo nasce com `.gitignore` cobrindo no mínimo: `__pycache__/`,
`*.py[cod]`, `.venv/`, `.env` (com `!.env.example`), `.pytest_cache/`,
`*.log`. O scaffold do `novo-agente-mana` já gera — o gotcha é repo criado à
mão ou herdado.

Se o repo lida com DADOS (planilha, extrato, export), bloquear também os
formatos: `*.xlsx *.csv *.pdf` e as pastas de dados — ver o `.gitignore` do
`agente-financeiro-gestao`, que documenta o porquê de cada bloco.

## Limpar o que já foi versionado

```bash
git rm -r --cached __pycache__ -q     # remove do Git, mantém no disco
git add .gitignore && git commit -m "Remove .pyc do versionamento e adiciona .gitignore"
```

## Por que importa além da estética

Lixo compilado suja o diff (esconde mudança real em revisão), causa conflito
de merge inútil entre máquinas, e — no caso de pastas de dados — é a última
linha de defesa contra subir dado de cliente pro GitHub.
