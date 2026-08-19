---
data: 2026-08-18
origem: maquina-hub (varredura dos 61 repos do parque) — revisa a versão de 2026-08-09
verificado: sim
---

# Git no Windows: diff fantasma de CRLF — detectar em 1 comando, curar sem checkout

## Sintoma

`git status` mostra arquivos modificados que ninguém editou, e o diff parece a
reescrita do arquivo inteiro. Na varredura do parque (18/08) mais de 20 repos
apareceram "sujos" assim; o pior, `agente-comercio-revendas`, acusava
**37 files changed, 6429 insertions(+), 6429 deletions(-)** — e não havia uma
linha de mudança real.

## Causa raiz (diagnóstico do parque)

`core.autocrlf` **não definido** — nem global, nem local em nenhum repo — e
**nenhum repo com `.gitattributes`**. Sem regra, o Git guarda LF no HEAD e o
Windows grava CRLF no disco: todo arquivo que qualquer editor do Windows tocar
passa a divergir do HEAD **só no terminador de linha**.

## Detecção — a regra dos 5 segundos

Dois sinais, os dois baratos:

1. **`insertions == deletions`** no `git diff --stat` (6429/6429) — nenhuma
   edição humana sai perfeitamente simétrica.
2. **`git diff --ignore-cr-at-eol` vazio** — prova definitiva.

```bash
git diff --stat                       # inserções == deleções? suspeita
git diff --ignore-cr-at-eol --stat    # vazio = FANTASMA, não commite
```

Rodando no parque inteiro, antes de qualquer commit em lote:

```bash
cd /c/Users/<voce>/ORQUESTRADOR
for d in */; do
  [ -d "$d/.git" ] || continue
  s=$(git -C "$d" status --porcelain 2>/dev/null | wc -l); [ "$s" = "0" ] && continue
  r=$(git -C "$d" diff --ignore-cr-at-eol --stat 2>/dev/null | wc -l)
  [ "$r" = "0" ] && echo "FANTASMA  $d" || echo "REAL      $d"
done
```

## Correção — máquina (imediata, zero commit, zero risco)

```bash
# Git Bash no Windows (é o que o POP de passagem de bastão manda)
git config --global core.autocrlf true

# sessão Cowork remota (Linux) — `true` aqui reescreveria os arquivos com CRLF
git config --global core.autocrlf input
```

Uma linha. O Git passa a normalizar para LF **no `git add`**; nenhum arquivo é
reescrito e o `git status` limpa sozinho nos repos que só tinham fantasma —
verificado em `agente-comercio-revendas` e `agente-estoque`, ambos de dezenas
de arquivos "sujos" para **0**.

> ⚠️ **O `--global` é por usuário/máquina, e são duas máquinas.** O Cowork remoto
> tem o `~/.gitconfig` dele, separado do Git Bash do Windows: configurar num não
> configura o outro.
>
> ⚠️ **Na sessão Cowork remota é POR SESSÃO, não uma vez.** O container é efêmero:
> cada sessão nova nasce com `~/.gitconfig` limpo. Sintoma clássico — um Claude vê
> o parque limpo e outro vê 28 repos sujos, no mesmo instante, e **os dois estão
> certos** (aconteceu em 19/08 entre a conta pessoal e a Maná-Dev). **Antes de
> varrer o parque numa sessão remota, rode `git config --global core.autocrlf` e
> confira: vazio = sete `input` primeiro, senão o relatório sai cheio de fantasma.** E máquina antiga não herda o POP — na hub (18/08) o
> `core.autocrlf` estava **vazio no global e em todos os repos**, embora o POP de
> passagem de bastão exija a linha desde a Fase 2.4. Em máquina já rodando,
> confira: `git config --global core.autocrlf` (vazio = você tem o problema).

## Correção — repo (vacina, para repo com mais de uma máquina)

O `.gitattributes` viaja com o repo e vale para todo mundo que clonar, inclusive
quem nunca ouviu falar de `autocrlf`:

```bash
printf '* text=auto\n' > .gitattributes
git add .gitattributes && git commit -m "chore: normaliza fim de linha (LF no repo)"
```

Como o HEAD já guarda LF, isso **não gera churn** — e o commit tem 1 arquivo.
Vale a pena nos repos compartilhados (ex.: os que o Dayan também clona).

## ⚠️ As duas lições caras

**1. Nunca commite uma varredura "suja" em lote.** Em 18/08 quase saiu um
`git add -A && commit` nos ~20 repos dirty: teria empurrado milhares de linhas
falsas, inclusive para dentro de repo de outro dev, escondendo as mudanças reais
(que estavam em apenas 6 repos: km, obra, mapa-pedidos, secretaria,
bartermanager, UBS). Separe FANTASMA de REAL **antes** de qualquer commit.

**2. Nunca rode `git checkout -- .` para "limpar" o CRLF.** Era a correção
antiga desta memória e ela destrói trabalho: em 09/08, na máquina-hub, o
checkout apagou uma edição recém-feita e não commitada (`_github_client.py`).
Com `core.autocrlf input` **o checkout deixa de ser necessário** — é por isso
que a cura mudou.

## Bônus: locks órfãos

`.git/index.lock` / `.git/HEAD.lock` / `.git/ORIG_HEAD.lock` sobrando travam
add/commit/pull com `Another git process seems to be running` ou
`fatal: cannot lock ref 'HEAD'`. Na Maná quase sempre é o Obsidian Git segurando
o ManaVault. Remova no Git Bash (o sandbox do Cowork não consegue, por permissão
do mount):

```bash
rm -f .git/*.lock
```
