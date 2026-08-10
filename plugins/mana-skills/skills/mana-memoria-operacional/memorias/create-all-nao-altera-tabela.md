---
data: 2026-08-07
origem: agente-financeiro-gestao (colunas parceiro_alt/bruto ausentes em produção)
verificado: sim
---

# db.create_all() NÃO adiciona coluna em tabela que já existe

## Sintoma

Você adiciona colunas num model SQLAlchemy, o deploy sobe **verde**, e a
primeira escrita quebra: `column "parceiro_alt" of relation "titulo" does
not exist`. Os testes passam (SQLite recriado do zero tem as colunas); só a
produção quebra.

## Causa

`create_all()` cria tabelas que não existem e **ignora silenciosamente** as
que existem — não compara colunas. O banco fica atrás do código sem nenhum
aviso.

## Correção — migração aditiva no boot

Padrão validado em `agente-financeiro-gestao/app/migracao.py`
(`alinhar_colunas()`), rodando no start antes do gunicorn:

- compara colunas do model com o banco via `inspect(engine)`;
- só `ADD COLUMN IF NOT EXISTS` — **nunca** DROP, ALTER TYPE ou rename;
- coluna nova entra NULL-ável mesmo se o model diz NOT NULL (tabela com
  linhas recusaria);
- falha numa tabela não bloqueia as outras; tudo é impresso no log do deploy
  (`+ coluna titulo.parceiro_alt (TEXT)`).

## Quando isto NÃO basta

Renomear coluna, mudar tipo, apagar: aí é Alembic de verdade. Este padrão é
deliberadamente só-aditivo — é o que o torna seguro para rodar em todo boot.
