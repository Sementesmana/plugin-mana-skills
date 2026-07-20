---
name: agente-whatsapp-pa
description: >
  Bot WhatsApp de Plano de Ação integrado ao SoftExpert tmc_ws.php para Sementes Maná LTDA.
  Serviço Flask no Railway que recebe mensagens via agente-whatsapp (Z-API), interpreta com Claude NLP,
  e executa operações no SE Plano de Ação (criar planos, criar ações, consultar progresso).
  Suporta dois perfis: Colaborador (cria e consulta suas próprias ações) e Líder (gerencia planos
  nomeados com liderados como responsáveis, notifica liderados via WhatsApp ao atribuir ação).
  Use este skill SEMPRE que precisar trabalhar com o agente-plano-acao — adicionar intents ao NLP,
  modificar handlers de mensagem, ajustar integração tmc_ws.php, corrigir painel admin, entender o
  schema do banco pa_*, ou depurar erros do bot. Também use quando mencionar: plano de ação,
  ação SE, tmc_ws, bot WhatsApp PA, liderado, líder, PA-MATRICULA, newAction, newActionPlan,
  getAction, executeAction, ou qualquer automação do módulo Plano de Ação do SoftExpert.
---

# Agente WhatsApp — Plano de Ação (agente-plano-acao)

Bot WhatsApp integrado ao SE Plano de Ação via SOAP (tmc_ws.php). Colaboradores enviam mensagens
em linguagem natural -> Claude extrai intenção -> bot executa no SE -> responde no WhatsApp.

## Infraestrutura

| Item | Valor |
|---|---|
| Projeto Railway | agente-plano-acao (repositório isolado) |
| Repositório GitHub | github.com/Sementesmana/agente-plano-acao |
| Branch | main |
| Arquivos principais | app.py, agente_pa.py, se_pa_client.py, db.py |
| Start command | gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 30 |

## Variáveis de ambiente (Railway)

| Variável | Descrição |
|---|---|
| SE_URL | https://sementesmana.softexpert.app |
| SE_PA_USERNAME | Login da conta de serviço SE (com permissão PL025) |
| SE_PA_PASSWORD | Senha da conta de serviço SE |
| SE_API_KEY | Bearer JWT — formato: Bearer eyJ... (inclui o prefixo) |
| ANTHROPIC_API_KEY | Chave Claude AI |
| OPENAI_API_KEY | Chave Whisper (transcrição de áudio — opcional) |
| BANCO_MANA_URL | postgresql://postgres:***@junction.proxy.rlwy.net:18184/railway |
| AGENTE_WA_URL | https://agente-whatsapp-production-eac3.up.railway.app |
| WEBHOOK_SECRET | Mesmo token do agente-whatsapp — enviado como X-API-Key header |
| PAINEL_SENHA | Senha do painel admin (padrão: mana2026) |

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | /health | Status + DB + SE URL |
| POST | /processar-mensagem | Recebe do agente-whatsapp (requer X-API-Key) |
| GET | /admin | Painel HTML de administração |
| GET/POST | /admin/colaborador | Listar / cadastrar colaborador |
| DELETE | /admin/colaborador/<zap> | Soft-delete colaborador |
| POST | /admin/colaborador/<zap>/reset-plan | Zera se_plan_id do colaborador |
| POST | /admin/liderado | Adicionar relação lider->liderado |
| DELETE | /admin/liderado | Remover relação |
| GET | /admin/relacoes | Listar todas as relações lider->liderado |
| GET | /admin/acoes-live/<zap> | Acoes enriquecidas com dados reais do SE |
| DELETE | /admin/acao/<se_action_id> | Apagar ação do banco local |
| POST | /admin/sincronizar-se | Marca planos/acoes inexistentes no SE como inativos |
| POST | /admin/limpar-inativos | Deleta registros com ativo=FALSE do banco |

## Arquitetura e fluxo

WhatsApp -> Z-API -> agente-whatsapp -> POST /processar-mensagem -> agente-plano-acao
-> Claude NLP -> se_pa_client.py (SOAP tmc_ws.php) -> SE -> resposta
-> enviar_resposta() -> POST /send-whatsapp (agente-whatsapp, header X-API-Key)
-> Z-API -> WhatsApp

### enviar_resposta() — autenticação correta
```python
# Header: X-API-Key (nao X-Webhook-Secret)
# Campo: "telefone" (nao "numero")
headers["X-API-Key"] = WEBHOOK_SECRET
payload = {"telefone": numero_zap, "mensagem": mensagem}
```

## Perfis de usuário

### Colaborador (eh_lider = FALSE)
- Cria ações para si mesmo (plano genérico PA-{SE_USERNAME})
- Consulta ações em aberto/atraso com %, resultado e prazo reais do SE
- Ve o plano completo com dados reais do SE

### Líder (eh_lider = TRUE)
- Cria planos nomeados (ex: "Financeiro", "Safra 26/27")
- Cria ações em planos, atribuindo liderados como responsáveis
- Liderado recebe notificação WhatsApp ao ter ação atribuída
- Ve resumo da equipe: IDs do banco + dados reais do SE (%, resultado, prazo, título)

## Fonte de verdade — banco vs SE

| Dado | Fonte |
|---|---|
| IDs (se_action_id, se_plan_id) | Banco local (shadow table) |
| Nome do plano | Banco local pa_planos.nome (gravado na criação, raramente muda) |
| % realizado (VlPercent) | SE — sempre via getAction |
| Título da ação (ActionTitle) | SE — sempre via getAction |
| Prazo real (DtPlanEnd) | SE — sempre via getAction |
| Resultado (DsResult) | SE — sempre via getAction, exibido como 📝 em todas as views |
| Status (FgStatus) | SE — sempre via getAction |

get_acoes_by_zap() usa DISTINCT ON (se_action_id, se_plan_id) para evitar duplicatas no banco.

## Intents do NLP

| Intent | Quando disparar | Quem pode usar |
|---|---|---|
| criar_plano | "cria plano chamado X" | Líder |
| criar | "cria ação no plano X: título, responsável Y, prazo D" | Todos |
| listar_planos | "meus planos", "quais planos tenho" | Líder |
| plano | "ver plano Financeiro", "ações do plano X" | Todos |
| consultar | "minhas ações", "em aberto" | Todos |
| equipe | "ver equipe", "resumo da equipe" | Líder |
| acoes_liderado | "ações do João", "como está o João" | Líder |
| menu | "menu", "ajuda" | Todos |

## SE SOAP — tmc_ws.php

Endpoint: {SE_URL}/apigateway/se/ws/tmc_ws.php
Namespace: urn:timecontrol
Auth: header Authorization: Bearer {SE_API_KEY} + corpo SOAP com Login/Password

### Métodos em se_pa_client.py

| Método SOAP | Função Python | Descrição |
|---|---|---|
| newActionPlan | new_action_plan() | Cria plano de ação |
| sendActionPlanToNextStep | send_action_plan_to_next_step() | Avança plano para Execução |
| newAction | new_action() | Cria ação dentro de um plano |
| editAction | edit_action() | Edita prazo / resultado |
| executeAction | execute_action() | Conclui ação (% = 100) |
| getAction | get_action() | Consulta VlPercent, DsResult, ActionTitle, DtPlanEnd, FgStatus |
| getActionPlan | get_action_plan() | Lista todas as ações de um plano |
| newIsolatedAction | new_isolated_action() | Cria ação isolada (sem plano) — legado |
| editIsolatedAction | edit_isolated_action() | Edita ação isolada |
| executeIsolatedAction | execute_isolated_action() | Conclui ação isolada |

### Campos-chave do SE

| Campo | Uso |
|---|---|
| ActionplanID | ID do plano: PA-{MATRICULA}-P{N} ex: PA-28051625870-P3 |
| RespID | Matrícula do responsável pela ação |
| VlPercent | % Realizado float ex: "30.00" — ausente se nunca preenchido (tratar como 0%) |
| DsResult | Resultado acumulado — exibido como 📝 |
| DsWhy | Historico de atualizações |
| FgStatus | 1=Planejamento 2=Aprovação 3=Execução 4=Verificação 5=Finalizado 6=Cancelado |
| ActionTitle | Título da ação no SE |
| DtPlanEnd | Prazo da ação no SE |

### Gotchas críticos

- HTTP 200 body vazio = sucesso (editIsolatedAction)
- newAction requer DtPlanStart e DtPlanEnd obrigatórios
- SE_API_KEY ja inclui "Bearer " — não concatenar novamente
- sendActionPlanToNextStep nao aceita UserID — só ActionPlanID
- Plano fechado: bot cria novo plano incrementando versão P1->P2->P3
- VlPercent ausente nas RAW TAGS se nunca preenchido — tratar como 0%

## Schema pa_* (PostgreSQL banco-mana)

```
pa_colaboradores: numero_zap PK, nome, se_username, eh_lider, ativo, se_plan_id
pa_lideres_liderados: lider_zap, liderado_zap, UNIQUE(lider_zap, liderado_zap)
pa_planos: se_plan_id UNIQUE, nome, lider_zap, ativo
pa_acoes: se_action_id, titulo, responsavel_zap, responsavel_se, criado_por_zap,
          se_plan_id, percentual, dt_prazo, situacao, obs  [shadow table]
pa_sessoes: numero_zap PK, estado, dados JSONB, expira_em  [TTL 15 min]
```

## Painel Admin (/admin)

- Senha: PAINEL_SENHA
- Matrícula SE = número numérico ex: 28051625870 (nao o login joao.silva)
- Botão Ver Ações: /admin/acoes-live/<zap> — dados reais do SE
- Botão Sincronizar SE: marca inexistentes como ativo=FALSE
- Botão Limpar Inativos: deleta registros ativo=FALSE

## Notificação ao criar ação para liderado

```
Ola, *{nome_liderado}*! Nova ação atribuída:
📋 *{se_action_id}* — {titulo}
📅 {inicio} -> {prazo}
📁 Plano: {nome_plano}
```

## Erros conhecidos e soluções

| Erro | Causa | Solução |
|---|---|---|
| SyntaxError painel admin (Enter nao funciona) | Unicode U+21BB ou U+2715 em string JS em triple-quote Python | Usar HTML entities: &#x21BB; e &#x2715; |
| Erro de sintaxe em onclick JS | Python processa barra-barra-aspas -> aspas em triple-quoted | Usar dupla-barra-barra-aspas no fonte Python |
| 401 ao enviar para agente-whatsapp | Header ou campo errado | X-API-Key (nao X-Webhook-Secret) e campo telefone (nao numero) |
| AttributeError: no attribute enviar_resposta | Funcao perdida por truncação | Recriar em agente_pa.py com X-API-Key e telefone |
| Duplicatas no banco | Sem DISTINCT | get_acoes_by_zap usa DISTINCT ON (se_action_id, se_plan_id) |
| IndentationError no deploy | Arquivo truncado | py_compile antes de push; usar python3 << EOF via bash para editar |
| 0% SE sempre no admin | app.py usava SEActionPlanClient (classe inexistente) | import se_pa_client as _se; _se.get_action(...) |
| Arquivos truncados | Edit tool trunca arquivos grandes no Windows CRLF | python3 - << 'EOF' via bash para modificar arquivos grandes |
