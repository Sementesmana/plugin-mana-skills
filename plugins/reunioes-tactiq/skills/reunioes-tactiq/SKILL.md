---
name: reunioes-tactiq
description: Acesso às reuniões da Sementes Maná via Tactiq MCP + transcrições completas no Google Drive. Use SEMPRE que o Xayer pedir qualquer coisa sobre uma reunião — "gera o HTML da reunião" (termo principal do Xayer), resumo, action items, decisões, "o que ficou combinado", cruzar reuniões, transformar reunião em documento/e-mail/plano. Também quando mencionar Tactiq, transcrição, "html da reunião", "reunião de ontem/hoje/semana passada", "reunião com [pessoa]", "gera a ata", "lista as reuniões", Meeting Transcription, ou qualquer análise de conversa gravada. O HTML da reunião é só UM dos formatos — a skill cobre qualquer finalidade sobre qualquer reunião.
---

# Reuniões Tactiq — Sementes Maná

Fluxo validado em 2026-07-02 para acessar reuniões (Google Meet/Zoom/Teams transcritas pela Tactiq) e produzir qualquer saída: HTML da reunião (documento visual padrão Maná), resumo, action items, análise, documento.

## Arquitetura (por que é assim)

A Tactiq expõe um MCP oficial (`https://mcp.tactiq.io`), mas no **plano Pro ele só lista/busca reuniões — nunca entrega conteúdo** (`get_meeting` retorna erro `mcp:meetings:details permission`; conteúdo só no plano Team, e mesmo assim só resumo de IA, nunca transcrição bruta). Por isso o conteúdo vem por outro caminho: o **auto-save da Tactiq grava a transcrição completa como Google Doc** na pasta **"Tactiq Transcription"** do Drive do Xayer (coronelxavier992@gmail.com), conectado via conector Google Drive.

Divisão de papéis:

| Fonte | Serve para | Nunca use para |
|---|---|---|
| Tactiq MCP (`list_recent_meetings`, `search_meetings`) | Localizar reunião: data, participantes, duração, id | Ler conteúdo (falha no plano Pro) |
| Google Drive (pasta "Tactiq Transcription") | Transcrição completa com timestamps | Buscar por assunto (títulos são genéricos) |

## Workflow

### 1. Localizar a reunião (Tactiq MCP)

- Pedido vago ("reuniões recentes") → `list_recent_meetings`.
- Data/pessoa/tópico → `search_meetings` com `dateFrom`/`dateTo`/`participants`. Pessoas vão em `participants`, NUNCA em `query`; NUNCA incluir o próprio Xayer em `participants` (retorna zero).
- Guardar da reunião escolhida: `id`, `createdAt`, `attendees`, `durationSeconds`. Ignorar reuniões de segundos de duração (testes/ruído).
- Se o usuário precisa escolher, apresentar lista curta: data/hora BRT (createdAt é UTC; BRT = UTC−3), participantes, duração em minutos.

### 2. Achar a transcrição no Drive

O Doc contém o **id da reunião** no link do cabeçalho (`app.tactiq.io/api/2/u/m/r/<id>`). Matching determinístico:

```
search_files: fullText contains '<meeting-id>'
```

Fallback: listar Docs da pasta "Tactiq Transcription" (título "Meeting Transcription") e casar pelo cabeçalho do Doc (data "2 Jul 2026 | Meeting Transcription" + Attendees).

Se não existir Doc: o auto-save só vale para reuniões **a partir de 2026-07-02**. Para antigas, pedir ao Xayer que abra a reunião na Tactiq e exporte manualmente pro Drive (ou, em último caso, cole a transcrição no chat).

### 3. Ler e interpretar a transcrição

`read_file_content` no Doc. Formato: cabeçalho Tactiq + `# Transcript` com blocos `**MM:SS Nome:** fala`.

Cuidados de interpretação (transcrição ASR de reunião real):

- **Erros de reconhecimento são a regra.** Termos do domínio saem corrompidos: "barter" vira barca/barco/Barker/Parker/marker; "Protheus" vira Proteus/protesto; "Simple Agro" vira simpoagro/ciclo água/setor Água. Normalizar pelo contexto Maná (consultar ManaVault/03-Sistemas/ se necessário).
- **Nunca inventar ou "corrigir" nomes de pessoas.** Usar como estão; se a grafia varia (ex.: três grafias do mesmo nome), adotar uma e sinalizar a variação. Em dúvida sobre papel/cargo, perguntar ao Xayer em vez de assumir.
- Falas truncadas/interrompidas: reconstruir o sentido pelo diálogo, não citar literalmente trecho sem sentido.

### 4. Gerar a saída pedida

Qualquer formato. Os mais comuns:

- **HTML da reunião** (formato principal — Xayer chama de "gerar o HTML da reunião"; é uma ata visual): ver template abaixo. Salvar em `C:\Users\Sementes Mana\Desktop\ORQUESTRADOR\` como `reuniao-<tema>-<YYYY-MM-DD>.html` e apresentar com present_files. Referência viva: `ORQUESTRADOR/reuniao-kickoff-sistema-barter-2026-07-02.html`.
- **Resumo / action items**: prosa concisa; ações sempre com responsável e, se dito, prazo.
- **Análise multi-reunião**: repetir passos 1–3 por reunião antes de cruzar.

## Template do HTML da reunião

Single-file, sem dependências externas, identidade Maná:

- Cores: verde `#1D6B3E` / verde escuro `#14502D`, ouro `#B8860B` / ouro claro `#F5E6C8`, fundo `#f4f6f5`.
- Header em gradiente verde com tag "Ata de Reunião", título, subtítulo, chips de meta (Data, Participantes, Formato).
- Seções numeradas em cards brancos: **1. Contexto** (prosa) · **2. Situação atual / o que foi apresentado** (grid de cards) · **3. Fluxo/processo mapeado** (lista numerada com passos circulares e badges de sistema, ex.: Simple Agro / Plataforma / Protheus) · **4. Dores e gaps** (lista) · **5. Decisões** (blocos D1, D2… com borda ouro) · **6. Próximos passos** (tabela Ação × Responsável) · **7. Backlog futuro** (lista).
- Adaptar as seções ao tipo de reunião — reunião de status não precisa de "fluxo mapeado"; comitê precisa de votos. O esqueleto é guia, não camisa de força.
- Footer: "Sementes Maná LTDA · Projeto Hiperautomação · Documento gerado a partir da transcrição da reunião de DD/MM/AAAA".
- `@media print` com quebra por seção.

## Disciplina Maná (obrigatória)

- HTML/resumo que registre **decisão arquitetural** sobre agentes/sistemas → avisar o Xayer que pode merecer ADR em `ManaVault/08-Decisoes/`.
- Descoberta relevante durante o trabalho → capturar em `ManaVault/00-Inbox/`.
- Conteúdo de reunião pode ter dado sensível (valores, CPF, crédito de cliente): o HTML fica local no ORQUESTRADOR; não enviar conteúdo pra fora sem o Xayer pedir.

## Troubleshooting

| Sintoma | Causa provável | Ação |
|---|---|---|
| `get_meeting` → erro de permissão | Plano Pro (esperado) | Usar o Drive; não é bug |
| Doc não aparece no Drive | Reunião antiga, auto-save desligado, ou transcrição vazia (reunião de segundos) | Export manual na Tactiq; verificar toggle "Salvar automaticamente" em Integrações → Google Drive |
| Doc recém-terminado ausente | Delay de 1–2 min pós-reunião | Aguardar e repetir busca |
| search_meetings retorna vazio | Nome em `query`, ou Xayer em `participants` | Corrigir parâmetros conforme passo 1 |
