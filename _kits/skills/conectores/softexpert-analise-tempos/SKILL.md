---
name: softexpert-analise-tempos
description: >-
  Receita completa para medir TEMPO por atividade em qualquer processo do
  SoftExpert Workflow, a partir da WFHISTORY (não da WFSTRUCT, que é estado e
  zera no retrabalho). Traz a query do Conjunto de Dados pronta, a decodificação
  do fgtype, o algoritmo de reconstrução de passagens e trechos por executor, o
  motor de horas úteis (jornada, almoço, feriados) e os padrões de painel
  (Kanban do funil, drill processo→passagem→executor). Use SEMPRE que alguém
  pedir: quanto tempo cada etapa demora, onde o processo está parado, aging,
  gargalo, tempo médio de execução, retrabalho, quem segurou a atividade, SLA
  do processo, produtividade por executor, funil do CRE/CPR/NF. Também quando
  mencionar WFHISTORY, WFSTRUCT, duration_wf, fgtype, dhhistory, atvsch,
  passagem, trecho, tempo útil, horas úteis, parado há, ou quando o relatório
  padrão do SE "mede errado". Nasceu do CRE-001 (agente-pedidos, 2026-08-12) e
  é replicável para qualquer cdProcessModel.
---

# Análise de tempos do SoftExpert Workflow

> **Lógica:** o SoftExpert sabe quanto tempo cada atividade levou, mas o
> relatório padrão mente quando há retrabalho — ele lê a `WFSTRUCT`, que é
> tabela de **estado** e é sobrescrita quando a atividade reabre. A verdade
> está na `WFHISTORY`, que é log e guarda tudo. Esta skill é a receita de
> transformar esse log em métrica confiável.

## Quando usar

- "Quanto tempo demora cada etapa do processo X?"
- "Onde o processo está parado agora e há quanto tempo?"
- "Qual etapa é o gargalo?" / "Quem segurou essa solicitação?"
- Montar funil/Kanban de um processo do SE com tempo por etapa
- Medir retrabalho (quantas vezes o processo voltou para a mesma etapa)
- Qualquer painel que hoje usa o `duration_wf` do relatório padrão do SE

## Regra zero: WFSTRUCT é estado, WFHISTORY é histórico

A `WFSTRUCT` tem **1 linha por atividade do processo**, sobrescrita a cada
reabertura. Confirmado empiricamente:

```sql
SELECT idProcess, nmStruct, COUNT(*)
  FROM WFSTRUCT WHERE fgType IN (2,3)
 GROUP BY 1,2 HAVING COUNT(*) > 1
-- volta VAZIO
```

Logo o `duration_wf` (`dhExecution - dhEnabled` da WFSTRUCT) mede **só a última
passagem**. Num processo que voltou 4 vezes para a mesma etapa, ele mostra a
4ª e esconde as outras três. **Nunca use para medir fluxo.**

## Passo 1 — Conjunto de Dados no SE

Monte um Conjunto (DI006, fonte SESUITE) com esta query. Troque o
`cdProcessModel` pelo do seu processo:

```sql
SELECT
    h.idprocess AS idobjeto,
    w.idProcess AS nrprocesso,
    w.nmprocess,
    h.idstruct,
    h.nmstruct,
    h.fgtype,
    h.dhhistory,
    h.nmuser,
    h.nmrole,
    h.nmaction,
    h.dscomment
  FROM WFHISTORY h
 INNER JOIN WFPROCESS w
    ON w.idObject = h.idprocess
 WHERE w.cdProcessModel = 1        -- <<< o SEU processo
   AND w.fgWfGroup = 1
   AND h.fgtype IN (6, 9, 12, 17, 48)
```

Leia por REST (`dataset-integration`) — ver skill `softexpert-dataset-integration`
para o transporte (Authorization **sem** `Bearer`, fonte SESUITE, corta em 10k).

**Armadilhas que custam tempo:**

| Armadilha | Sintoma | Regra |
|---|---|---|
| `;` no fim da query | `syntax error at or near ";"` | o wizard embrulha a query — nunca terminar com `;` |
| `idprocess` é **citext** | `operator does not exist: citext = integer` | comparar com string: `= '354'`, não `= 354` |
| `idprocess` ≠ número da tela | junta errado | `WFHISTORY.idprocess` = `WFPROCESS.idObject` (interno). O número que o usuário vê (`000028`) é o `idProcess` |
| Sem filtro de modelo | vem o histórico do SE inteiro | sempre `INNER JOIN WFPROCESS` + `cdProcessModel` |

## Passo 2 — Decodificação do `fgtype`

Validado contra a tela do SE:

| fgtype | Significa |
|---|---|
| **6** | atividade **habilitada/atribuída** (`nmrole` preenchido quando cai em papel/fila) |
| **9** | atividade **executada** (`nmaction` = a ação escolhida) |
| **12** | "Executor alterado" — troca **com** justificativa |
| **48** | "transferiu a tarefa" — troca **sem** justificativa |
| **17** | "retornou a instância" — devolução formal, motivo no `dscomment` |
| 16 | atividade cancelada |
| 13 | execução de atividade **sistêmica** |
| 1 | criação do processo |
| 67 | documento anexado (costuma ser a maioria das linhas — filtrar fora) |

Placeholders do `dscomment` na troca de responsável:
`{{214632}}` = responsável anterior · `{{214617}}` = novo responsável ·
`{{101072}}` = justificativa.

## Passo 3 — Reconstruir as passagens (o algoritmo)

**Passagem** = uma estadia do processo numa atividade. Abre no `6` e fecha no
**primeiro evento seguinte do MESMO PROCESSO** — o `9` dela **ou** o `6` de
outra atividade.

> ⚠️ **O erro clássico:** fechar a passagem só no `9` da própria atividade.
> Isso infla o número. Caso real: "Validar Documentação" habilitou 27/04, o
> processo foi para "Ajustar Crédito" em 28/04 e voltou em 29/04. Pelo par
> 6→9 daria **uma** passagem de 27/04 a 05/05, cobrando de Validar o tempo em
> que o processo estava em outra etapa. São **duas** passagens.

**Trechos:** `12`/`48` **não** encerram a passagem — fecham o **trecho** do
responsável atual e abrem outro. Assim o tempo vai para quem estava com a
atividade na mão, não para quem apertou o botão no fim.

**Guarda obrigatória:** se o `dscomment` disser um "responsável anterior" que
não bate com quem você acha que estava com a atividade, **não fatie** (registre
e siga com o original). Menos detalhe é melhor que detalhe errado.

Outras regras que a experiência impôs:

- **Só atividades humanas.** Fora as sistêmicas e os gateways (nome terminando
  em `?`). Mantenha a lista de sistêmicas em constante, não espalhada.
- **Concluída e em curso NUNCA na mesma média.** O tempo de quem está em curso
  só cresce e não é comparável.
- **Passagem instantânea** (tempo zero) conta como passagem, mas fica fora da
  média.
- **Premissa:** fluxo sequencial. Atividade paralela seria contada a menor —
  se o processo tiver AND/paralelo, tratar explicitamente.
- **Reincidência** = a mesma atividade aparecendo N vezes no mesmo processo. É
  o indicador de retrabalho e sai de graça da contagem de passagens.

## Passo 4 — Tempo ÚTIL (e o que o número significa)

> **Escreva esta frase antes de escrever a fórmula:**
> o número mede **ATRASO EM TEMPO DE EXPEDIENTE**, não quanto a pessoa trabalhou.

A diferença decide o cálculo. Com essa definição, uma atividade executada às
19h **não atrasou o processo** (ele ia esperar o dia seguinte de qualquer jeito)
e conta **zero** — e isso está certo. Creditar tempo fora de hora faz a
atividade esquecida aberta a noite toda **acumular** tempo que ninguém gastou.

O SE só aplica calendário de expediente quando a atividade tem **SLA
configurado**. Sem SLA, o `dhhistory` é corrido puro e o desconto tem que ser
feito no consumidor.

Módulo de referência: `tempo_util.py` do `agente-pedidos`. Jornada por env
(`JORNADA_INICIO`, `JORNADA_FIM`, `ALMOCO_INICIO`, `ALMOCO_FIM`,
`FERIADOS_EXTRA`), feriados nacionais + estaduais calculados sem dependência
externa (móveis derivadas da Páscoa por Meeus/Butcher). Almoço desligado =
`ALMOCO_INICIO == ALMOCO_FIM`.

**Exiba o corrido ao lado do útil.** O útil é atraso de expediente; o corrido é
o que o cliente sente. Os dois juntos evitam discussão.

## ☠️ Passo 4b — FUSO HORÁRIO (o bug mais caro desta receita)

O `dhhistory` vem em **epoch ms (UTC)**. Converter com `datetime.fromtimestamp()`
sem fuso usa o TZ do contêiner — e **Railway roda em UTC**. Resultado: tudo 3h
adiantado no Brasil.

**E não é cosmético.** A janela de expediente é aplicada em cima da hora torta,
então trabalho das 9h vira "dentro do almoço" e trabalho das 15h vira "depois
das 17h". No caso real isso gerou um diagnóstico inteiro **falso** ("o time
trabalha no almoço e até 20h") e uma alteração de código que teve de ser
revertida.

```python
from zoneinfo import ZoneInfo
_TZ = ZoneInfo(os.environ.get("TZ_PAINEL") or "America/Sao_Paulo")

def de_epoch_ms(valor):
    return datetime.fromtimestamp(int(valor) / 1000.0, tz=_TZ).replace(tzinfo=None)

def agora():
    """Mesmo fuso — senão o aging do que está aberto sai deslocado também."""
    return datetime.now(tz=_TZ).replace(tzinfo=None)
```

**Teste obrigatório antes de calcular qualquer coisa:** pegue **um** registro,
abra o balão do fluxograma no SE e confira o horário contra o seu. Um minuto de
trabalho; teria evitado três rodadas de retrabalho.

## Passo 5 — Precisão e rótulo

- Arredonde horas em **4 casas** (0,36 s). Duas casas dá granularidade de 36 s
  e não distingue 1 min de 6 min — e boa parte das passagens é de **minutos**.
- Rótulo que **escala com a grandeza**, senão "0,1 h" não diz nada:

| Grandeza | Rótulo |
|---|---|
| < 1 min | `<1 min` |
| < 1 h | `6 min` |
| < 1 jornada | `2h 15min` |
| ≥ 1 jornada | `3,4 d` (dia = jornada útil, **não** 24 h) |

## Passo 6 — Ruído que deve sair da análise

**Processo cancelado sai INTEIRO**, não só a passagem do cancelamento. Um
processo aberto e cancelado em 2 minutos não diz nada sobre a velocidade da
etapa, e as etapas anteriores de algo que morreu também não medem fluxo
saudável. Detecte pela ação (`nmaction ~ /cancel/i` no `fgtype 9`) e transforme
em **indicador próprio** — cancelamento é informação de gestão, não lixo.

**Nunca deixe uma flag significar duas coisas.** Separe:

- `instantanea` — durou zero de verdade
- `fora_expediente` — aconteceu inteira fora da janela (tempo útil zero, mas
  houve tempo de relógio)

São opostos. Misturados, o rótulo mente e o dono tira a conclusão errada —
aconteceu de verdade: acharam que os zeros eram cancelamento.

## Passo 7 — Padrões de painel que funcionaram

**Kanban do funil.** Uma coluna por etapa, na ordem do processo. No card, dois
blocos **separados**: "parados agora" (quantos, esperando há quanto tempo em
média / o mais antigo / o mais novo) e "histórico" (média, mediana, mais rápido,
mais demorado dos concluídos). Juntar os dois numa média só faz a etapa parecer
mais rápida do que é.

**Drill em três níveis**, do clique no card:

```
processo   (tempo somado, cadeia de mãos, selo "4×" de retrabalho)
  └─ passagem   (ordem CRONOLÓGICA — a ordem do retrabalho é a informação)
      └─ executor  (tempo do trecho + % dentro da passagem)
```

O **percentual do trecho** é o que responde "fulano só repassou" batendo o olho
(ex.: `Lorena 4,0 d (5%) · José 76,7 d (95%)`).

**Filtro Tudo | Em curso | Concluídos** na lista, com o cabeçalho da coluna
virando "Parado há" no modo em curso. E o bloco por responsável **recortado pela
etapa selecionada** — clicou em "Validar Documentação", aparecem só quem passou
por ela.

**Réguas de cor diferentes por nível:** a linha do processo compara com a
mediana dos totais por processo; a sub-linha com a mediana das passagens. Régua
única pintaria todo processo com retrabalho de vermelho.

**Dispersão (strip plot)** das passagens concluídas com a mediana marcada — mostra
num relance se a etapa é estável ou se tem cauda puxando a média.

## ⚠️ Leitura política do número

O bloco por responsável mede **onde o processo esteve, não culpa**. Boa parte do
tempo pode ser espera de documento do cliente. O rótulo no painel deve dizer
"sob responsabilidade de", nunca "demorou". Combine isso com quem vai ler o
painel **antes** de publicar — é a diferença entre uma ferramenta de gestão e
uma fonte de atrito.

## Checklist para aplicar num processo novo

1. [ ] Descobrir o `cdProcessModel` e criar o Conjunto com a query do Passo 1
2. [ ] Dar permissão de visualização do Conjunto ao token do agente
3. [ ] Conferir **um** horário contra o balão do fluxograma do SE (fuso!)
4. [ ] Mapear as atividades **sistêmicas** e os gateways para excluir
5. [ ] Escrever a frase do que o número responde e validar com o dono
6. [ ] Confirmar a jornada — e **conferir contra o histórico**, não só perguntar
7. [ ] Definir o funil (ordem das etapas) e os esclarecimentos entre parênteses
8. [ ] Cachear no data lake (skill `mana-habilidade-data-lake-pg`), lake-first
9. [ ] Rodapé do painel explicando a régua em duas frases

## Implementação de referência

`agente-pedidos` — `/api/tempos` + `tempo_util.py` + aba Indicadores do
`/painel-reais`. Nota do vault: `ManaVault/06-Agentes-e-Skills/agente-pedidos.md`
(seções de 2026-08-12). Conjunto `atvsch` no SE, CRE-001.

**Skills irmãs:** `softexpert-dataset-integration` (transporte REST),
`mana-habilidade-se-dataset-reader` (reader pronto),
`mana-habilidade-data-lake-pg` (cache), `softexpert-wf-ws` (escrita no SE).
