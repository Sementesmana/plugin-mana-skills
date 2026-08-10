# Memória viva Maná — índice

> Um arquivo = um aprendizado. O Claude de QUALQUER máquina lê este índice e
> abre só o que a tarefa pede. Aprendeu algo durável na sua máquina? Escreva
> um arquivo novo aqui, commit, e o dono pusha — no próximo sync do
> marketplace, todas as máquinas passam a saber.

| Arquivo | Quando abrir |
|---|---|
| [git-crlf-fantasma-e-checkout.md](git-crlf-fantasma-e-checkout.md) | git mostra arquivos modificados que ninguém tocou; antes de QUALQUER `git checkout -- .`; lock órfão travando pull |
| [se-embed-frame-validador.md](se-embed-frame-validador.md) | embed de painel no SoftExpert recusado; widget "Página WEB"; deploy que "não muda nada" depois de env nova |
| [gitignore-desde-o-dia-1.md](gitignore-desde-o-dia-1.md) | repo novo; `.pyc`/`__pycache__` aparecendo no diff; limpar lixo versionado |
| [create-all-nao-altera-tabela.md](create-all-nao-altera-tabela.md) | coluna nova no model + "column does not exist" em produção; migração sem Alembic |
| [carga-grande-insert-em-lote.md](carga-grande-insert-em-lote.md) | importação de milhares de linhas; WORKER TIMEOUT no gunicorn |

## Regras deste diretório

- **Estados** (no frontmatter): `verificado: sim` = aconteceu em produção e a
  correção foi testada; `verificado: nao` = hipótese razoável, confirmar antes
  de confiar. Memória substituída não se apaga — ganha `supersede: <arquivo>`
  no substituto e um aviso no topo da antiga.
- **O que entra**: gotcha que custou ≥30 min, padrão validado em produção,
  decisão de convenção. **O que NÃO entra**: credencial, dado de cliente,
  nada específico de um único agente (isso vai na skill do agente).
- **Formato**: frontmatter (`data`, `origem`, `verificado`) + sintoma + causa
  + correção com comando pronto. Curto: o leitor está no meio de um problema.
