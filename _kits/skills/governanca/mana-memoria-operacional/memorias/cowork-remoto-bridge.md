---
data: 2026-08-18
origem: máquina-hub (Xayer) — Cowork remoto (sessão na nuvem + bridge do desktop)
verificado: sim
---

# Cowork remoto: escrever pela bridge, ler pelo list_dir, e `touch` antes do commit

Vale quando a sessão roda **na nuvem** com a pasta do dev montada pela bridge do app
desktop (`device_*`). Os fantasmas do mount Windows continuam existindo — só mudam de nome.

## Regras

- **Escrever no disco do dev = `device_commit_files`.** Grava os bytes reais (equivalente
  ao Write do Cowork local). Construir/editar o arquivo no container (`/tmp`), validar lá,
  e só então gravar.
- **NÃO editar arquivo do mount in-place** (`sed`, `python open(...,'w')`, `git checkout`).
  Já truncou o fim de um HTML em produção, e as leituras seguintes mostraram tamanhos
  oscilando — cache podre de leitura *e* de escrita.
- **A fonte autoritativa do que está no disco é `device_list_dir`** (metadados direto do
  Windows). O `bash` da máquina local lê stale logo após um commit pela bridge: mostra
  tamanho antigo com conteúdo novo no meio, parecendo truncamento.
- **Re-stage imediato não serve de verificação** — devolve o conteúdo anterior.
- **`git add` diz "nothing to commit" mesmo com arquivo mudado.** A gravação pela bridge
  mantém o **mtime antigo**; o git usa mtime+size pra decidir se reconfere e pula o arquivo.
  **Fix:** `touch` nos arquivos editados antes do `add`:
  ```bash
  touch <arquivos> && rm -f .git/index.lock .git/HEAD.lock && git add -A && git commit -m "..." && git push
  ```
  Sinal de que funcionou: voltam os warnings de LF/CRLF (o git reexaminou).
- **O bash local não tem rede e não deleta** (`rm` = Operation not permitted). Para remover,
  `mv` para `_to_delete/` e o dev apaga; ou `git rm` no Git Bash dele.
- **Commit/push é sempre do dev no Git Bash** — o bash da bridge leria a versão em cache e
  poderia commitar arquivo quebrado.
- **Diff CRLF fantasma** (insertions == deletions, `git diff --ignore-cr-at-eol` vazio) é
  ruído de line-ending, não mudança real.
