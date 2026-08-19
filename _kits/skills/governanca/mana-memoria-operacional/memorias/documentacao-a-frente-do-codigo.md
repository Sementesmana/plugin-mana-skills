---
data: 2026-08-19
origem: varredura dos 62 repos do parque Maná (chat-mãe Maná OS, 18–19/08)
verificado: sim
---

# Documentação à frente do código: quando a nota diz "pronto" e o repo não tem

## Sintoma

A nota do vault (ou a SKILL) descreve uma funcionalidade em detalhe, com data e tudo —
e o repositório não tem o código. Ninguém mente: o trabalho foi feito, a nota foi
escrita na mesma sessão, e o `git add` levou só parte.

Na varredura de 18–19/08 isso apareceu **quatro vezes**, com atrasos de 13 dias a 2 meses:

| Agente | O que ficou fora | Atraso | Consequência real |
|---|---|---|---|
| `agente-bartermanager` | `relatorios.py` + testes (871 linhas) | 13 dias | 7 rotas chamadas pelo front devolvendo 404; dashboard de lavoura **exibindo zero** por causa de um `.catch(()=>({}))` |
| `agente-mapa-pedidos` | lake-first + retry 452 (`sa_client.py`) | 1 mês | painel continuou vulnerável ao 452 que o código já resolvia |
| `agente-obra` | migração PostgreSQL inteira | 2 meses | nota prometia "base única compartilhada"; produção rodava build sem banco |
| `agente-km` | SKILL v3 (393 linhas) | 3 meses | limitação do SOAP na grid do SE documentada só no disco |

## Causa

Duas somadas:

1. **O `git status` estava soterrado em diff fantasma de CRLF** — 20+ repos apareciam
   sujos, então "sujo" deixou de significar alguma coisa e ninguém olhava.
   (Ver `git-crlf-fantasma-e-checkout.md`.)
2. **Não havia rito de fechamento.** A tarefa terminava quando o código funcionava,
   não quando estava versionado.

## Correção

**A regra do fechamento** (instituída pelo Xayer em 18/08): ao fim de toda tarefa não
trivial, perguntar **explicitamente** se sobe pro Git — com o comando pronto — e
atualizar a nota do vault e a SKILL junto. Fechamento é `push`, não "funcionou".

**A varredura periódica**, para pegar o que já escapou:

```bash
cd /c/Users/<voce>/Desktop/ORQUESTRADOR
for d in */; do
  [ -d "$d/.git" ] || continue
  s=$(git -C "$d" status --porcelain 2>/dev/null | wc -l); [ "$s" = "0" ] && continue
  r=$(git -C "$d" diff --ignore-cr-at-eol --stat 2>/dev/null | wc -l)
  [ "$r" = "0" ] && echo "FANTASMA  $d ($s)" || echo "REAL      $d ($s)"
done
```

**Onde a nota está à frente, ela é o mapa do que falta.** Não apague a seção nem
"corrija" a data: leia como especificação do que precisa entrar, confira contra o
código e commite. Foi assim que os quatro casos fecharam.

## Antes de commitar trabalho represado — as 3 conferências

Código velho reencontra uma base que andou. Verifique, nesta ordem:

1. **`git fetch` primeiro.** Ler o `git log` local levou a afirmar que um dono não
   tinha commits — ele tinha quatro. Log local não é verdade, é cache.
2. **As dependências que o código usa estão no `requirements.txt`?** No `Agente-UBS`,
   `app.py` importava `requests` sem ele nos requirements: a função caía num
   `except Exception` genérico e toda sugestão era salva sem a explicação, com um
   `log.warning` que ninguém lia.
3. **Colide com o que entrou depois?** Confira rotas, models e imports contra
   `origin/main`. No Barter, o próprio cabeçalho dos blueprints do dono dizia
   *"NÃO portado nesta fase"* — o código dele estava esperando o arquivo represado.

## Não faça

- **Não commite a varredura suja em lote.** Separe FANTASMA de REAL antes.
- **Não empurre em repo de outro dono sem avisar** — o push dispara auto-deploy e
  reinicia a produção dele. Avise antes, principalmente se o dono for não-dev.
- **Não confie no nome do arquivo.** `SKILL-v3.md`, `SKILL.md` e `_old/SKILL-v2.md` do
  `agente-km` tinham o mesmo md5: eram cópias, não versões. Compare conteúdo.
