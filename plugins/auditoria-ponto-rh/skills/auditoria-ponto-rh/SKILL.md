---
name: auditoria-ponto-rh
description: >
  Gera um aplicativo HTML completo de auditoria de espelho de ponto trabalhista para RH.
  Use sempre que o usuario pedir para analisar, auditar ou verificar registros de ponto,
  espelhos de ponto, fechamento de ponto, banco de horas, jornada de trabalho, horas extras,
  inconsistencias trabalhistas, ou qualquer tarefa relacionada a controle de ponto e
  conformidade com CLT ou CCT. A skill entrega um unico arquivo HTML autocontido sem servidor
  que importa PDFs do JasperReports relFolhaPonto, extrai dados de cada colaborador, aplica
  todas as validacoes da CLT e CCT vigente, e exibe dashboards, relatorios por departamento,
  fichas individuais e modulos de justificativa prontos para uso no navegador. Acionar tambem
  para pedidos como analisar ponto, verificar horas extras, checar conformidade trabalhista,
  auditar PDFs de ponto, banco de horas negativo, e similares.
---

# Auditoria de Ponto — RH

Esta skill produz **um único arquivo `auditoria_ponto.html`** — 100% client-side, sem backend, sem instalação — que implementa um sistema completo de auditoria de espelho de ponto para empresas brasileiras, com foco na CCT de Armazéns Gerais GO (MR071570/2025) e na legislação trabalhista federal vigente.

---

## O que entregar

Um arquivo HTML único com todo o CSS e JavaScript embutidos. Ao abrir no navegador Chrome/Edge/Firefox (110+), o usuário consegue:
1. Importar PDFs de espelho de ponto (JasperReports `relFolhaPonto`)
2. Ver o dashboard com métricas e gráficos de inconsistências
3. Navegar por departamento, por colaborador e por tipo de ocorrência
4. Justificar e solicitar ajustes diretamente na interface
5. Exportar Excel e PDF de qualquer módulo

Sempre leia `assets/auditoria_ponto.html` — ele é o artefato final completo e testado. Entregue-o diretamente ao usuário via `present_files`. **Não reescreva do zero** a menos que o usuário peça mudanças estruturais — apenas aplique as modificações solicitadas sobre o arquivo existente.

---

## Estrutura do arquivo de referência

O arquivo `assets/auditoria_ponto.html` contém:

### Identidade visual — Sementes Maná
- Paleta verde escuro: `--green-main: #2d7d2d`, `--green-dark: #1e5e1e`, `--green-mid: #3a9a3a`
- Fundo escuro: `--bg: #0e1a0e`
- Fonte: Nunito (títulos) + IBM Plex Mono (dados numéricos)
- Banner da empresa embutido em base64 (entre `<nav>` e `<main>`)
- Logo no canto superior esquerdo do header

### Stack CDN (client-side)
```
PDF.js 3.11.174    → extração de texto dos PDFs
XLSX 0.18.5        → exportação Excel
Chart.js 4.4.1     → gráficos
Nunito + IBM Plex Mono → fontes (Google Fonts)
```

### 6 Módulos (abas)
| Aba | Função |
|-----|--------|
| 📂 Importação | Drag-and-drop de PDFs; dedup por SHA-256; barra de progresso |
| 📊 Dashboard | Stats, gráfico de barras por regra, pizza por severidade, filtro multi-departamento |
| 🏢 Por Departamento | Inconsistências com dados do ponto do dia; campos de justificativa |
| 👤 Por Colaborador | Tabela diária detalhada; gráfico BH; exportar Excel+PDF |
| ⚠ Marcações Atípicas | Dias com ≠ 4 batidas; validação humana |
| 🔄 Desvios de Turno | Entradas com desvio > 30 min do turno cadastrado |

---

## Parser de PDF — regra crítica

O PDF.js retorna cada coluna da tabela como **item de texto separado**. O parser deve trabalhar **linha por linha** (não com regex multi-linha), detectando:

### Formato dos itens PDF.js (cada um vira uma linha após `join('\n')`)
```
Funcionário:          ← label sozinho (PDF.js separa label de valor)
ADRYAN LUCAS MARTINS  ← valor (pode continuar na linha seguinte)
OLIVEIRA              ← overflow do nome
...
Horário:              ← label
15:00 às 23:20 - 2º turno (SML)  ← valor
...
Seg - 26/05           ← início de linha de dia
14:50 19:30 20:32 23:08  ← marcações (coluna separada)
07:16                 ← trab
07:20                 ← carga horária
Adicional noturno...  ← ocorrências
```

### Estratégia do parser (`parseColaboradorFromText`)
Para cada campo do header: tentar match **na mesma linha** primeiro (formato pdfplumber/mesclado), depois **label sozinho → valor na próxima linha** (formato PDF.js separado).

Para dias: DAY_RE = `/^(Seg|Ter|Qua|Qui|Sex|S[aá]b|Dom)\s*[-–]\s*(\d{2}\/\d{2})\s*(.*)/i` — quando encontra, abre acumulador de linhas; fecha no próximo dia ou em `STOP_RE = /^(Geral|Carga hor|Assinatura|P[aá]gina\s+\d)/i`.

`_buildDay`: tokens que são `\d{1,2}:\d{2}*?` no início = dados estruturais (marcações+trab+carga); primeiro token não-tempo = início das ocorrências (preservar tudo a partir daí, inclusive horários dentro das ocorrências).

### Contagem de campos estruturais
```
≥ 6 tokens → 4 marcações + trab + carga
5 tokens   → 4 marcações + trab
4 tokens   → 3 marcações + trab
3 tokens   → 2 marcações + trab
2 tokens   → 1 marcação  + trab
1 token    → só trab
0 tokens   → só ocorrências (folga, feriado, etc.)
```

---

## Regras de validação implementadas

### CLT / TST
| Código | Regra | Severidade |
|--------|-------|-----------|
| V01 | Jornada diária > 10h | 🔴 Crítico |
| V02 | Intervalo intrajornada insuficiente (< 60 min p/ jornada > 6h) | 🔴 Crítico |
| V03 | Intervalo interjornada < 11h | 🔴 Crítico |
| V04 | Mais de 2h extras no dia | 🔴 Crítico |
| V05 | Trabalho no domingo sem folga compensatória | 🔴 Crítico |
| V06 | Trabalho em feriado nacional sem compensação | 🟡 Atenção |
| V07 | Horário noturno (22h–05h) sem Adicional Noturno registrado | 🔴 Crítico |
| V08 | Falta injustificada em dia útil com carga prevista | 🟡 Atenção |
| V09 | Ponto britânico (≥ 5 dias consecutivos com entrada+saída idênticos) | 🔴 Crítico |
| V10 | Banco de horas negativo por mais de 30 dias | 🟡 Atenção |
| V11 | Marcações atípicas (quantidade ≠ 4 batidas) | 🔵 Informativo |
| V12 | Desvio de turno cadastrado (diferença > 30 min) | 🟡 Atenção |

### CCT 2025/2026 — Armazéns Gerais GO (MR071570/2025)
| Código | Regra | Severidade |
|--------|-------|-----------|
| CCT01 | Créd. BH diário > 2h em dia útil (Cláusula 17ª, §4º) | 🔴 Crítico |
| CCT02 | Saldo BH > 40h próximo ao encerramento (31/10/2026) | 🟡 Atenção |
| CCT06 | Extensão de jornada fora do período de safra (out–dez) sem previsão | 🟡 Atenção |
| CCT08 | HE > 2h sem pausa de lanche registrada (Cláusula 9ª) | 🟡 Atenção |
| CCT09 | Trabalho no Dia do Armazenista (último dia útil de outubro) | 🟡 Atenção |

---

## Como modificar o arquivo

Ao receber pedidos de ajuste, sempre:
1. Ler o arquivo com `view /tmp/auditoria-ponto-rh/assets/auditoria_ponto.html` (ou o path atual)
2. Identificar a seção exata a alterar
3. Usar `str_replace` para mudanças cirúrgicas, ou reescrever seções completas via `bash_tool`
4. Após qualquer alteração de JavaScript: validar com `node --check` antes de entregar
5. Copiar para outputs e apresentar com `present_files`

### Validação obrigatória antes de entregar
```bash
python3 -c "
import subprocess, tempfile, os
with open('auditoria_ponto.html') as f:
    html = f.read()
js = html[html.find('<script>')+8:html.rfind('</script>')]
with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
    f.write(js); tmp = f.name
r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
os.unlink(tmp)
print('✅ JS válido' if r.returncode == 0 else '❌ ERRO: ' + r.stderr[:500])
"
```

---

## Persistência e sessão

- `localStorage` chave `auditoria_ponto_v3` guarda colaboradores, justificativas, hashes de arquivos já importados
- Botões no header: Importar Sessão (JSON) / Exportar Sessão (JSON) / Limpar Dados
- Dedup de PDFs via `crypto.subtle.digest('SHA-256')` — mesmo arquivo com nome diferente é detectado

---

## Feriados nacionais hardcoded
`['01/01','21/04','01/05','07/09','12/10','02/11','15/11','20/11','25/12']`

Dia do Armazenista: `lastWorkdayOctober(year)` — último dia útil de outubro.

---

## Erros frequentes a evitar

1. **Sintaxe JS quebrada**: Todo `inconsistencias.push({rule:..., detail:\`...\`})` precisa de `}` encerrando o objeto e `)` encerrando o `push(`. Sempre validar com `node --check`.

2. **Parser trava o browser**: Nunca usar regex com flag `/gs` em texto de página inteira. Usar sempre a estratégia linha-a-linha com DAY_RE.

3. **Imagens base64**: O banner (`data:image/jpeg;base64,...` com ~54KB) e a logo (~5KB) são JPEG mesmo com extensão .png. Verificar com `file` antes de embutir.

4. **Banner cortado**: Usar `aspect-ratio: 1128/191` (dimensões reais do banner) com `background-size: contain` — não `height` fixo com `cover`.

5. **Filtro de departamento vazio**: `populateDeptSelects()` deve ser chamado tanto no `renderAll()` quanto ao ativar a aba Por Departamento.
