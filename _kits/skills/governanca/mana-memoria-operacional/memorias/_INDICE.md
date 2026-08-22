# Memória viva Maná — índice

> Um arquivo = um aprendizado. O Claude de QUALQUER máquina lê este índice e
> abre só o que a tarefa pede. Aprendeu algo durável na sua máquina? Escreva
> um arquivo novo aqui, commit, e o dono pusha — no próximo sync do
> marketplace, todas as máquinas passam a saber.

| Arquivo | Quando abrir |
|---|---|
| [git-crlf-fantasma-e-checkout.md](git-crlf-fantasma-e-checkout.md) | git mostra arquivos modificados que ninguém tocou; diff com inserções == deleções; **antes de qualquer commit em lote numa varredura**; antes de QUALQUER `git checkout -- .`; lock órfão travando pull |
| [se-embed-frame-validador.md](se-embed-frame-validador.md) | embed de painel no SoftExpert recusado; widget "Página WEB"; deploy que "não muda nada" depois de env nova |
| [gitignore-desde-o-dia-1.md](gitignore-desde-o-dia-1.md) | repo novo; `.pyc`/`__pycache__` aparecendo no diff; limpar lixo versionado |
| [create-all-nao-altera-tabela.md](create-all-nao-altera-tabela.md) | coluna nova no model + "column does not exist" em produção; migração sem Alembic |
| [carga-grande-insert-em-lote.md](carga-grande-insert-em-lote.md) | importação de milhares de linhas; WORKER TIMEOUT no gunicorn |
| [sa-single-session-452.md](sa-single-session-452.md) | HTTP 452 do Simple Agro em bloco; requests caindo sozinhos em horário comercial; credencial compartilhada entre agentes |
| [falha-nao-vira-dado.md](falha-nao-vira-dado.md) | painel branco sem aviso; `return []` no caminho de erro; cache guardando vazio; timestamp sem fuso |
| [cowork-remoto-bridge.md](cowork-remoto-bridge.md) | sessão na nuvem com a pasta pela bridge; arquivo que "não salva"; `git add` dizendo "nothing to commit"; leitura truncada depois de gravar |
| [verificar-por-conjunto.md](verificar-por-conjunto.md) | "está tudo lá?"; conferir migração/índice/import; a contagem bateu mas algo sumiu; **o conjunto bateu mas o conteúdo pode estar velho** (prova de frescor) |
| [descartar-no-escuro.md](descartar-no-escuro.md) | trabalho sumiu sem erro; antes de QUALQUER `git restore .` / `checkout -- .` / `reset --hard` / `clean -fd`; push rejeitado com "fetch first"; committer com e-mail @MAQUINA.LOCAL |
| [documentacao-a-frente-do-codigo.md](documentacao-a-frente-do-codigo.md) | a nota do vault diz "pronto" e o repo não tem; antes de commitar trabalho represado; varredura periódica do parque; fechamento de tarefa |
| [railway-startcommand-port.md](railway-startcommand-port.md) | deploy sobe mas healthcheck não passa; 502 no Railway; `$PORT` literal no comando |
| [sa-api-mente-listagem-e-limit.md](sa-api-mente-listagem-e-limit.md) | item existe na tela do SA mas não no agente; conjunto incompleto com limit=-1; `total` que bate mas falta dado; vínculo por posição apontando pro registro errado |

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
