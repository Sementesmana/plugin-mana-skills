---
name: mana-softexpert
description: >-
  SDK Camada 2A da Maná Builder — ESCRITA no SoftExpert Workflow via wf_ws.
  Use SEMPRE que um agente/app precisar: instanciar processo no SE
  (newWorkflow), preencher formulário (editEntityRecord — campos texto/opção
  E campo tipo ARQUIVO via EntityAttributeFileList), anexar documento em
  atividade (newAttachment, ATV-XX habilitada), ou cancelar instância
  (cancelWorkflow). Instalar via pip git+tag em vez de copiar bloco SOAP.
  Também quando mencionar: escrever no SE, criar solicitação de crédito por
  API, endosso, popular scred/contapagar/formscpr, campo arquivo do
  formulário, termoanuencia, anexar na ATV-01, sessão SOAP persistente,
  wsdl session viva, code -5 processo não encontrado, SoftExpertError,
  mana-softexpert. A skill softexpert-wf-ws é a documentação dos 23 métodos;
  este SDK é o código pronto dos 5 de escrita mais usados.
---

# SDK mana-softexpert — escrita no SoftExpert Workflow

> **Regra:** agente que escreve no SE NÃO copia bloco SOAP — instala o SDK.
> Extraído de consumidor real em produção (endossos do agente-comercio-revendas,
> processo CRE-001 real com form + campo arquivo + anexos, 2026-07-10).

## Instalação (requirements.txt do agente)

```
mana-softexpert @ git+https://github.com/Sementesmana/mana-softexpert.git@v0.1.0
```

## Setup (1× por agente — env vars no Railway)

```python
import os
from mana_softexpert import SoftExpertWF, SoftExpertError

se = SoftExpertWF(
    base_url=os.environ["SE_URL"],
    api_key=os.environ["SE_API_KEY"],
    user_id=os.environ.get("SE_USER_ID", ""),   # matrícula do executor
)
```

## Receita completa (padrão endosso → CRE-001)

```python
# 1. instanciar → SALVAR o idprocess IMEDIATAMENTE (amarre + retry idempotente)
idp = se.new_workflow("SM.CV.PR.NE.CRE-001", f"ENDOSSO - {cliente} - {revenda}")
db.execute("UPDATE endossos SET idprocess=%s WHERE id=%s", [idp, eid])

# 2. formulário (uma chamada, campos vazios são filtrados)
se.edit_form(idp, "scred", {"nomeclientenovo": nome, "uf": uf, ...})

# 3. campo tipo ARQUIVO do formulário
se.edit_form_arquivo(idp, "scred", "termoanuencia", "termo.pdf", pdf_bytes)

# 4. anexos da atividade (1 por chamada; sessão persistente barateia)
for doc in docs_pendentes:
    se.anexar(idp, "ATV-01", doc.filename, doc.bytes)
    marcar_anexado(doc)   # retry anexa só o que faltou

# 5. excluir no app → cancela no SE (WS não exclui)
se.cancel_workflow(idp, "excluído pelo painel")
```

## Erros

`FAILURE` do SE → `SoftExpertError` com `.code`/`.detail`. Casos clássicos:

| Code | Causa provável |
|---|---|
| `-5` processo não encontrado | ProcessID errado OU usuário sem permissão de INSTANCIAR (lista escopada) OU **vírgula/espaço colado no valor da env** |
| anexo falha | atividade não HABILITADA (anexo é da atividade, não da instância) |

## Regras que o SDK já cumpre por você

- Sessão HTTP persistente (thread-safe) — nunca abrir 1 conexão por chamada
- Escape XML de todos os valores
- base64 do binário nos arquivos
- Zero credencial no código (env do consumidor)
- Nada passa por LLM (transporte app→SE direto)

## Chamadas a partir de webhook (regra da casa)

Envio ao SE é LENTO (segundos). Em caminho de webhook/painel com workers=1:
responder primeiro, rodar o envio em **thread background** com guard-com-validade
(padrão do agente-comercio-revendas / skill mana-memoria-operacional §5).

## Relacionados

- Skill `softexpert-wf-ws` — documentação canônica dos 23 métodos (o "porquê")
- `mana-habilidade-se-dataset-reader` — o par de LEITURA (Conjuntos de Dados REST)
- Repo: https://github.com/Sementesmana/mana-softexpert (manifest.yaml = estado)
