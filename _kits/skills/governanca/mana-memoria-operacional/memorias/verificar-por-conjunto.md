---
data: 2026-08-18
atualizado: 2026-08-22
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

## Conjunto completo não garante conteúdo fresco (2026-08-22)

**Sintoma.** Na conferência do one-way pro Claude Team o placar fechou: 99/99 itens
depois de restaurar 5 do backup, zero link quebrado, zero duplicata. E a memória do
452 do Simple Agro ainda era a de julho — sem o gateway em produção, sem a API que
mente. **O conjunto estava íntegro e o conteúdo estava velho.**

**Causa.** Diff de conjuntos compara **nomes**. Arquivo com o nome certo e conteúdo
defasado passa limpo nos dois sentidos do `comm`.

**Correção.** Além do diff, definir uma **prova de frescor**: uma pergunta cuja
resposta certa só existe se a atualização mais recente tiver chegado ("o que a memória
diz sobre X?", com X mudado na última semana). Escrever a prova **junto com as
contagens, antes da migração**, e anotar a resposta esperada — depois já não se sabe o
que era novo.

**E quando a prova falhar, achar onde nasceu a defasagem antes de culpar o transporte.**
Neste caso o mesmo arquivo já estava velho **dentro do backup**: não foi a migração que
perdeu, foi a atualização que nunca havia sido gravada. Conferir o artefato de origem,
não só o destino.

**Corolário.** Contagem prova cardinalidade; diff de conjuntos prova identidade;
**só a prova de frescor prova conteúdo.**
