---
data: 2026-08-09
origem: maquina-hub (agente-monitor e plugin-mana-skills)
verificado: sim
---

# Git no Windows: modificações fantasma de CRLF — e o perigo do checkout

## Sintoma

`git status` mostra arquivos modificados que ninguém editou. O diff parece a
reescrita do arquivo inteiro (todas as linhas `-` e `+` iguais). Aconteceu
com 5 arquivos no agente-monitor e 8 no plugin-mana-skills.

## Causa

O Windows gravou fim de linha CRLF onde o Git guarda LF. O conteúdo é
idêntico; só o terminador mudou. Qualquer app/editor do Windows que toque o
arquivo dispara isso.

## Como confirmar que é fantasma (antes de qualquer limpeza)

```bash
python3 - <<'EOF'
import subprocess
CRLF=b"\r\n"; LF=b"\n"
for f in subprocess.run(['git','diff','--name-only'],capture_output=True,text=True).stdout.split():
    disco = open(f,'rb').read()
    git = subprocess.run(['git','show','HEAD:'+f],capture_output=True).stdout
    print(("FANTASMA " if disco.replace(CRLF,LF)==git.replace(CRLF,LF) else "REAL     ") + f)
EOF
```

## Correção

```bash
git config core.autocrlf true    # neste repo; evita repetir
git checkout -- .                # SÓ depois da conferência acima
```

## ⚠️ A lição cara

**Nunca rode `git checkout -- .` enquanto o Claude estiver editando arquivos
do mesmo repo.** Na máquina-hub, a limpeza do CRLF apagou uma edição recém-
feita e não commitada (2026-08-09, `_github_client.py`). Sequência segura:
Claude termina e avisa → conferência de fantasma → checkout → Claude segue.

## Bônus: locks órfãos

`.git/ORIG_HEAD.lock` / `index.lock` sobrando travam pull/push com "Another
git process seems to be running". O sandbox do Cowork NÃO consegue removê-los
(permissão do mount) — remova no Git Bash: `rm -f .git/*.lock`.
