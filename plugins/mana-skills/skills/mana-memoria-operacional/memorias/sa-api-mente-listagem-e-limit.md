---
data: 2026-08-21
origem: migração do agente-tms pro mana-sa-gateway (caso do agendamento de 52 bags invisível)
verificado: sim
---

# API do Simple Agro mente: listagem trunca aninhado, e limit=-1 mente com o total junto

## Sintoma

Item que existe na TELA do SA não aparece no seu agente — e "atualizar o cache"
não traz. Ou: conjunto que deveria ter centenas volta com 19. Ou: o mesmo
endpoint devolve 11 com `total=11` num dia em que o caminho paginado trazia 24.

## As três mentiras (todas vistas em produção, 19–21/08)

1. **A listagem trunca lista aninhada.** `/api/orders-scheduling` devolve só o
   `data_volume` MAIS RECENTE de cada item — achatado num objeto único. Pedido
   com 9 agendamentos voltava com 1. O agendamento de 52 bags ficou 28 min como
   "mais recente", nenhum refresh rodou na janela, e ele nunca existiu pro
   agente (o cache do TMS só "funcionava" por acumulação acidental).
2. **`limit=-1` vem incompleto sem avisar.** 19 cargas de uma safra cheia — a
   carga 2696 "não existia" na Seleção de Lote.
3. **O `total` da resposta mente JUNTO.** Não dá pra validar o limit=-1 por
   dentro: ele disse `total=11` entregando 11, no momento em que a paginação
   trazia 24. Conferir `len(docs) >= total` NÃO protege.

## Correção (padrão do mana-sa-gateway, em produção)

- **Sempre paginado** (`limit=200` até vir página curta/vazia) — nunca
  `limit=-1`, nunca confiar no `total`. Espaçado (2s entre chamadas) não
  dispara 452; o que disparava era rajada.
- **Listagem é ÍNDICE, documento é a VERDADE.** Para dado aninhado, use a
  listagem só pra descobrir os ids e busque cada registro completo
  (`/api/orders/{id}`). Entregue no formato da listagem (explode a lista
  aninhada em entradas de objeto único, descarta `deleted`) — os consumidores
  já foram escritos pra esse formato.
- **Diagnóstico pronto:** `GET /diag/pedido/<id_mongo>` no mana-sa-gateway
  devolve o documento cru — compare com a listagem antes de caçar bug no agente.

## Lição de desenho que veio junto (caminhão #12)

**Vínculo por posição desliza.** Id composto terminado em `#posição` aponta pro
registro errado assim que alguém cria/edita/remove item no SA (a lista muda,
tudo desliza — caminhão carregou olhando pro agendamento errado). Vincule pelo
`_id` mongo do próprio registro (imutável); posição é só desempate de exibição.
E guarde snapshot (id + quantidade) no momento do vínculo: no refresh, se
divergir, volta a etapa no processo — nunca siga em silêncio.

## Não faça

- Não valide completude pelo `total` da resposta — pagine até o fim.
- Não conclua "está no lake, logo o agente vê": formato importa (lista aninhada
  × objeto único quebra parser silenciosamente).
