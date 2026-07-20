---
name: agente-nf
description: "Agente inteligente para processamento automatizado de Notas Fiscais com 3 camadas de proteção contra reprocessamento. Captura NFs de pasta local ou email (IMAP), extrai dados via OCR+Claude AI, classifica fornecedor/centro-de-custo, instancia workflows no SoftExpert com formulário preenchido e itens detalhados. Gerencia automaticamente pasta de email (move para NF-Processadas), rastreia hashes MD5 com nomes de arquivo para reprocessamento seletivo, e avança atividades. Ideal para automação de despesas em ERP, integração email corporativo e classificação em lote."
---

# Agente NF — Automação Inteligente de Notas Fiscais

## Visão Geral

O **Agente NF** é um automatizador end-to-end para processamento de Notas Fiscais que:

1. **Captura NFs** de pasta local ou caixa de email corporativo (IMAP/Localweb)
2. **Extrai dados** via OCR (pdfplumber) + análise inteligente (Claude API)
3. **Classifica automaticamente** fornecedor, descrição, valor, centro de custo
4. **Instancia workflows** no SoftExpert com formulário preenchido + itens detalhados
5. **Gerencia email inteligentemente** — move para pasta `INBOX.NF-Processadas` após processamento
6. **Protege contra reprocessamento** — 3 camadas: filtro INBOX, hash MD5, rastreamento de nomes
7. **Permite reprocessamento seletivo** — delete linha de `pdfs_processados.txt` pra reprocessar 1 NF
8. **Integra com SE Documentos** — cria documento, grava ID no workflow
9. **Avança atividades** — executa transições automáticas (ATV-01, ATV-02)

## Configuração

### 1. Requisitos

- Python 3.8+ com bibliotecas: `requests`, `anthropic`, `pytesseract`, `pdf2image`
- Tesseract OCR (https://github.com/UB-Mannheim/tesseract/wiki)
- Poppler (https://github.com/oschwartz10612/poppler-windows/releases/)

### 2. Credenciais

Preencha no script `agente_nf.py`:

```python
CONFIG = {
    "SE_URL": "https://sementesmana-test.softexpert.app",
    "SE_API_KEY": "seu_jwt_token_aqui",
    "ANTHROPIC_API_KEY": "sk-ant-api03-...",
    "EMAIL_USER": "financeiro@sementesmana.com.br",
    "EMAIL_PASSWORD": "sua_senha_aqui",
    # ... resto da config
}
```

### 3. Customizar Prompt (Opcional)

Edite `prompt_classificacao.json` para ajustar a classificação:

```json
{
  "prompt_template": "Você é um agente especialista em classificação de notas fiscais...\n\n{lista_ccs}\n\nTexto da Nota Fiscal:\n{texto_nf}"
}
```

## Execução

```bash
# Processa pasta local + email
python agente_nf.py

# Modo teste — só extrai, sem enviar ao SE
python agente_nf.py --teste arquivo.pdf
```

## 🛡️ Proteção Contra Reprocessamento (3 Camadas)

1. **Camada 1 — Filtro INBOX**: Processa apenas emails não lidos do dia em INBOX. Emails em `NF-Processadas` nunca são tocados.
2. **Camada 2 — Movimento seguro**: Email é movido para `INBOX.NF-Processadas` ANTES de processar PDFs. Se move falhar, PDF não é processado.
3. **Camada 3 — Hash MD5**: Arquivo `pdfs_processados.txt` rastreia `hash | nome_arquivo`. Mesmo PDF com nomes diferentes não é reprocessado.

**Reprocessar seletivamente:**
```
1. Abra pdfs_processados.txt
2. Delete a linha da NF desejada (ex: a do NF-37720.pdf)
3. Move email de volta ao INBOX e marque como NÃO LIDO
4. Próxima execução reprocessa apenas essa NF
```

## Fluxo do Workflow no SoftExpert

```
ATV-01 (Registrar NF)
  ├─ OCR + Claude classifica
  ├─ Cria documento em SE Documentos
  ├─ Instancia workflow (preenche formulário)
  ├─ Anexa PDF
  ├─ Grava iddocumento no formulário
  └─ Avança → Complexo

Complexo (Gateway Paralelo)
├─ ATV-02 (Revisar Classificação)
│  └─ Agente avança automaticamente
└─ Atividade Sistêmica
   └─ Lê iddocumento e associa documento automaticamente
```

## Campos do Formulário (SE)

Criar no SoftExpert:
- `iddocumento` (Texto) — armazena ID do documento criado
- `idprocess` (Texto) — armazena ID da instância do workflow

## Treinar o Claude

Adicione exemplos no `prompt_classificacao.json`:

```json
{
  "prompt_template": "...Centros de custo:\n{lista_ccs}\n\nExemplos:\n- 'Microsoft' → CC-4020 (TI)\n- 'Agência' → CC-5010 (Marketing)\n\nTexto:\n{texto_nf}"
}
```

## ✅ Melhorias Recentes (Março 2026)

- ✅ **Email inteligente**: Cria automaticamente pasta `INBOX.NF-Processadas` no Localweb
- ✅ **Rastreamento com nomes**: `pdfs_processados.txt` agora salva `hash | nome_arquivo` para fácil identificação
- ✅ **Movimento seguro**: Verifica sucesso do move antes de processar PDFs
- ✅ **Normalização corrigida**: Valores numéricos com 4 casas decimais (quantidade, unitário)
- ✅ **Extração de itens**: Suporta múltiplos itens por NF com NCMSH, CST, CFOP, descontos, impostos
- ✅ **Logging detalhado**: Rastreia valores em cada etapa do pipeline

## ⚠️ Conhecidos

- **Precisão decimal (SoftExpert)**: Campo `quant` via SOAP arredonda para 2 casas (aguardando correção no SE)
  - Workaround: valores são enviados corretamente (329.7350), mas SE armazena como 329.74
  - Chamado aberto com SoftExpert para investigar `newChildEntityRecordList` API

## 🚀 Futuro

- Agendamento automático
- Pasta compartilhada do servidor
- Agente de confecção de garantias (Word)
- Dashboard de monitoramento
- Integração com Protheus (após resolução precisão decimal)
