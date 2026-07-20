---
name: agente-whatsapp
description: >
  Agente de envio de mensagens WhatsApp via Z-API para Sementes Maná LTDA. Serviço Flask no Railway que
  envia mensagens para números individuais e grupos do WhatsApp sem necessidade de aprovação de template Meta.
  Conecta via QR Code com número pessoal. Suporta texto livre, templates pré-definidos (crédito aprovado,
  reprovado, pendência de documentos) e envio em massa. Integrado ao SoftExpert como Fonte de Dados REST
  em Atividades Sistêmicas. Use este skill sempre que precisar trabalhar com o agente-whatsapp —
  enviar mensagens, adicionar templates, modificar endpoints, corrigir integração Z-API, configurar
  grupos, adicionar webhooks de entrada, implementar transcrição de áudio, ou entender a arquitetura
  do serviço WhatsApp. Também use quando o usuário mencionar WhatsApp, Z-API, grupos, mensagem automática,
  notificação WhatsApp, ou qualquer integração entre SoftExpert e WhatsApp.
---

# Agente WhatsApp — Sementes Maná

Serviço Flask implantado no Railway que envia mensagens WhatsApp via Z-API (alternativa ao Twilio sem
necessidade de aprovação de template Meta). Conecta via QR Code — o número permanece ativo no celular
enquanto a API envia em paralelo.

## Infraestrutura

| Item | Valor |
|---|---|
| URL produção | `https://agente-whatsapp-production-eac3.up.railway.app` |
| Projeto Railway | `keen-luck` |
| Root Directory | `/agente-whatsapp` |
| Repositório | `github.com/Sementesmana/hiperautomacao-mana` |
| Branch | `main` |
| Arquivos principais | `agente-whatsapp/agente_whatsapp.py`, `agente-whatsapp/app.py` |

## Variáveis de ambiente (Railway)

| Variável | Descrição |
|---|---|
| `ZAPI_INSTANCE_ID` | ID da instância Z-API (`3F1196C7F833710CDF0B3EDA471FC5DF`) |
| `ZAPI_TOKEN` | Token da instância — atenção: termina em `DDEB`, não `0DEB` |
| `ZAPI_CLIENT_TOKEN` | Security Token da conta Z-API (obtido em Segurança → Token de segurança) |

## Endpoints disponíveis

### GET /health
Verifica se o serviço está online e se o WhatsApp está conectado.
```json
{"whatsapp_conectado": true, "whatsapp_status": "online", "telefone_conectado": "..."}
```

### POST /send-whatsapp
Envia mensagem para número individual ou grupo. Aceita dois modos:

**Modo texto livre:**
```json
{"telefone": "64996261541", "mensagem": "Texto da mensagem"}
```

**Modo template pré-definido:**
```json
{
  "telefone": "62994331331",
  "template": "workflow_aprovado",
  "variaveis": {"nome": "João Silva", "numero": "000142", "limite": "50.000,00", "safra": "26/27"}
}
```

**Envio para grupo** (usar ID do /grupos no campo telefone):
```json
{"telefone": "120363405530482862-group", "mensagem": "Mensagem para o grupo"}
```

> O campo `telefone` aceita número pessoal (ex: `64996261541`) OU ID de grupo (ex: `120363405530482862-group`).
> Aceita parâmetros via JSON body **ou** query string (compatibilidade SoftExpert).

### POST /send-whatsapp-lista
Envia a mesma mensagem para múltiplos destinatários.
```json
{"telefones": ["64996261541", "62994331331"], "mensagem": "Texto"}
```

### GET /grupos
Lista todos os grupos WhatsApp com IDs e nomes.
```json
{"grupos": [{"id": "120363405530482862-group", "nome": "Governança Sementes Maná"}], "total": 10}
```

## Templates pré-definidos

| Chave | Variáveis | Uso |
|---|---|---|
| `workflow_aprovado` | nome, numero, limite, safra | Notificação de crédito aprovado |
| `workflow_reprovado` | nome, numero | Notificação de crédito reprovado |
| `pendencia_documentos` | nome, numero | Solicitar documentos pendentes |
| `solicitacao_atualizada` | nome, numero | Atualização genérica de processo |
| `notificacao_generica` | nome, mensagem | Mensagem livre com cabeçalho Maná |

Para adicionar novo template, editar `TEMPLATES` em `agente_whatsapp.py`.

## Grupos WhatsApp mapeados

| Nome | ID |
|---|---|
| Governança Sementes Maná | `120363405530482862-group` |
| TIME - SEMENTES MANÁ | `556481434577-1615203415` |
| Comercial J2A | `556599988066-1530534657` |
| Mural do RH \| Sementes Maná | `120363405446308588-group` |
| Teste Hiperautomação RPA CLAUDE | `120363408264194294-group` |
| Relatórios de Campo | `120363422681329422-group` |
| Maná x Softexpert | `120363406035520752-group` |

## Integração SoftExpert (Fonte de Dados REST)

Fonte configurada como `agente_whatsapp_railway`:
- **URL:** `https://agente-whatsapp-production-eac3.up.railway.app/send-whatsapp`
- **Método:** POST
- **Parâmetros de entrada:** `telefone` (QUERY, STRING), `mensagem` (QUERY, STRING), `Content-Type` (HEADER, `application/json`)
- **Corpo da requisição:** `{"telefone": "{telefone}", "mensagem": "{mensagem}"}`
- **Retorno:** status, telefone, timestamp, zaapi_id

## Como fazer deploy/atualização

```bash
# Repo local no container
cd /sessions/admiring-modest-gauss/repo-mana

# Copiar arquivo modificado
cp /sessions/.../ORQUESTRADOR/agente-whatsapp/app.py agente-whatsapp/
cp /sessions/.../ORQUESTRADOR/agente-whatsapp/agente_whatsapp.py agente-whatsapp/

# Commit e push (Railway faz deploy automático)
git add agente-whatsapp/
git commit -m "feat: descrição da mudança"
git push
```

> Gerar novo token em github.com/settings/tokens com permissão `repo` quando necessário.

## Arquitetura Z-API

```
SoftExpert (Atividade Sistêmica)
    ↓ POST /send-whatsapp
Railway Flask (agente-whatsapp)
    ↓ POST /send-text
Z-API (instância web)
    ↓ via protocolo WhatsApp
WhatsApp (número conectado via QR Code)
```

O número conectado permanece funcional no celular — Z-API funciona em paralelo (Multi Device).

## Próximas funcionalidades planejadas

### Fluxo Inverso (webhook de entrada)
Receber mensagem no WhatsApp → Z-API dispara webhook → Railway processa → Claude AI extrai dados → SoftExpert instancia processo com formulário preenchido.

**Para implementar:**
1. Adicionar endpoint `POST /webhook-incoming` no `app.py`
2. Configurar webhook na Z-API (Instâncias Web → aba "Webhooks e configurações gerais")
3. Usar Claude API para extrair campos da mensagem de texto
4. Chamar SoftExpert SOAP para instanciar workflow

### Suporte a Áudio
Z-API entrega URL do áudio no payload do webhook → baixar arquivo → transcrever com OpenAI Whisper → extrair dados → instanciar processo SE.

Requer variável adicional: `OPENAI_API_KEY` no Railway.

## Erros conhecidos e soluções

| Erro | Causa | Solução |
|---|---|---|
| `{"error":"Instance not found"}` | Token errado no Railway | Verificar ZAPI_TOKEN — termina em `DDEB` não `0DEB` |
| `whatsapp_conectado: false` | WhatsApp desconectou | Z-API → Instâncias Web → escanear QR Code novamente |
| `Campo 'telefone' obrigatório` | SE enviando params como query string | API já aceita ambos; verificar corpo da requisição no SE |
| HTTP 400 do Z-API | Client-Token inválido ou ausente | Verificar ZAPI_CLIENT_TOKEN no Railway |
