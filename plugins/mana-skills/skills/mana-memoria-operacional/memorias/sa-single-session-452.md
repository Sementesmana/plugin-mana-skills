---
data: 2026-08-18
origem: parque Maná (11 agentes lendo o Simple Agro) — incidentes recorrentes desde 2026-05
verificado: sim
---

# Simple Agro derruba sessão: HTTP 452 quando o mesmo login entra em outro lugar

## Sintoma

Requests que funcionavam começam a voltar **452** em bloco. O agente parece "quebrado",
mas nada mudou no código. Costuma acontecer em horário comercial — e some sozinho.

## Causa

O Simple Agro é **single-session por usuário**: quando o mesmo login autentica em outro
lugar (outro agente, ou uma pessoa abrindo o painel do SA no navegador), a sessão anterior
é invalidada. Não é rate limit, não é bug do seu código: é outro consumidor com a mesma
credencial.

Sintoma em bloco = fonte compartilhada, não dado sujo. Se **vários** agentes falham juntos,
procure a origem comum antes de investigar cada um.

## Correção

1. **Usuário dedicado à automação** — cada integração com o SA usa credencial exclusiva,
   nunca a de uma pessoa. Login humano no SA derruba a automação inteira.
2. **Tratar 452 como 401 com retry limitado** — relogar e repetir, com teto (ex.: 3
   tentativas). Sem teto, dois agentes entram em guerra de relogin.
3. **Cura estrutural: data lake.** Uma leitura por safra a cada N minutos alimentando
   `banco-mana`, e os painéis lendo do lake (`mana-habilidade-data-lake-pg`, lake-first).
   Onze consumidores batendo direto no ERP é o problema; um cron é a solução.

## Não faça

- Não trate 452 como "sem dados" — **falha não vira dado** (veja `falha-nao-vira-dado.md`).
- Não distribua a mesma credencial entre agentes novos "só pra testar".
