---
name: auditoria-ponto-mana
description: Use esta skill SEMPRE que trabalhar no projeto de Auditoria de Ponto da Sementes Maná (agente-auditoria-ponto). Triggers obrigatórios: "auditoria de ponto", "auditoria_ponto.html", "agente-auditoria-ponto", "espelho de ponto", "inconsistências de ponto", "gestores de ponto", "relatório de ponto Maná", "DIXI ponto", "melhorar o HTML de ponto", "validações de ponto", "banco de horas", "BH saldo", "PDF gestor", "CCT armazéns", "V06", "V07", "V13", "interjornada", "feriado dobra", "sábado compensação", "noturno adicional", "regras trabalhistas ponto", "forçar download DIXI", "embed ponto no SE", "disparo WhatsApp gestor", "DM gestor ponto". Se a conversa envolve auditoria de ponto de qualquer forma — use esta skill.
---

# Skill: Auditor de Ponto — Sementes Maná (agente-auditoria-ponto)

> **Desde 2026-06-10 este projeto é um agente Railway em produção** (sucessor do agente-ponto
> e dos scripts locais da máquina da Mariana). ADR: `ManaVault/08-Decisoes/2026-06-10-agente-auditoria-ponto-dixi-server-side.md`.
> Nota do agente: `ManaVault/06-Agentes-e-Skills/agente-auditoria-ponto.md` — **ler antes de mexer**.

## ONDE VIVE O CÓDIGO

| O quê | Onde |
|---|---|
| Repo (fonte da verdade) | `Sementesmana/agente-auditoria-ponto` (GitHub, privado) |
| Clone local | `C:\Users\Sementes Mana\Desktop\ORQUESTRADOR\agente-auditoria-ponto\` |
| HTML principal | `static/auditoria_ponto.html` (single-file ~500KB) |
| Backend | `app.py` (Flask, workers=1 — APScheduler interno, NÃO aumentar) |
| Produção | `https://agente-auditoria-ponto-production.up.railway.app` |
| Deploy | `git push origin main` → Railway auto-deploya ~2 min (Xayer roda no Git Bash) |

**Fluxo de trabalho:** `git pull` no clone → ler o arquivo atual ANTES de alterar → editar →
smoke test → Xayer commita/pusha no Git Bash → atualizar nota no ManaVault.

⚠️ **LEGADO DESCONTINUADO:** o HTML antigo em `ORQUESTRADOR\RH\Cargos e salario\auditoria_ponto.html`
e os scripts `dixi_auto_import\` (dixi_server.py porta 8765, .bats, Task Scheduler) foram substituídos
pelo agente. Não evoluir os legados. **NUNCA ler, exibir ou citar valores do `dixi_config.json`** —
credenciais DIXI agora vivem só em Railway Secrets.

## ARQUITETURA

```
Cron interno (APScheduler, seg-sex CRON_HORARIO=08:00 BRT)
  └─→ API DIXI (POST /login_ + POST /relatorio_/ponto/individual, base64)
        └─→ PDF em cache efêmero (PDF_CACHE_DIR, retenção RETENCAO_DIAS=14, sem banco)

Navegador RH (/auditoria) — TODO o processamento é client-side:
  GET  /api/dixi/status        ← lista cache
  POST /api/dixi/baixar        ← {"data":"DD-MM-YYYY"} opcional (default ontem; sem futuro; máx 90d; idempotente)
  GET  /api/dixi/pdf/<nome>    ← bytes → PDF.js processa no navegador
  GET  /health                 ← sem auth
  POST /api/whatsapp/enviar    ← {"telefone","mensagem"} → proxy pro hub agente-whatsapp (rate 30/h)
```

DIXI é a fonte da verdade (regenera qualquer data sob demanda) — por isso sem persistência em banco.

**Auth dual:** Basic Auth (`PAINEL_USUARIO`/`PAINEL_SENHA`) OU query param `?senha=` — o segundo
existe pro embed no SE; o JS propaga via helper `_api(path)` (const `_API_SENHA`).

**Env vars Railway:** `PAINEL_SENHA`, `PAINEL_USUARIO`, `DIXI_USUARIO`, `DIXI_SENHA`,
`DIXI_UNIDADE=ouro-branco`, `DIXI_ID_REGISTROS` (csv de IDs ativos — **atualizar a cada
admissão/demissão**), `CRON_HABILITADO`, `CRON_HORARIO`, `RETENCAO_DIAS`, `TZ`,
`AGENTE_WHATSAPP_URL` + `AGENTE_WHATSAPP_API_KEY` (= `WEBHOOK_SECRET` do projeto agente-whatsapp).
Sem credenciais DIXI o agente degrada: painel funciona em modo upload manual, `/api/dixi/*` → 503.

## EMBED NO SE (lições validadas 2026-06-10 — NÃO regredir)

Portal RH → aba Ponto, widget "Página WEB" (`<object>`) → `/auditoria?senha=<PAINEL_SENHA>`.

1. Basic Auth NÃO funciona em iframe cross-origin → por isso o `?senha=`.
2. `confirm()`/`alert()` nativos são bloqueados em iframe → o HTML tem `manaConfirm()` (modal
   Promise) e `window.alert` sobrescrito com toast. **Nunca reintroduzir confirm/alert nativos.**
3. PDF.js worker é carregado **via blob same-origin** (`window._workerReady`; processPDFs aguarda).
   Worker de CDN cross-origin é bloqueado → fake worker congela a UI = "todos os botões mortos".
   **Nunca voltar workerSrc direto pro CDN.**
4. Pós-deploy, instância aberta no SE pode ficar com renderer travado → F5 na página do SE.
5. `localStorage` é particionado por origem/contexto: dados dentro do SE ≠ dados fora. Migração
   manual via Exportar/Importar da sidebar (JSON de sessão).
6. `app.py` usa `Flask(static_folder=None)` — a rota default `/static` serviria o HTML sem auth.

## DISPARO WHATSAPP (desde 2026-06-11)

Botão WhatsApp do painel de gestores → `enviarWhatsAppGestor()` monta a mensagem
(ocorrências pendentes da área, máx 15), mostra preview via `manaConfirm` e POSTa em
`/api/whatsapp/enviar`. O backend valida (tel 10-13 dígitos, msg ≤4000 chars), normaliza
DDI 55 e repassa pro hub [[agente-whatsapp]] `/send-whatsapp` com `X-API-Key` — **a key
nunca vai pro HTML**. Sem env vars → 503 e o JS cai no fallback `wa.me` (WhatsApp Web).
Logs LGPD: telefone mascarado + tamanho, nunca o conteúdo. Alias `abrirWhatsappGestor`
mantido por compat. Router NÃO participa (é hub inbound) — resposta do gestor via DM
seria evolução N2/N3 futura.

## STACK (frontend)

PDF.js 3.11.174 · Chart.js 4.4.0 · SheetJS 0.18.5 · jsPDF + AutoTable · Vanilla JS ES6+ · CSS puro · localStorage

## STATE E STORAGE

```javascript
let state = {
  employees: {},          // { matricula: { nome, matricula, departamento, turno, registros:[] } }
  inconsistencies: [],    // alertas de validateEmployee()
  justifications: {},     // esclarecimentos por key
  esclarecimentos: {},    // status DP dos alertas
  gestores: [],
  holidays: [...FERIADOS_NAC],
  processedFiles: [],     // histórico de PDFs (evita reprocessar)
  inativeEmployees: new Set(),
  charts: {}, currentEmployee: null,
};
```

**localStorage keys:** `auditoria_ponto_v3` (sessão) · `mana_gestores_v1` · `mana_processed_files_v1` · `mana_inativos_v1`

## BANCO DE HORAS — SNAPSHOT

```javascript
const BH_SNAPSHOT_DT = new Date(2026, 5, 7); // 07/06/2026
```

`calcBHSaldo(emp)` parte do `BH_SALDO_INICIAL` (snapshot) e soma apenas registros **APÓS** 07/06/2026.

**Bug crítico a evitar em `parseDIXIRow`:** extrair `bhDebito/bhCredito/bhTotal` ANTES de fazer
strip das horas no texto — senão os valores de BH somem.

## FORMATOS DE PDF SUPORTADOS

- **DIXI — Relatório de Ponto Diário:** por data, todos os funcionários em tabela.
  Colunas `Funcionário | Matrícula | E1 S1 E2 S2 | Trab | CH | Ocorrências`.
- **Espelho Ponto (API `/relatorio_/ponto/individual`)** — o que o agente baixa: diário/mensal
  por funcionário com cabeçalho completo (Nome, CPF, Matrícula, Departamento...).
- **DIX — Espelho mensal legado.**

**Parser gotcha:** PDF.js retorna text runs na ordem do content stream, não visual — agrupar
por bucket de `y` (`transform[5]`) e ordenar por `x` (`groupByRow`, tolerância 12px no DIXI).

## VALIDAÇÕES (`validateEmployee`)

| Código | Descrição | Sev |
|--------|-----------|-----|
| V01 | Jornada > 10h | crítico |
| V02 | Almoço (S1→E2) < 1h | crítico |
| V03 | Interjornada < 11h | crítico |
| V04 | HE > 2h | crítico |
| V05 | Domingo trabalhado | crítico |
| V05B | Domingo sem HE/DSR em dobro no DIXI | crítico |
| V05C | Sábado sem HE ou compensação | atenção |
| V06 | Feriado trabalhado | atenção |
| V06B | Feriado sem HE/dobra no DIXI | crítico |
| V07 | Noturno (22h-05h) sem "HE Noturno"/"Extra Noturno" | crítico |
| V08 | Dia sem marcações | atenção |
| V09 | Ponto britânico (5+ dias mesma entrada) | crítico |
| V10 | BH negativo > 30 dias | atenção |
| V11 | Marcações atípicas (≠ 4 batidas) | info |
| V12 | Desvio de turno | atenção |
| V13 | Saída não registrada (batidas ímpares) | crítico |
| CCT01 | BH crédito diário > 2h | crítico |
| CCT05 | Vigia 12×36 | atenção |
| CCT06 | HE fora da safra | atenção |
| CCT08 | HE > 2h sem pausa lanche | atenção |
| CCT09 | Dia do Armazenista trabalhado | atenção |

### Lógica de dobra (V05B, V06B, V05C)
```javascript
const hasHE = /\b(HE\s*(Diu?rno?|Noturno|Normal|Feriado)|Extra\s*(Normal|Noturno)|Extras|DSR\s*pago|folga\s*compensat)\b/i.test(r.ocorrencias);
const bhCred = timeToMin(r.bhCredito || '00:00');
if (trabMin > 0 && !hasHE && bhCred <= 0) { /* alerta */ }
```

### V07 — Noturno
```javascript
const hasNoturno = /adicional noturno|adic.*noturno|\bHE\s*Noturno\b|Extra\s*Noturno/i.test(r.ocorrencias);
```

## MÓDULO DE GESTORES

Cadastro: Nome, E-mail, Telefone, Departamento(s). Painel por área com inconsistências + status
de esclarecimento (Pendente → Em análise → Esclarecido → Ajuste solicitado).
Botões: PDF área (`gerarPDFGestor`), Excel, E-mail (mailto), WhatsApp.

### PDF do Gestor
3 colunas `Data | Funcionário/Matrícula | Marcações / Obs`, agrupado por tipo de alerta,
pills E1/S1/E2/S2 + descrição em itálico. **Sanitização obrigatória** (em-dash quebra jsPDF):
```javascript
const _sp = s => (s||'').replace(/—|―/g,' - ').replace(/–/g,'-').replace(/[^\x00-\xFF]/g,'?');
```

## CCT APLICÁVEL

**CCT Armazéns Gerais GO 2025/2026** — MR071570/2025 — vigência 01/11/2025–31/10/2026.
Cláusulas: 9ª (pausa lanche), 13ª (feriado dobro), 14ª (sábado), 17ª §4º (BH máx 2h/dia),
18ª/19ª (vigia 12×36), 20ª (HE safra), 37ª (Dia do Armazenista). Aba CCT (p-legislacao) tem os cards.

## INSTRUÇÃO DE ENTREGA

1. `git pull` no clone + ler nota do agente no ManaVault ANTES de qualquer alteração
2. Editar `static/auditoria_ponto.html` e/ou `app.py` no clone local
3. Smoke test (py_compile + flask test client; pro HTML, conferir que não voltou confirm/alert/workerSrc CDN/fetch sem `_api()`)
4. Xayer commita e pusha no Git Bash → Railway deploya → **F5 na página do SE**
5. Atualizar `ManaVault/06-Agentes-e-Skills/agente-auditoria-ponto.md` (`ultima-revisao` + seções) e apresentar com `mcp__cowork__present_files`
6. **NUNCA** ler/citar `dixi_config.json` legado; credenciais só em Railway Secrets
