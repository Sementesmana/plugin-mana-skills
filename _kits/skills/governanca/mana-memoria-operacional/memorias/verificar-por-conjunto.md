---
data: 2026-08-18
origem: máquina-hub (Xayer) — importação de 94 arquivos de memória para a org Team
verificado: sim
---

# Conferir por diff de conjuntos, nunca por contagem

## Sintoma

A conferência declarou "**100 arquivos, zero órfãos**" e estava errada: existia **1 link
quebrado** no índice. A conta fechou (94 importados + 5 seeds + 1 índice = 100) porque um
arquivo faltando e uma linha sobrando **se cancelam na soma**.

## Causa

Contagem aritmética prova cardinalidade, não identidade. Dois erros de sinal oposto zeram
o sintoma — o número fica bonito e o conjunto continua errado.

## Correção

Comparar as **duas listas, item a item**, nos dois sentidos:

- **Órfão** = existe mas não está no índice → `comm -23 <(sort reais) <(sort indexados)`
- **Link quebrado** = está no índice mas não existe → `comm -13 <(sort reais) <(sort indexados)`
- **Duplicata no índice** → `sort indexados | uniq -d`

Reportar **os dois lados mesmo quando vazios** ("0 órfãos, 0 quebrados") — silêncio não
prova checagem. Contagem serve só como sinal secundário.

## Onde aplicar

Memória do Cowork, `_index.md` do vault, ADRs, arquivos migrados entre contas/máquinas,
registros carregados no banco, plugins × repos do marketplace. Qualquer pergunta na forma
"**está tudo lá?**".

## Corolário

Número que bate fácil demais merece desconfiança, não alívio — mesma família do
`falha-nao-vira-dado.md`, onde o valor certo significava a coisa errada.
