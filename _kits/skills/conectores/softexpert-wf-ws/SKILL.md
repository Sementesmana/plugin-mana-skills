---
name: softexpert-wf-ws
description: Referência canônica dos 23 métodos SOAP do SoftExpert Workflow (wf_ws.php) — Maná. Use SEMPRE que precisar instanciar workflow no SE, preencher formulário, avançar atividade, popular grid, anexar arquivo, ou explicar método do wf_ws. Cobre newWorkflow, newWorkflowEditData, executeActivity, executeSystemActivity (SIS-XX), editAttributeValue, editEntityRecord, editChildEntityRecord, newChildEntityRecord, newChildEntityRecordList (bulk), newAttachment, newAssocDocument, newComment, cancelWorkflow, reactivateWorkflow, getWorkflow. Inclui endpoint, Bearer JWT, encoding ISO-8859-1, identificadores (ProcessID, WorkflowID, ActivityID, EntityID, MainEntityID, ChildRelationshipID, EntityAttributeID), códigos de erro, exemplos Python e cookbook Maná. Triggers wf_ws, wf_ws.php, SOAP SoftExpert, atividade sistêmica, SIS-02, ATV-02, scred, formscpr, contapagar, contxiten, scredito, dyngridfazendas, agente-cpr/nf/pedidos/documentos/km. Substitui softexpert-orchestrator (em drift).
---

# SoftExpert Workflow Web Service (`wf_ws.php`) — Base de Conhecimento

> Referência canônica dos **23 métodos SOAP** do módulo Workflow do SoftExpert.
> Fonte: `https://developer.softexpert.com` (capturas oficiais em `pdfs-originais/`).
> Versão coberta: **SoftExpert Suite 3.0.0** (última atualização da fonte: 23/abr/2026).

## Quando usar esta skill

Sempre que precisar montar uma chamada SOAP para o módulo **Workflow** do SE:

- Instanciar um processo (`newWorkflow`, `newWorkflowEditData`, `newWorkflowTypeEditData`)
- Avançar atividade (`executeActivity`, `executeSystemActivity`)
- Editar dados do formulário principal (`editEntityRecord`, `editAttributeValue`, `editWorkflowData`)
- Popular ou alterar grids (`newChildEntityRecord`, `newChildEntityRecordList`, `editChildEntityRecord`, `clearChildEntityRecord`, `deleteChildEntityRecord`)
- Anexar arquivo ou associar documento (`newAttachment`, `newAssocDocument`)
- Comentar ou comunicar no workflow (`newComment`)
- Controlar acesso (`newAccessException`, `deleteAccessException`)
- Associar workflows (`newAssocWorkflow`)
- Operações de ciclo de vida (`cancelWorkflow`, `reactivateWorkflow`, `unlinkActivityFromUser`, `getWorkflow`)

## Endpoint base

```
POST https://sementesmana.softexpert.app/apigateway/se/ws/wf_ws.php
Authorization: Bearer {SE_API_KEY}
Content-Type: text/xml; charset=ISO-8859-1
SOAPAction: ""
```

⚠️ **Encoding ISO-8859-1 é crítico** — UTF-8 quebra acentuação de campos como `WorkflowTitle`, `Explanation`, `Text` (newComment).

## Os 23 métodos do `wf_ws.php`

| # | Método | O que faz | Arquivo |
|---|---|---|---|
| 1 | `cancelWorkflow` | Cancela um workflow | [`references/cancelWorkflow.md`](references/cancelWorkflow.md) |
| 2 | `clearChildEntityRecord` | Exclui todos registros relacionados de uma grid | [`references/clearChildEntityRecord.md`](references/clearChildEntityRecord.md) |
| 3 | `deleteAccessException` | Remove uma exceção de acesso | [`references/deleteAccessException.md`](references/deleteAccessException.md) |
| 4 | `deleteChildEntityRecord` | Exclui um registro específico de grid | [`references/deleteChildEntityRecord.md`](references/deleteChildEntityRecord.md) |
| 5 | `editAttributeValue` | Altera o valor de um atributo do workflow | [`references/editAttributeValue.md`](references/editAttributeValue.md) |
| 6 | `editChildEntityRecord` | Altera registro de grid | [`references/editChildEntityRecord.md`](references/editChildEntityRecord.md) |
| 7 | `editEntityRecord` | Altera registro do formulário principal | [`references/editEntityRecord.md`](references/editEntityRecord.md) |
| 8 | `editWorkflowData` | Edita metadados da instância (UserID, Customer, Contact) | [`references/editWorkflowData.md`](references/editWorkflowData.md) |
| 9 | `executeActivity` | Avança atividade de usuário/decisão | [`references/executeActivity.md`](references/executeActivity.md) |
| 10 | `executeSystemActivity` | Avança atividade sistêmica assíncrona (SIS-XX) | [`references/executeSystemActivity.md`](references/executeSystemActivity.md) |
| 11 | `getWorkflow` | Retorna informações de uma instância | [`references/getWorkflow.md`](references/getWorkflow.md) |
| 12 | `newAccessException` | Inclui exceção de acesso | [`references/newAccessException.md`](references/newAccessException.md) |
| 13 | `newAssocDocument` | Associa documento do SE Documento à atividade | [`references/newAssocDocument.md`](references/newAssocDocument.md) |
| 14 | `newAssocWorkflow` | Associa workflow a outro (bloqueante ou não) | [`references/newAssocWorkflow.md`](references/newAssocWorkflow.md) |
| 15 | `newAttachment` | Anexa arquivo binário a uma atividade | [`references/newAttachment.md`](references/newAttachment.md) |
| 16 | `newChildEntityRecord` | Insere 1 registro em grid | [`references/newChildEntityRecord.md`](references/newChildEntityRecord.md) |
| 17 | `newChildEntityRecordList` | Insere múltiplos registros em grid (bulk, ~100/req) | [`references/newChildEntityRecordList.md`](references/newChildEntityRecordList.md) |
| 18 | `newComment` | Adiciona comentário a uma atividade | [`references/newComment.md`](references/newComment.md) |
| 19 | `newWorkflow` | Instancia workflow (sem dados) | [`references/newWorkflow.md`](references/newWorkflow.md) |
| 20 | `newWorkflowEditData` | Instancia workflow já preenchendo formulário | [`references/newWorkflowEditData.md`](references/newWorkflowEditData.md) |
| 21 | `newWorkflowTypeEditData` | Instancia por tipo (WorkflowTypeID) com dados | [`references/newWorkflowTypeEditData.md`](references/newWorkflowTypeEditData.md) |
| 22 | `reactivateWorkflow` | Reativa instâncias suspensas (lote) | [`references/reactivateWorkflow.md`](references/reactivateWorkflow.md) |
| 23 | `unlinkActivityFromUser` | Devolve atividade ao grupo (desassocia executor) | [`references/unlinkActivityFromUser.md`](references/unlinkActivityFromUser.md) |

Para o overview de autenticação, padrões de envelope SOAP, retorno comum e gotchas: [`references/00-overview.md`](references/00-overview.md).

## Padrão de retorno comum

Todos os métodos retornam:

| Campo | Descrição |
|---|---|
| `Status` | `SUCCESS` ou `FAILURE` |
| `Code` | Código do retorno (ex: `1` = sucesso; `-9`, `-16`, `-93`, `-94` = falhas conhecidas) |
| `Detail` | Mensagem em texto |
| `RecordKey` | (quando aplicável) Código do registro criado |
| `RecordID` | (quando aplicável) Identificador do registro criado |

## Cookbook — combinações típicas no ecossistema Maná

**Instanciar processo + popular grid + anexar PDF + avançar:**

```
newWorkflowEditData(ProcessID, WorkflowTitle, dados_form)
   ↓ retorna RecordID = WorkflowID
newChildEntityRecordList(WorkflowID, MainEntityID, ChildRelationshipID, lista_itens)
   ↓ insere N itens da grid em 1 chamada
newAttachment(WorkflowID, ActivityID, FileName, FileContent_b64)
   ↓ anexa PDF
executeActivity(WorkflowID, ActivityID, ActionSequence)
   ↓ avança pra próxima atividade
```

**Atividade sistêmica chamando agente Railway:**

```
SE → SIS-02 (Atividade Sistêmica) → POST agente-XXX/endpoint
   ↓ agente processa
agente → editEntityRecord(WorkflowID, EntityID, dados)   # popula form
       → newChildEntityRecordList(...)                    # popula grid
       → executeSystemActivity(WorkflowID, ActivityID)   # avança SIS
```

**Triagem documental (CRE-001 ATV-03):**

```
newDocument(...)              # dc_ws.php — não está nesta skill
   ↓ retorna DocumentID
newAssocDocument(WorkflowID, ActivityID, DocumentID)   # wf_ws.php
   ↓ associa doc à atividade
```

## Tipos de dados — observações sobre `AttributeValue`

Para `editAttributeValue`, `editEntityRecord`, `newChildEntityRecord`, `newWorkflowEditData`:

| Tipo do atributo | Formato esperado |
|---|---|
| Numérico | dígitos sem separador de milhar; ponto (`.`) como decimal |
| Moeda | dígitos sem separador de milhar; ponto (`.`) como decimal |
| Data | `YYYY-MM-DD` |
| Hora | `HH:MM` |
| Booleano | `0` ou `1` |
| Texto | string em ISO-8859-1 |
| Arquivo | par `FileName` + `FileContent` (base64) |

## Drift conhecido na biblioteca `softexpert-orchestrator`

A biblioteca `softexpert-orchestrator` (em `ORQUESTRADOR/softexpert-orchestrator/`) tem **scripts vazios (0 bytes)** desde mar/2026. A SKILL.md dela descreve "25+ métodos cobertos" mas **nada está implementado**. Todos os agentes Maná em produção fazem SOAP manual.

Esta skill (`softexpert-wf-ws`) é a referência canônica enquanto a `softexpert-orchestrator` não for reconstruída.

## Quem consome estes métodos na Maná

| Agente | Métodos usados |
|---|---|
| `agente-cpr` | `newAssocDocument`, `executeActivity` |
| `agente-nf` | `editEntityRecord`, `newChildEntityRecordList` (16 colunas), `executeSystemActivity` (SIS-02) |
| `agente-documentos` | `newAssocDocument` (após `newDocument` no dc_ws), anti-dup via `getAssocDocuments` (dc_ws) |
| `agente-pedidos` | `newChildEntityRecordList` (grid `scredito`) |
| `agente-km` | `editEntityRecord` (`latcampo`/`lngcampo`/`kmrodados`), `newAttachment` (foto) |
| `agente-whatsapp` (notify-comite) | `editEntityRecord` |

## Fontes

- Documentação oficial: `https://developer.softexpert.com` → Guia de integração → Integrações nativas → APIs SOAP → Workflow
- PDFs locais: `pdfs-originais/` (24 capturas FireShot do site oficial)
- WSDL: `https://sementesmana.softexpert.app/apigateway/se/ws/wf_ws.php?wsdl`
