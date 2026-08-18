---
data: 2026-08-07
origem: agente-governanca (deploy que sobe e o healthcheck nunca passa)
verificado: sim
---

# Railway: `startCommand` do railway.json NÃO expande `$PORT`

## Sintoma

Deploy conclui, container sobe, e o healthcheck nunca passa / a URL responde 502.
No log, o gunicorn subiu numa porta que não é a que o Railway está roteando —
ou o processo morre com erro de bind.

## Causa

O `startCommand` declarado no `railway.json` **não passa por shell**, então `$PORT`
vai literal em vez de ser substituído pelo valor injetado pelo Railway.

## Correção

Usar **CMD em shell-form no Dockerfile** (aí o `$PORT` expande), e fazer bind em `[::]`
para cobrir IPv6:

```dockerfile
CMD gunicorn app:app --bind [::]:$PORT --workers 2 --timeout 60
```

Complemento: no pool Postgres, `connect_timeout` — sem ele, banco lento no boot vira
container pendurado sem log útil.

## Regra geral

Se a variável é do runtime (PORT, DATABASE_URL montada na hora), o comando precisa passar
por shell. Configuração declarativa não interpola.
