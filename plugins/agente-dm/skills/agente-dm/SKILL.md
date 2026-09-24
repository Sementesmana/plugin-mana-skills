---
name: agente-dm
description: >-
  Maná Mercado — plataforma de Desenvolvimento de Mercado (DM) da Sementes Maná. Flask + Jinja2 +
  Alpine + PostgreSQL (banco-mana, schema dm) + Railway. Vincula pedidos de bonificação, difusão e
  doação do Simple Agro (lidos do lake do banco-mana, SEM login no SA) a solicitações justificadas
  com aprovação (rascunho → aguardando → aprovada/reprovada), lado a lado com concorrentes + termo
  assinado + protocolo DM-ano-seq, usuários admin/vendedor ligados ao vendedor do SA pelo ID.
  Use SEMPRE no agente-dm / plataforma DM / Maná Mercado — Vincular Pedidos, solicitações,
  aprovação, segregação por vendedor/agente, dias de campo, emplacamentos, treinamento, resultado
  de produtividade, lado a lado, termo de uso de imagem, mana-mercado.html.
---

# agente-dm — Maná Mercado

Donos: **Xayer + Dayan** (co-donos; "um motorista por vez"). Repo `Sementesmana/agente-dm` (privado).
Nota no vault: `ManaVault/06-Agentes-e-Skills/agente-dm.md`.

## Regras que não mudam sem decisão

1. **Não loga no Simple Agro.** Pedidos vêm de `agente_financeiro_sa.data_lake` (`orders:<safra_id>`)
   e, se faltar a safra, `agro.lake_pedidos_raw` — `lake_sa.py`. Dado ao vivo → `mana-sa-gateway`
   (`/v1/pedidos` pronto), só quando alguma tela precisar de atualização toda hora.
2. **Tipos do DM:** bonificação, difusão, doação (`CONFIG["TIPOS_DM"]`, substring sem acento).
   No SA 26/27 existem "VENDA BONIFICAÇÃO" e "VENDA DIFUSÃO"; "doação" ainda não apareceu.
3. **Dono do pedido = vendedor + agente(s)**; todos enxergam. Vínculo do usuário pelo
   `vendedor.id` / `agente_venda.id` do SA (nunca pelo nome). Segregação no SQL.
4. **Uma solicitação por pedido**; aprovação em um nível (admin). Só rascunho edita.
   Sem aprovação não gera documento/resultado final.
5. **Falha nunca vira dado:** lake fora → erro 503 na tela (ou última leitura DECLARADA), nunca
   "nenhum pedido".
6. CPF/CNPJ não sai do lake. Termos são minuta até o jurídico validar.

## Mapa do código

| Arquivo | O quê |
|---|---|
| `lake_sa.py` | leitura/normalização dos pedidos, `tipo_dm`, `visivel` (segregação) |
| `solicitacoes.py` | máquina de estados (regras puras + banco), anexos, protocolo |
| `db.py` | pool + DDL do schema `dm` (usuarios, motivos, arquivos, solicitacoes, historico, audit_log) |
| `auth.py` | hash de senha, sessão, rate limit, `requer_login`/`requer_admin` |
| `routes_api.py` / `routes_ui.py` | API JSON (header `X-DM` em mutação) / páginas |
| `templates/app.html` | SPA Alpine com o visual da maquete (`static/css/mana-mercado.css` intacto) |
| `docs/referencia/` | pacote original do Dayan: maquete, FLUXOS, MODELO-DADOS, TERMO, BACKLOG |

## Próximas fases (portar da maquete, não reinventar)

Dias de Campo (status + 8 abas) · Emplacamentos (GPS, ≥3 fotos) · Clientes e Áreas
(propriedade vem no pedido) · Obtentoras (metas) · Painel · Relatórios · Treinamento ·
Resultado de Produtividade · Lado a Lado Plantio/Colheita · lista de presença A4 + OCR.

## Gotchas

- Railway: deploy só por `git push`; `/health` = `degraded` se o banco cair.
- O CSS da maquete começava com `<style>` quando extraído — isso anula o `:root` inteiro.
- Testes: `pytest -q` (sem banco) e `DM_PG_TESTE=<pg descartável>` para o fluxo ponta a ponta.
