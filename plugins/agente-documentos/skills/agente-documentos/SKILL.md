---
name: agente-documentos
description: App de documentos do processo Solicitação de Crédito (SM.CV.PR.NE.CRE-001) do SoftExpert — Sementes Maná LTDA. Flask + Alpine.js no Railway com 2 abas: (1) Triagem — drag-and-drop de até 50 docs, Claude classifica por filename pseudonimizado (TIPODOC/DOCUMENTO/TITULAR/SAFRA), cria docs em CRE via newDocument com urn:attributes e associa à ATV-03 com anti-duplicação. (2) Análise Documental v2 (2026-07-05) — relatório de COBRANÇA de documentos: núcleo determinístico (checklist fixa PF/PJ, grupo econômico, fazendas via gridcapacipro, anuência valiassinatura, DV CPF/CNPJ), ingestão estruturada no data lake banco-mana (data-lake-pg), Claude só como estruturador cirúrgico + check de divergências via mana-llm-gateway sobre JSON pseudonimizado. Use SEMPRE em tarefas do agente-documentos: triagem, análise documental, ATV-03, scred, gridcapacipro, tipodecliente, usodasemente, valiassinatura, analiseclaude, relatório de cobrança, CRE-001.
---

# Agente Documentos — Triagem + Análise Documental (v2) do CRE-001

Serviço Flask no Railway, 2 abas no mesmo painel (`/triagem-docs?idprocess=XXX`):

- **Aba 1 — Triagem** (produção desde 2026-04-30): drag-and-drop → Claude classifica por filename **pseudonimizado** → cria docs no SE (categoria CRE, 6 atributos) → associa à ATV-03.
- **Aba 2 — Análise Documental v2** (produção desde 2026-07-05, ADR `2026-07-04-aba2-v2-deterministica-lake-sem-check-cpr`): **relatório de cobrança de documentos** pra analista de crédito. Check 3 (suficiência CPR) foi REMOVIDO — regras de CPR vivem só no agente-cpr.

## URLs e Identificadores

| Item | Valor |
|---|---|
| URL produção | `https://agente-documentos-production.up.railway.app` |
| Repo | `Sementesmana/agente-documentos` |
| Processo / Atividade SE | `SM.CV.PR.NE.CRE-001` / `ATV-03` |
| Categoria doc | `CRE` |
| Form | `scred` |
| Grid fazendas/capacidade | `gridcapacipro` (rel. `capaproxsolicre`) — **é a fonte das fazendas do CRE-001** |
| Data lake | banco-mana schema `analise_documental` (habilidade `data-lake-pg`, lock 778912) |

## ⚠️ Nomenclatura canônica (Xayer 2026-07-04)

- **`tipodecliente`** = PF | PJ → decidido pelos **dígitos do `scred.cpfcnpj`** (11=PF, 14=PJ); fallback texto `scred.tipocliente` ("Pessoa Física/Jurídica"); divergência entre os dois vira alerta
- **`usodasemente`** = Agricultor | Multiplicador | Distribuidor → campo `scred.usodasemente`
- **`scred.tipoclient` NÃO EXISTE** (drift corrigido na v2)
- Distribuidor: sem gridcapacipro, sem CPR. PJ: sem gridcapacipro.
- `gridfazendas`/`cprxfazendas` é do **formscpr (CRE-002)** — no scred não existe; leitor implementado fica dormindo (env `SE_GRID_FAZENDAS_ID`)

## Aba 2 v2 — Pipeline

1. **SOAP:** scred completo + gridcapacipro (+`gridgrupoecon` se `scred.grupeconom == "Sim"` — VALIDADA em prod 2026-07-05, WF 000001 GARCIA; campos: nome, cpfcnpj, grau, matricula)
2. **Ingestão por doc (lake-first):** MD5 dos bytes → `doc:<md5>` no lake → HIT pula tudo. MISS: OCR (pdfplumber→Tesseract DPI200+autocontrast) → `estruturar_por_regex` com **validação DV** (CPF/CNPJ errados de OCR são descartados → `cpfs_suspeitos`) → **Claude estruturador** (`mana-rapido`) SÓ se origem=tesseract ou campo crítico vazio; texto vai pseudonimizado; resposta re-validada por DV → merge (regex prevalece) → upsert no lake (sem texto cru)
3. **Checks determinísticos (zero LLM,** `analise_deterministica.py`**):**
   - Checklist FIXA PF (RG+CPF produtor/cônjuge-se-casado, certidão casamento/divórcio, comprovante endereço ≤90d, IR vigente+anterior, contratos se areaarrendada>0, matrícula se areapropria>0, croqui, CAR) e PJ (contrato social*, RG+CPF sócios, certidão casamento, balanço 3 exercícios, DRE, faturamento 12m*) + itens extras de `docpessofisica`/`docpessojuridica`
   - *itens sem valor DOCUMENTO na taxonomia → fallback por filename (pendência: criar "Contrato social" e "Relação de faturamento" no SE)
   - Estado civil AMARRADO À PESSOA (regra Xayer): só doc PESSOAL (IRPF/CNH/RG/certidões) com titular=Cliente E CPF do cliente no conteúdo decide; cônjuge declarado no IRPF (campo CPF do cônjuge, DV validado) = casado; contrato NUNCA decide ("casada" solto é de terceiro). Desconhecido → cônjuge e certidão viram "verificar"; solteiro comprovado → não aplicável; divorciado → cobra certidão de divórcio
   - Grupo econômico (v3, validado 2026-07-05): vínculo doc↔pessoa por **CPF/CNPJ no conteúdo extraído** (primário) + token distintivo do nome no filename (secundário; sobrenomes compartilhados com cliente/membros são ignorados). Checklist do membro pelo **tipo DELE**: PF = itens pessoais (RG/CPF, cônjuge, certidão, endereço, IR), PJ = societários (contrato social, balanço, DRE, faturamento). No PJ principal, doc de identidade vinculado por CPF a membro do grupo conta como doc de Sócio (re-tag), mesmo classificado como Filho(a)
   - Fazendas: **gridcapacipro** × união dos estruturados (matrícula normalizada, CAR, IE, área ±5%)
   - Anuência: `scred.valiassinatura == "Sim"` (termo de anuência do vendedor)
4. **Check divergências (LLM,** `mana-equilibrio` **via gateway):** output com `titulo` humano + `acao` no imperativo (destacada em verde na UI), ordenado por gravidade com placar 🔴🟡⚪, números pt-BR. recebe SÓ JSONs estruturados pseudonimizados + subconjunto cadastral do scred (`_SCRED_CAMPOS_LLM`) — **NUNCA scred completo (parecer/decisões/Tarken) nem texto cru**. Falha → `llm_indisponivel: true`, análise segue determinística
5. Resultado cacheado (in-memory 5min) + histórico `analise:<idprocess>` no lake. UI gera markdown localmente → `POST /api/salvar-analise` → `scred.analiseclaude` (30k chars)

## Performance validada (smoke WF 000002, 9 docs reais)

| Cenário | Tempo | Reqs gateway |
|---|---|---|
| 1ª análise (lake frio) | ~109s | 3 estruturador + 1 divergências |
| Re-análise (lake quente, mesmo pós-deploy) | **~58s** (9× LAKE HIT; ~54s é só o mana-equilibrio) | **+1** |
| Triagem (qualquer lote) | ~3s | +1 |

Follow-up candidato: divergências em background job (analista vê o determinístico na hora).

## Env vars (além de SE_URL/SE_API_KEY/ANTHROPIC_API_KEY)

- `LLM_GATEWAY_URL` / `LLM_GATEWAY_KEY` — gateway SEMPRE que presentes (fallback Anthropic direto)
- `LLM_MODEL_TRIAGEM=mana-rapido` · `LLM_MODEL_ANALISE=mana-equilibrio` · `LLM_MODEL_ESTRUTURADOR=mana-rapido` (default)
- `DATABASE_URL` — banco-mana; sem ela lake desliga (cache /tmp legado, morre no deploy)
- `SE_GRID_CAPACIDADE_ID=gridcapacipro` / `SE_GRID_CAPACIDADE_RELATIONSHIP_ID=capaproxsolicre`
- `SE_GRID_GRUPOECON_ID=gridgrupoecon` (validada) / `SE_GRID_FAZENDAS_ID=gridfazendas` (dormindo — não existe no scred)
- `ANALISE_MAX_DOC_BYTES=26214400` / `ANALISE_MAX_TEXT_CHARS=15000`

## Endpoints

`GET /health` · `GET /triagem-docs?idprocess=X` · `POST /api/classificar` · `POST /api/enviar?idprocess=X` · `GET /api/scred?idprocess=X` (retorna scred + tipodecliente + usodasemente + 3 grids) · `POST /api/analisar?idprocess=X` (multipart files+meta da Aba 1; fallback getAssocDocuments) · `POST /api/salvar-analise` · `GET /imputar` · `GET /api/validar-wf`

## Estrutura

```
app.py                       # Flask, 11 endpoints, segurança (rate limit, whitelist idprocess)
agente_documentos.py         # Aba 1: SOAP, classificação, domínio CRE, pseudonimização filename
agente_analise_documental.py # Aba 2 v2: SOAP, OCR, lake, estruturador, divergências
analise_deterministica.py    # núcleo zero-LLM: DV, regex, checklists, fazendas, anuência
templates/triagem.html       # UI 2 abas (Alpine.js)
```

## Aba 1 — domínio CRE (inalterado na v2)

6 atributos (`SAFRA`, `TIPOCLIENT`, `CLIENTE`, `TITULAR`, `TIPODOC`, `DOCUMENTO`); `<urn:attributes>` é STRING ÚNICA `IDENT=VALOR;...`; mapa TIPODOC→DOCUMENTO com 38 valores; anti-dup por título via getAssocDocuments; regras prioritárias de filename (faturas de utilities → Comprovante de endereço; IE/SEFAZ → Inscrição Estadual). LGPD: Claude recebe APENAS filename pseudonimizado.

## Bugs/gotchas (acumulado)

1. Mount Cowork trunca arquivos ~22-24KB — validar em /tmp com ast.parse
2. Mount Windows trava `.git/*.lock` — git ops em /tmp ou Git Bash do Xayer
3. `railway.toml` tem precedência sobre Procfile (timeout 600s nos DOIS)
4. Cache in-memory não compartilha entre workers → `--workers 1`
5. DPI 200 + autocontrast > DPI 150 sem autocontrast (Tesseract)
6. **data-lake-pg `read()` retorna TUPLA `(dados, atualizado_em)`** — tratar como dict = miss eterno silencioso
7. **pseudonimizar-pii v0.1.0 não tem `registrar_nomes`** — v2 usa fallback local `_PseudoLocal` (placeholders [CLIENTE-1]/[CPF-1], mapa só em memória)
8. **Wait for CI no Railway trava deploy** (herança da migração pra Org) — desabilitado em Settings→Source
9. Chaves de `_CAMPOS_CRITICOS_POR_DOC` em forma norm() SEM acentos
10. **parse_num_br aceita 2 formatos**: BR ('1.664,50') E decimal do SE ('462.000000000000') — tratar só como BR gera "462 trilhões de ha"
11. **Chave do lake é versionada** (`doc:v3:<md5>`) — bumpar `_ESQUEMA_DOC` quando a extração ganhar campos novos, senão snapshots antigos servem schema velho pra sempre
12. Embed no SE: **Ctrl+F5 pós-deploy** (cache do iframe)

## LGPD (v2)

Aba 1: só filename pseudonimizado. Aba 2: lake guarda estruturado SEM pseudonimização (uso interno, execução de contrato art. 7º V); pseudonimização acontece NA SAÍDA pro LLM (cliente/cônjuge/sócios/grupo econ + CPF/CNPJ → placeholders; mapa em memória, nunca persiste). Parecer, decisões de comitê e rating Tarken NUNCA vão pro LLM.

## ADRs

- `2026-07-04-aba2-v2-deterministica-lake-sem-check-cpr` — vigente (supersede o Check 3 inline de 2026-05-07)
- `2026-06-19-pseudonimizacao-padrao-llm-e-terceiros`
- Pendências: bridge CRE-001→CRE-002; taxonomia Contrato social/Faturamento no SE; `registrar_nomes` na habilidade pseudonimizar-pii; normalizar números do payload pro LLM; divergências em background job; usar campo `grau` da gridgrupoecon pra vincular cônjuges entre membros
