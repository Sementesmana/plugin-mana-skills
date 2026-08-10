---
data: 2026-08-03
origem: agente-comercio-revendas (embed no SE), confirmado no agente-financeiro-gestao
verificado: sim
---

# Embed no SoftExpert: o validador recusa QUALQUER restrição de frame

## Sintoma

Widget "Página WEB" do SE recusa a URL do painel, mesmo com
`frame-ancestors` liberando exatamente a origem do SE.

## Causa (comprovada por teste)

O validador do SE faz um GET server-side e recusa se encontrar **qualquer**
diretiva de frame declarada — ele não parseia allowlist. Teste que fechou a
questão: `google.com` (que manda `X-Frame-Options: SAMEORIGIN`) também é
recusado.

## Correção

Quando `SE_EMBED_ORIGIN` estiver definido:

- **omitir** `X-Frame-Options` e `frame-ancestors` por completo (não tentar
  liberar — omitir);
- cookie de sessão com `SameSite=None; Secure` (Lax não viaja em iframe
  cross-site);
- sem embed (`SE_EMBED_ORIGIN` vazio), os headers de bloqueio voltam.

Referência de código: `agente-comercio-revendas/config.py` + `app.py`
(commit `3224787`) e `agente-financeiro-gestao/app/config.py`.

## Armadilha associada: deploy FAILED silencioso

Ao ligar a env nova, se o app tem fail-fast no boot e algo está errado, o
deploy FALHA e o Railway **mantém o ACTIVE antigo no ar**. O log que você
abre é do deploy velho — parece que "não mudou nada". Custou ~2h. Sempre
conferir no Railway QUAL deploy está ACTIVE antes de debugar o log.
