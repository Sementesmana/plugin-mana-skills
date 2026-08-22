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

## Achado de campo: o parâmetro importa (agente-tms, Dayan, 12/08)

Nem toda chamada ao mesmo endpoint tem o mesmo risco. No `charge-montage`:

| Consulta | Resultado |
|---|---|
| `?carga=<numero>` (filtro por número) | **dispara o 452** |
| por `safra.id` (igual ao relatório do SA) | **200** |

A correção foi **remover o filtro** e resolver o número sempre pelo cache local. Antes de
concluir que "o SA bloqueou", teste se **outra forma de perguntar a mesma coisa** passa —
pode ser o parâmetro, não a sessão.

Complementos validados em produção no mesmo trabalho:

- **Cooldown de 3h após um 452.** Continuar batendo *reativa* o bloqueio e nunca deixa a
  janela fechar. Depois do 452, sirva do lake e não toque no SA.
- **Ping de liberação** — um request barato só para checar se voltou, que limpa o cooldown
  quando responde 200. Evita esperar as 3h inteiras à toa.
- **Refresh do lake em background** (intervalo configurável, default 60 min, piso de 5)
  com resposta servida do cache: a tela nunca espera o ERP.

## Cura estrutural EM PRODUÇÃO: mana-sa-gateway (21/08)

A porta única saiu do papel: **mana-sa-gateway** (ADR 2026-08-20) com credencial
PRÓPRIA de automação (nenhum humano loga com ela — senão o 452 volta), portão
serializado com espaçamento de 2s, lake `sa_lake` no banco-mana (leitura
pública, escrita só do gateway), frescor declarado pelo chamador e X-API-Key
por agente. TMS migrado 21/08: **zero 452 desde então**. Agentes novos que leem
o SA: consumir o gateway (`SA_GATEWAY_URL`/`SA_GATEWAY_KEY`), não o SA direto.

Dois gotchas de login descobertos na migração:

- **O token do SA já vem com `Bearer `** — prefixar de novo vira
  `Bearer Bearer <token>` = **401 em toda chamada com login "ok"** (o POST de
  login não usa o header, então o login passa e o resto morre). Sempre:
  `raw if raw.startswith("Bearer ") else "Bearer " + raw`.
- A API também mente sobre completude — veja `sa-api-mente-listagem-e-limit.md`.

## Não faça

- Não trate 452 como "sem dados" — **falha não vira dado** (veja `falha-nao-vira-dado.md`).
- Não distribua a mesma credencial entre agentes novos "só pra testar".
