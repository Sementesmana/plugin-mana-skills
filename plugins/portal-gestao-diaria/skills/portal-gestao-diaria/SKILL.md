---
name: portal-gestao-diaria
description: |
  Cria, mantém e evolui o Portal de Gestão Diária Financeira da Sementes Maná — um HTML single-file (~3.300 linhas, 91 funções JS) que integra exportações do TOTVS Datasul (SE1/SE2/APF) para gerir Contas a Receber, Contas a Pagar, Caixa, Adiantamentos, DRE Parcial, Plano de Ação, Aging Report, Checklists e Histórico. USE SEMPRE que Felipe ou a equipe Maná mencionar: portal, gestão diária, portal diário; CR, CP, contas a receber/pagar no portal; aging, aging report, carteira de recebíveis; importar TOTVS/Excel/.xlsx; chips/filtro de tipo e status; projeção do dia, NCG, saldo projetado, realizado; plano de ação, pendências, responsável, prazo; checklist CR/CP; anexar arquivo, preview, download; salvar dia, exportar/carregar JSON; histórico consolidado; o arquivo gestao-financeira-mana.html; ou qualquer nova aba, filtro ou funcionalidade no portal.
---

# Portal de Gestão Diária — Sementes Maná

Sistema financeiro completo em HTML single-file (~3.300 linhas, 91 funções JS).
Persistência via localStorage + JSON export/import para pasta de rede compartilhada.
Integra com exportações do TOTVS Datasul (módulos SE1/SE2/APF).

---

## Arquitetura Geral

### Arquivo de saída
`gestao-financeira-mana.html` — abre direto no browser, sem servidor.

### Dois modos (toggle no header)
- **📚 Guia** — referência estática (Agenda Semanal, Checklists, KPIs, Papéis, TOTVS, DRE & Fluxo)
- **⚙️ Portal Diário** — ferramenta operacional com persistência

### Estrutura de persistência
```
localStorage key: mana_gestao_diaria_v1

portalData = {
  records: { "YYYY-MM-DD": RecordDiario },
  agingAnnotations: { "tipo_ref_date": AgingAnnotation }  // GLOBAL, fora dos records
}
```

> ⚠️ `agingAnnotations` fica no nível raiz de `portalData` (não dentro de records) para que as anotações do Aging persistam independente da data selecionada e entre operadores.

### Dependências externas (CDN)
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800
     &family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

---

## Design System

### Cores (CSS variables)
```css
--green:  #1D6B3E   /* primária Sementes Maná — CR, ações, positivo */
--green-d:#154d2d
--green-l:#e8f5ee
--amber:  #B8860B   /* CP, adiantamentos, atenção */
--amber-l:#fdf3d7
--red:    #dc2626   /* atraso, NCG negativo, crítico */
--red-l:  #fee2e2
--blue:   #1d4ed8
--blue-l: #dbeafe
--gray-50/100/200/400/600/800
```

### Tipografia
- Corpo: `'Sora', sans-serif` (--font)
- Números/código/datas: `'JetBrains Mono', monospace` (--mono)

---

## Schema Completo do RecordDiario

```javascript
{
  // CR / CP
  cr: [{ id, nome, valor, dt, status, obs, tipo }],
  cp: [{ id, nome, valor, dt, status, obs, tipo }],

  // Caixa
  caixa: { saldo, proj30, cgiro, capt, obs },

  // Adiantamentos (com status desde v2)
  adiantCli:  [{ id, nome, valor, dt, status }],  // status: 'pendente'|'recebido'
  adiantForn: [{ id, nome, valor, dt, status }],  // status: 'pendente'|'pago'

  // Realizados (importação TOTVS, saldo=0)
  realizadoCR: [{ id, nome, razao, valor, dt, dtBaixa, obs }],
  realizadoCP: [{ id, nome, razao, valor, dt, dtBaixa, obs }],

  // DRE parcial
  dre: { receita, cmv, desp, obs },

  // Checklist por seção (V2)
  checklistV2: { "cr_0": true, "cp_1": false, "geral_2": true, ... },

  // Plano de ação
  acoes: [{
    id, acao, responsavel, prazo, status, obs,
    criadaEm, resolvidaEm
  }],
  // status: 'aberta' | 'em_andamento' | 'concluida' | 'cancelada'

  // Documentos anexados
  anexos: [{ id, nome, tipo, tamanho, data (base64), uploadedAt }],

  notas: "string",         // ata livre
  decisions: [],           // legado, mantido por compat
  agingObs: {}             // legado, substituído por portalData.agingAnnotations
}
```

### Schema AgingAnnotation (global, em portalData.agingAnnotations)
```javascript
{
  "cr_000007272_2025-04-30": {
    obs: "texto de observação",
    responsavel: "nome do responsável",
    dataPrevista: "YYYY-MM-DD",
    status: "pendente" | "negociacao" | "prometido" | "juridico" | "acordo" | "resolvido"
  }
}
```
Key: `${agingView}_${r.ref}_${r.dt}` — estável desde que o mesmo arquivo TOTVS seja usado.

---

## Abas do Portal Diário

| Aba | ID Pane | Conteúdo principal |
|-----|---------|--------------------|
| 💰 CR | `pp-cr` | Títulos CR + filtro Status+Tipo + subtotal + edit/limpar |
| 📤 CP | `pp-cp` | Títulos CP + filtro Status+Tipo + subtotal + edit/limpar |
| 🏦 Caixa | `pp-caixa` | Saldo + 2 fileiras NCG (A Realizar / Realizado) |
| 📦 Adiantamentos | `pp-adiant` | Adiant. clientes e fornecedores com status |
| 📊 DRE Parcial | `pp-dre` | Receita / CMV / Despesas + resultado em tempo real |
| ✅ Checklist | `pp-chklist` | 3 seções independentes: CR / CP / Geral |
| 📝 Plano de Ação | `pp-notas` | Tabela de ações + Anexos + Ata livre |
| 📅 Histórico | `pp-hist` | Toggle: Registros Diários | Plano de Ação Consolidado |
| 📊 Aging Report | `pp-aging` | Upload CR+CP xlsx, análise por faixas, top 10, alertas |

---

## Importação TOTVS (openImportModal)

### Colunas lidas — CP (APF050/SE2)
| Campo | Coluna TOTVS |
|-------|-------------|
| nome | `Nome Fornece` |
| razao | `Razao Social` |
| tipo | `Tipo` ← NF/PA/PR/RA/RC… |
| saldo | `Saldo` |
| valor | `Vlr.Titulo` |
| dt | `Vencimento` ← serial Excel |
| dtEmis | `DT Emissao` ← serial Excel |
| obs | `Desc. Nature` |
| baixa | `DT Baixa` ← serial Excel |
| ref | `No. Titulo` |
| parcela | `Parcela` |

### Colunas lidas — CR (ACR050/SE1)
| Campo | Coluna TOTVS |
|-------|-------------|
| nome | `Nome Cliente` (fallback: `Razao Social`) |
| razao | `Razao Social` |
| tipo | `Tipo` |
| saldo/valor/dt/obs/baixa/ref | igual ao CP |

### Conversão serial Excel → ISO
```javascript
function excelSerialToISO(serial) {
  const epoch = new Date(1899, 11, 30);
  return new Date(epoch.getTime() + serial * 86400000).toISOString().slice(0,10);
}
```

### Classificação no import
| Condição | Destino |
|----------|---------|
| `saldo === 0 && dtBaixa !== ''` | `isRealizado` → `realizadoCR/CP` + auto-preenche DRE |
| `saldo > 0 && saldo < vlr && dtBaixa !== ''` | `isParcial` → marcado como Parcial |
| `adiant toggle = S` | `adiantForn` ou `adiantCli` |
| demais | `rec.cr` ou `rec.cp` |

---

## Projeção do Dia / NCG (Aba Caixa)

### Fileira 1 — A Realizar
```
Saldo Projetado = Saldo Bancário Atual
               + CR(status='aberto' | 'atrasado')
               − CP(status='aberto' | 'atrasado')
               + AdiantCli(status='pendente')
               − AdiantForn(status='pendente')
```

### Fileira 2 — Realizado
```
Saldo c/ Realizados = Saldo Bancário Atual
                    + CR(status='recebido')
                    − CP(status='pago')
                    + AdiantCli(status='recebido')
                    − AdiantForn(status='pago')
```

- NCG negativo → card vermelho + alerta `⚠️ NCG: déficit de R$X`
- Atualiza em tempo real ao digitar saldo ou mudar status de títulos/adiantamentos

---

## Checklist — 3 Seções Independentes

```javascript
CHECKLIST_SECTIONS = [
  { id:'cr',    label:'💰 Contas a Receber', cls:'cr',    items: [5 itens] },
  { id:'cp',    label:'📤 Contas a Pagar',   cls:'cp',    items: [5 itens] },
  { id:'geral', label:'🏦 Caixa & Geral',    cls:'geral', items: [5 itens] },
]
```

Estado salvo em `rec.checklistV2` com chaves `"sectionId_index"` (ex: `"cr_0"`, `"cp_3"`).
Compatibilidade retroativa: `PORTAL_CHECKLISTS` é gerado via `flatMap` das seções.

---

## Plano de Ação

### Schema da ação
```javascript
{
  id: timestamp,
  acao: "texto",
  responsavel: "nome",
  prazo: "YYYY-MM-DD",
  status: "aberta" | "em_andamento" | "concluida" | "cancelada",
  obs: "texto",
  criadaEm: "YYYY-MM-DD",
  resolvidaEm: "YYYY-MM-DD"   // preenchido ao concluir
}
```

### Histórico Consolidado
`renderHistConsolidado()` varre todos os records, coleta ações com `status !== 'concluida'` e `!== 'cancelada'`, ordena por urgência (abertas → em andamento → por prazo) e permite atualizar status diretamente sem navegar dia a dia via `updateAcaoFromConsolid(date, id, status)`.

---

## Anexos de Documentos

- Limite: 5MB por arquivo (warning automático)
- Armazenado como base64 DataURL em `rec.anexos[]`
- Preview inline:
  - Imagens (`image/*`) → `<img>`
  - PDFs (`application/pdf`) → `<iframe>`
  - Word/outros → só download
- `previewAnexo(id)` → abre modal `.preview-overlay`
- `downloadAnexo(id)` → cria link temporário com `a.download`

---

## Aging Report

### Faixas
```javascript
AGING_BUCKETS = [
  { key:'corrente', label:'A Vencer',    color:'#1D6B3E', min:-∞, max:0   },
  { key:'b1',       label:'1–30 dias',   color:'#B8860B', min:1,  max:30  },
  { key:'b2',       label:'31–60 dias',  color:'#d97706', min:31, max:60  },
  { key:'b3',       label:'61–90 dias',  color:'#ef4444', min:61, max:90  },
  { key:'b4',       label:'91–180 dias', color:'#dc2626', min:91, max:180 },
  { key:'b5',       label:'>180 dias',   color:'#7f1d1d', min:181,max:∞   },
]
```

### Anotações (GLOBAL — não por data)
```javascript
// Chave estável: tipo_nroTitulo_vencimento
key = `${agingView}_${r.ref}_${r.dt}`

// Salvo em portalData.agingAnnotations (não em records)
// Auto-save no localStorage a cada alteração (não depende de "Salvar Dia")

AgingAnnotation = {
  obs: "",
  responsavel: "",
  dataPrevista: "",
  status: "pendente" | "negociacao" | "prometido" | "juridico" | "acordo" | "resolvido"
}
```

### Filtros na lista completa
- Busca: nome, razão social, natureza
- Chips de Tipo multi-seleção (buildTipoFilter)
- Subtotal + breakdown por faixa quando filtros ativos
- Critérios de alerta: `days > 60` OU `saldo > 50000`

---

## Filtros CR e CP

### Estado
```javascript
tituloFilterState = {
  cr: { status: Set(['aberto','recebido','atrasado','prorrogado']), tipo: Set() },
  cp: { status: Set(['aberto','pago','atrasado','prorrogado']),     tipo: Set() },
}
// tipo Set vazio = todos selecionados
```

### Comportamento
- Status chips sempre visíveis
- Tipo chips aparecem automaticamente quando dados têm tipos (via `buildTituloTipoChips`)
- Subtotal na barra de filtro + `<tfoot>` na tabela
- Botão "🗑 Limpar dados do dia" com `confirm()` — visível só quando há dados

### Edit inline
```javascript
let editingTitulo = null; // { type, id }
// Row editada recebe classe .edit-row (fundo âmbar)
// Reseta ao trocar de data
```

---

## TIPO_COLORS (compartilhado entre CR/CP e Aging)
```javascript
NF:#1D6B3E, RA:#2d5a8e, RC:#B8860B, NCC:#dc2626,
FT:#7c3aed, PR:#0891b2, PA:#0369a1, CH:#6b7280,
BL:#374151, DP:#9333ea, LC:#15803d
```

---

## Funções JS — Referência Rápida

### Persistência
| Função | O que faz |
|--------|-----------|
| `getRecord(date)` | Retorna/cria record, inicializa campos ausentes (retrocompat) |
| `loadPortalUI()` | Carrega UI com dados do record atual |
| `collectCurrentRecord()` | Lê UI → salva no record (chama antes de saveDay) |
| `saveDay()` | collect + localStorage.setItem + renderHist |
| `exportJSON()` | Download `gestao-mana-YYYY-MM-DD.json` |
| `importJSON(event)` | Lê JSON, garante `agingAnnotations`, recarrega UI |

### CR / CP
| Função | O que faz |
|--------|-----------|
| `renderTitulos(type)` | Renderiza tabela com filtros, subtotais, edit row, limpar btn |
| `addTitulo(type)` | Adiciona título manual ao record |
| `editTitulo(type,id)` | Ativa modo edição inline (row âmbar) |
| `saveTituloEdit(type,id)` | Salva edição dos campos inline |
| `limparTitulosDodia(type)` | Limpa todos os títulos do dia com confirm() |
| `buildTituloTipoChips(type)` | Constrói chips de tipo dinamicamente |

### Caixa
| Função | O que faz |
|--------|-----------|
| `renderCaixaProjection()` | Calcula e renderiza 2 fileiras NCG (A Realizar + Realizado) |

### Adiantamentos
| Função | O que faz |
|--------|-----------|
| `addAdiant(type)` | Adiciona com status='pendente' |
| `changeAdiantStatus(type,id,val)` | Muda status → dispara renderCaixaProjection |
| `renderAdiant(type)` | Renderiza tabela com pills de resumo |

### Plano de Ação
| Função | O que faz |
|--------|-----------|
| `renderAcoes()` | Renderiza tabela de ações com campos editáveis inline |
| `addAcao()` | Adiciona nova ação (status='aberta') |
| `updateAcaoField(id,field,val)` | Atualiza campo inline |
| `deleteAcao(id)` | Remove ação |
| `renderHistConsolidado()` | Varre todos records, mostra ações abertas consolidadas |
| `updateAcaoFromConsolid(date,id,status)` | Atualiza status direto no consolidado |

### Anexos
| Função | O que faz |
|--------|-----------|
| `uploadAnexos(event)` | Lê múltiplos arquivos como base64, salva em rec.anexos |
| `previewAnexo(id)` | Abre modal com img/iframe/fallback por tipo |
| `downloadAnexo(id)` | Download via link temporário |
| `deleteAnexo(id)` | Remove do array |
| `renderAnexos()` | Renderiza lista de anexos com ações |

### Aging
| Função | O que faz |
|--------|-----------|
| `parseAgingFile(event,tipo)` | Lê xlsx, filtra saldo>0, calcula dias |
| `renderAging()` | buildTipoFilter + todos os sub-renders |
| `renderAgingFullList()` | Lista completa com filtros e 4 campos de anotação |
| `updateAgingAnn(key,field,val)` | Salva anotação no nível global + auto-localStorage |
| `getAgingAnn(key)` | Lê/inicializa anotação global |

### Checklist
| Função | O que faz |
|--------|-----------|
| `renderPortalChecklist()` | Renderiza 3 seções com progresso individual |
| `togglePChk(key)` | Toggle item por chave 'sectionId_index' |

---

## Fluxo Diário da Equipe

```
1. Abrir gestao-financeira-mana.html
2. ⬆ Carregar JSON → selecionar gestao-mana-[data].json da rede
3. 📥 Importar TOTVS (.xlsx) nas abas CR e/ou CP
4. Filtrar por Tipo/Status, editar status, marcar adiantamentos
5. Aba Caixa → digitar saldo → ver projeção NCG
6. Aging Report → carregar xlsx → anotar responsável/prazo/status por título
7. Checklist → marcar itens por seção (CR / CP / Geral)
8. Plano de Ação → adicionar/atualizar ações, anexar documentos
9. 💾 Salvar Dia
10. ⬇ Salvar JSON → gravar na pasta da rede (sobrescreve anterior)
```

---

## Checklist para Alterações no Portal

### Ao adicionar nova aba
1. Botão em `.portal-tabs`
2. Div `<div id="pp-novaaba" class="p-pane">` no `.portal-body`
3. Campo default em `getRecord()` (retrocompat)
4. Leitura em `loadPortalUI()`
5. Coleta em `collectCurrentRecord()`

### Ao adicionar campo de dados
1. Default em `getRecord()` com retrocompat guard (`if (!rec.field) rec.field = default`)
2. Leitura em `loadPortalUI()`
3. Coleta em `collectCurrentRecord()`
4. **NÃO alterar** key `mana_gestao_diaria_v1`

### Ao adicionar nova coluna TOTVS ao import
1. `const iColuna = col('Nome Exato na Planilha');`
2. Adicionar ao `.map()` em `openImportModal`
3. Adicionar ao push em `confirmImport`

### Ao adicionar novo Tipo TOTVS
Apenas adicionar em `TIPO_COLORS`:
```javascript
'XX': '#hexcolor',
```

---

## Contexto do Projeto

| Item | Valor |
|------|-------|
| Empresa | Sementes Maná (Grupo Ouro Branco), Indiara-GO |
| ERP | TOTVS Datasul (SE1/SE2/APF) |
| Usuários | Felipe Campos (Gerente), Adenilton, André, Pablo, Vinícius, Beatriz |
| Arquivo portal | `gestao-financeira-mana.html` |
| Manual equipe | `manual-cafe-mana.html` |
| Pasta rede | JSON diário salvo/carregado por todos os operadores |
