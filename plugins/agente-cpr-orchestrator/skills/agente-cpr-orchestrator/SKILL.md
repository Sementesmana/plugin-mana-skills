---
name: agente-cpr-orchestrator
description: Gerador automatizado de CPR (Cédula de Produto Rural) com Orquestração SoftExpert. Transforma dados estruturados em documentos Word preenchidos usando Claude para formatação inteligente. Suporta múltiplos tipos de garantia (CPR Penhora AF, Fiança, Confissão de Dívida, Nota Promissória) com integração ao SoftExpert para instanciar workflows, criar documentos, associar PDFs e avançar atividades. Disponível também como micro-serviço Flask REST para integração automática com SoftExpert. Use este skill sempre que precisar gerar, preencher ou processar CPRs, garantias agrícolas, ou qualquer documento jurídico estruturado com dados variáveis do agronegócio.
---

# Agente CPR — Confecção de Garantia (SEMENTES MANÃ LTDA)

Automatiza o processamento completo de **Cédulas de Produto Rural (CPR)** com integração segura ao SoftExpert Workflow.

## Modos de Uso

### 1. CLI (linha de comando)
```bash
# Apenas gerar documento Word local (sem SoftExpert)
python scripts/agente_cpr.py --workflow 000139 --apenas-gerar

# Processamento completo: gerar + criar no SE + associar ao workflow
python scripts/agente_cpr.py --workflow 000139
```

### 2. Micro-serviço Flask REST (para integração automática com SoftExpert)
```bash
# Iniciar o serviço na porta 5000
python scripts/flask_agente_cpr_api.py

# SoftExpert chama automaticamente:
POST http://localhost:5000/gerar-cpr
Body: {"idprocess": "000142"}

# Verificar se serviço está online:
GET http://localhost:5000/health
```

## Recursos

- ✅ Lê dados do formulário CPR no SoftExpert (getTableRecord via SOAP)
- ✅ Claude formata dados com inteligência (datas por extenso, negrito, valores)
- ✅ Preenche template Word original com logo e formatação preservados (docxtpl)
- ✅ Suporta múltiplos emitentes, cônjuges anuentes e múltiplas fazendas
- ✅ Cria documento no SoftExpert (newDocument via SOAP)
- ✅ Associa documento ao workflow na ATV-02 (newAssocDocument)
- ✅ SoftExpert avança atividade automaticamente via regra de workflow
- ✅ Retry automático com backoff exponencial (2s, 4s, 8s)
- ✅ Modo `--apenas-gerar` para testes sem SoftExpert
- ✅ Micro-serviço Flask REST para chamada automática pelo SoftExpert
- ✅ Logging completo em stdout e arquivo de log

## Variáveis de Ambiente / Configuração

As credenciais ficam no bloco `CONFIG` dentro do script `agente_cpr.py`:

```python
CONFIG = {
    "SE_URL":            "https://sementesmana-test.softexpert.app",
    "SE_API_KEY":        "eyJ...",          # Bearer token SoftExpert
    "ANTHROPIC_API_KEY": "sk-ant-api03-...", # Chave Anthropic
    "ENTITY_ID":         "formscpr",         # ID do formulário no SE
    "DOC_CATEGORY_ID":   "GARANTIAS",        # Categoria de doc no SE
    "ACTIVITY_ID":       "ATV-02",           # Atividade do workflow
    "ACTION_SEQUENCE":   "1",
    "TEMPLATE":          ".../templates/template_cpr_preenchivel.docx",
    "PASTA_SAIDA":       ".../output/garantias",
}
```

## Fluxo de Processamento

```
1. LER dados do SoftExpert (getTableRecord — campo jsonclaude)
   ↓
2. FORMATAR com Claude claude-opus-4-6 (inteligência jurídica)
   ↓
3. PREENCHER template Word (docxtpl — logo + formatação preservados)
   ↓
4. CRIAR documento no SoftExpert (newDocument — categoria GARANTIAS)
   ↓
5. ASSOCIAR documento ao workflow na ATV-02 (newAssocDocument)
   ↓
6. SoftExpert avança atividade automaticamente (regra de workflow)
   ↓
7. LOG de auditoria (sucesso/erro com detalhes)
```

## Micro-serviço Flask — Endpoints

| Método | Endpoint      | Descrição                                          |
|--------|---------------|----------------------------------------------------|
| POST   | `/gerar-cpr`  | Gera e associa CPR a partir do `idprocess`         |
| GET    | `/health`     | Verifica se o serviço está online                  |
| GET    | `/`           | Documentação dos endpoints                         |

**Request `/gerar-cpr`:**
```json
{"idprocess": "000142"}
```

**Response sucesso:**
```json
{
  "status": "sucesso",
  "workflow_id": "000142",
  "arquivo": "C:\\...\\CPR_04-2026_000142_20260315.docx",
  "tamanho_bytes": 45123,
  "timestamp": "2026-03-15T22:26:00",
  "mensagem": "Documento CPR gerado com sucesso: CPR_04-2026_000142_20260315.docx"
}
```

## Tratamento de Erros

| Tipo | Comportamento |
|------|---------------|
| Timeout / erro de rede | Retry automático: 3 tentativas (2s → 4s → 8s) |
| Campo `jsonclaude` vazio | Erro claro: "Avance o workflow no SE (botão Validar)" |
| Template Word não encontrado | Erro claro com caminho esperado |
| Falha ao criar doc no SE | Aborta com log detalhado |
| Falha ao associar doc | Aborta com diagnóstico (workflow existe? ATV-02 existe?) |
| Flask timeout (>120s) | Retorna HTTP 504 com mensagem de timeout |

## Arquivos de Saída

```
output/garantias/CPR_04-2026_000139_20260315_103045.docx   ← documento gerado
dados_cpr_000139.json                                        ← dados formatados pelo Claude
api/flask_agente_cpr.log                                     ← log do micro-serviço Flask
```

## Dados Fixos da Credora (nunca alterar)

| Campo | Valor |
|-------|-------|
| Razão Social | SEMENTES MANÃ LTDA |
| CNPJ | 37.635.276/0001-56 |
| RENASEM | GO-02876/2021 |
| Inscrição Estadual | 10.810.154-1 |
| Sede | Rodovia BR 060, Km 245,8, Indiara/GO |

## FAQ

**P: Preciso ter o SoftExpert configurado?**
R: Não para testes. Use `--apenas-gerar` para gerar o DOCX localmente sem conexão com SE.

**P: O script avança a atividade automaticamente?**
R: Não. O script apenas **associa** o documento à ATV-02. O SoftExpert avança automaticamente via regra de workflow configurada no SE.

**P: Como integrar com SoftExpert sem rodar o CLI manualmente?**
R: Use o micro-serviço Flask (`flask_agente_cpr_api.py`). Configure o SoftExpert para fazer POST em `http://localhost:5000/gerar-cpr` com o `idprocess`.

**P: Posso customizar o template?**
R: Sim. Atualize `TEMPLATE` no CONFIG e regenere com `criar_template_cpr.py`.

**P: Quanto tempo economizo?**
R: ~80% de redução de trabalho manual. Documento gerado em ~5s vs 15min manual.

---

**Versão:** 2.0
**Atualizado:** 2026-03-18
**Status:** ✅ Pronto para Produção
**Novidades v2.0:** Script simplificado (sem avanço manual de atividade) + Micro-serviço Flask REST para integração automática com SoftExpert
