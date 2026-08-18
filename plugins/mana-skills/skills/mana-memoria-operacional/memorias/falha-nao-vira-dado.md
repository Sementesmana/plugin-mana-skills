---
data: 2026-08-13
origem: incidente do Painel Comercial SA (agente-financeiro-sa) — painel branco sem aviso
verificado: sim
---

# Falha nunca vira dado — e vazio não sobrescreve snapshot bom

## Sintoma

O painel abriu **branco**, sem erro na tela e sem alerta. O ERP tinha recusado a chamada;
o código devolveu `[]`; o cache guardou `[]` como se fosse resultado legítimo. Durante
horas o sistema afirmou, com toda a confiança, que não havia pedidos.

## Causa

**Um valor significando duas coisas.** `[]` queria dizer "não há registros" *e* "a origem
falhou". O mesmo defeito aparece em outras roupas: `horas == 0.0` significando "durou zero",
"fora do expediente" e "rápido demais pro contador"; ISO sem offset significando hora local
*e* UTC.

## Correção — quatro regras que andam juntas

1. **Falha levanta exceção.** `return []` no caminho de erro é proibido. Lista vazia
   significa uma coisa só: não há registro.
2. **Nunca persistir vazio vindo de erro; nunca sobrescrever snapshot bom com falha.**
   Vazio só entra no lake quando a origem **confirmou** sucesso (safra nova com zero
   pedidos é verdade gravável — a proibição é no caminho de erro, não no valor).
3. **Todo payload diz de quando é** — `fonte` (lake/ao vivo) + idade, e a tela avisa quando
   o dado está velho. Dado antigo com aviso é útil; dado antigo silencioso é mentira.
4. **Timestamp que cruza processo carrega o offset.** ISO sem fuso é dado ambíguo — foi
   rodapé mostrando 17h às 14h.

## Regra de bolso

Dar à falha um **tipo próprio** e nunca deixar o caminho de erro escrever no cache.
Se o mesmo valor pode ser resposta e desculpa, ele já é um bug com data marcada.
