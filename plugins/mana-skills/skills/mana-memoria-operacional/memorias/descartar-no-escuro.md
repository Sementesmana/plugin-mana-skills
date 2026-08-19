---
data: 2026-08-19
origem: máquina do Dayan (agente-comercio-revendas) + incidente na máquina-hub em 09/08
verificado: sim
---

# `git restore .` e `git checkout -- .`: descartar no escuro

## Sintoma

Trabalho some. Não deu erro, não pediu confirmação, não foi pro `stash` nem pro
reflog — simplesmente **não existe mais em lugar nenhum**. O dev jura que editou o
arquivo, e o arquivo está igual ao do último commit.

## Causa

Alguém rodou um comando de descarte **com ponto** (`.` = tudo). O padrão que apareceu
em 19/08 na máquina do Dayan:

```bash
git add api.py config.py templates/endossos.html   # só 3 arquivos
git commit -m "..."
git restore .                                      # ☠️ apaga TODO o resto que estava modificado
```

O `git add` seletivo é correto e comum. O problema é o `git restore .` logo depois:
ele devolve **todos** os arquivos ao estado do commit. Tudo que ficou de fora do
`git add` — e que muitas vezes é justamente o que o dev ainda estava trabalhando —
evapora.

**Por que é pior que apagar arquivo:** conteúdo não commitado não está no Git em
lugar nenhum. `git reflog` não salva, o Ctrl+Z do editor já passou, e não há lixeira.
É o único tipo de perda no Git que **não tem volta**.

## A família toda (mesma armadilha, nomes diferentes)

| Comando | O que faz |
|---|---|
| `git restore .` | descarta modificações não staged de tudo |
| `git checkout -- .` | idem (sintaxe antiga) |
| `git reset --hard` | descarta staged **e** não staged |
| `git clean -fd` | apaga arquivos **não rastreados** (inclusive os que você acabou de criar) |

## Correção — descarte nomeando, ou use algo reversível

```bash
git restore caminho/do/arquivo.py      # nomeando: você sabe o que está perdendo
git stash push -m "antes de limpar"    # reversível: git stash pop traz de volta
git diff                               # SEMPRE olhe antes de descartar qualquer coisa
```

**Regra:** descarte com `.` só depois de `git diff` e sabendo exatamente o que sai.
Na dúvida, `git stash` — custa nada e volta atrás.

## ⚠️ Os dois casos reais

1. **09/08, máquina-hub:** `git checkout -- .` rodado para "limpar CRLF fantasma"
   apagou uma edição recém-feita e não commitada no `_github_client.py`. Foi o que
   fez a cura do CRLF mudar para `core.autocrlf`, que **não precisa de checkout**
   (ver `git-crlf-fantasma-e-checkout.md`).
2. **19/08, máquina do Dayan:** `git restore .` como passo fixo depois de todo commit
   seletivo. Não dá para saber quanto se perdeu — é exatamente esse o problema.

## Bônus 1: pull rejeitado = você commita de dois lugares

`! [rejected] main -> main (fetch first)` significa que o remoto andou. Se você é o
único dev do repo, quase sempre é **você mesmo de outro lugar** (outra máquina, ou a
sessão Cowork na nuvem empurrando direto). Antes de começar a trabalhar, sempre:

```bash
git fetch origin && git log --oneline HEAD..origin/main   # o que chegou sem eu saber?
```

Para integrar com segurança: `git branch backup-antes-rebase` → `git pull --rebase
origin main`. Deu conflito, `git rebase --abort` volta tudo — não resolva no susto.

## Bônus 2: committer com e-mail inventado

```
Committer: Fulano <fulano@MAQUINA.LOCAL>
Your name and email address were configured automatically...
```

O Git chutou pelo nome da máquina porque ninguém configurou. Os commits **não vinculam
à conta do GitHub** e o histórico fica com um e-mail que não existe. É a Fase 2.4 do POP
de passagem de bastão, e escapa com frequência:

```bash
git config --global user.name "Nome Sobrenome"
git config --global user.email "email-da-conta-github@dominio"
```
