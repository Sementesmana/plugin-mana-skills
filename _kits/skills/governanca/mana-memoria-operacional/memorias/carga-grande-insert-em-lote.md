---
data: 2026-08-07
origem: agente-financeiro-gestao (23.288 títulos do Protheus numa carga)
verificado: sim
---

# Importação de milhares de linhas: insert em lote, com fallback que isola a linha ruim

## Sintoma

Endpoint de importação com milhares de registros estoura `WORKER TIMEOUT` do
gunicorn (o bot-multiplicacao já tinha sofrido o mesmo com 56 pedidos sem
pool). Uma linha inválida derruba a carga inteira.

## Padrão validado (`agente-financeiro-gestao/app/blueprints/carga.py`)

1. **Valida/coage linha a linha** em memória (barato) — linha ruim vira
   contagem de `ignoradas`, não exceção.
2. **`insert(model)` executemany em lotes de 1000** — 23 mil linhas caem de
   minutos para segundos.
3. **Se um lote inteiro falhar** (tipo incompatível, coluna faltando):
   rollback e reprocessa AQUELE lote linha a linha, para isolar a culpada e
   salvar as outras 999.
4. Toda linha aponta pra uma `carga_id`; a leitura usa a última carga OK —
   reimportar não duplica, apagar a carga volta pra anterior.

## Regra de bolso

Acima de ~500 linhas, `db.session.add()` num loop é bug em produção esperando
hora. E o aviso na tela importa tanto quanto a gravação: "✓ N linhas salvas"
/ "✗ NÃO foi salvo: <motivo real do Postgres>" — o erro real na tela foi o
que permitiu diagnosticar `column does not exist` em minutos.
