---
name: akita
description: >
  Guia de arquitetura, segurança e testes para criação de agentes e apps — baseado nos padrões reais do Akitaonrails (ai-jail, frank_investigator, frank_fbi, FrankYomik).
  Use esta skill SEMPRE que for projetar ou revisar: pipelines de agentes com LLM, arquitetura de segurança em camadas, sistemas multi-modelo com consenso, estratégias de teste para agentes, ou qualquer app que precise de isolamento, scoring ponderado ou processamento assíncrono.
  Também use quando o usuário mencionar: sandboxing, defense in depth, multi-model consensus, pipeline de análise, idempotência, graceful degradation, job queues, ou pedir para "seguir boas práticas de arquitetura".
---

# Skill Akita — Arquitetura, Segurança e Testes para Agentes

Padrões extraídos de projetos reais do Fábio Akita (akitaonrails): `ai-jail`, `frank_investigator`, `frank_fbi`, `FrankYomik`.

---

## 1. Segurança em Camadas (Defense in Depth)

**Princípio central:** nunca dependa de uma única barreira. Empilhe defesas independentes — se uma falhar, as outras contêm o dano.

### Camadas por contexto

**Para isolamento de processos/agentes (padrão ai-jail):**
1. **Namespace isolation** — PID, UTS, IPC, mount separados
2. **Filesystem control** — Landlock LSM ou equivalente; bloquear `.ssh`, `.aws`, `.gnupg`
3. **Syscall filtering** — seccomp-BPF: filtrar ~30 syscalls perigosas (ptrace, bpf, module loading)
4. **Resource limits** — RLIMIT_NPROC, RLIMIT_NOFILE, RLIMIT_CORE=0
5. **File masking** — substituir `.env`, secrets por arquivos vazios antes de expor ao agente

**Para APIs e endpoints Flask/web:**
1. **Validação de entrada** — regex whitelist antes de qualquer operação (`^[\w\-\.]+$`)
2. **Autenticação** — Bearer token em todos os endpoints (exceto `/health`)
3. **Rate limiting** — por remetente/IP (ex: 20 req/hora)
4. **Deduplicação** — SHA256 para evitar reprocessamento
5. **Dados sensíveis** — criptografar após análise; nunca logar payloads completos

### Regras de ouro
- Valide **antes** de passar qualquer valor para subprocess, SQL ou filesystem
- Use `shell=False` + arglist explícita em subprocess — sempre
- Contas dedicadas para serviços externos (nunca conta pessoal)
- Modo lockdown opcional: read-only por padrão, rw apenas onde necessário
- Seja honesto sobre limites: "não é 100% seguro" é melhor que oversell

---

## 2. Arquitetura de Pipelines

### Pipeline em camadas com pesos (padrão frank_fbi)

Quando o sistema precisa chegar a um score/veredicto, organize em camadas ordenadas por custo:

```
Camada 1 — Determinístico (sem rede, sem LLM)    peso: 0.15
Camada 2 — Cache local + DNS                      peso: 0.15
Camada 3 — Análise de conteúdo (regex/padrões)   peso: 0.15
Camada 4 — APIs externas (com cache + TTL)        peso: 0.15
Camada 5 — OSINT / verificação de entidades       peso: 0.10
Camada 6 — LLM (mais caro, mais poderoso)         peso: 0.30
```

**Fórmula de score ponderado:**
```
score_final = Σ(score_camada × peso × confiança) / Σ(peso × confiança)
```

**Thresholds de veredicto sugeridos:**
- 0–25: Legítimo ✅
- 26–50: Suspeito (provavelmente OK) ⚠️
- 51–75: Suspeito (provavelmente problema) 🚨
- 76–100: Problemático confirmado 🛑

### Idempotência obrigatória
Cada etapa do pipeline deve ser **idempotente** — reprocessar não deve gerar duplicatas nem estados inconsistentes. Guarde resultado de cada step antes de avançar.

### Graceful degradation
- Se API externa falha → fallback para score neutro (50) ou heurística local
- Se LLM retorna JSON inválido → fallback determinístico, nunca crash
- APIs opcionais devem degradar silenciosamente, nunca bloquear o pipeline

### Paralelismo onde possível
```
Job principal
  ├── Camada 1, 2, 3 em paralelo
  └── Camada 4 (depende de 3)
       └── Camada 5 (depende de 1 e 3)
            └── Camada 6 (depende de todas)
                 ├── LLM-A (paralelo)
                 ├── LLM-B (paralelo)
                 └── LLM-C (paralelo)
                      └── Score aggregation → Entrega
```

---

## 3. Consenso Multi-Modelo (Multi-LLM Consensus)

**Princípio:** nunca confie em um único modelo para decisões críticas.

### Padrão frank_fbi / frank_investigator
- Rode 3+ modelos em paralelo (ex: Claude + GPT-4o + Grok)
- Use votação por maioria para veredicto final
- Penalize desacordo entre modelos (alta divergência = confiança menor)
- Fallback: se 1 modelo falha, os outros continuam

### Filosofia "Truth Over Consensus" (frank_investigator)
- **Veto de fonte primária**: se uma fonte primária contradiz, limite a confiança máxima
- **Detecção de câmara de eco**: fontes que só citam umas às outras recebem penalidade
- Temperatura emocional × densidade de evidência: emoção alta + evidência baixa = flag
- Identifique falácias explicitamente (ad hominem, straw man, cherry picking)

### Quando usar consenso
- Classificações com consequências (fraude, crédito, compliance)
- Análise de conteúdo onde viés de um modelo é problema
- Qualquer decisão que vai para produção sem revisão humana

---

## 4. Arquitetura de Sistema

### Stack recomendada por contexto

**Agente leve (API + processamento):**
- Flask + Gunicorn (Python) — simples, direto
- Background jobs: threading ou Celery
- Cache in-memory com TTL

**Agente robusto (produção):**
- Rails 8 + Solid Queue (Ruby) — battle-tested para jobs assíncronos
- SQLite com WAL mode para single-server (surpreendentemente performático)
- Solid Cable para WebSockets
- Kamal para deploy (containers web + worker separados)

**Agente com ML/visão:**
- Go para orquestração/API (alta performance, baixo footprint)
- Python para pipeline ML (ecossistema rico)
- Redis Streams + Pub/Sub para filas assíncronas
- Priorização de jobs (high/low queue)

**Cliente/Frontend:**
- Flutter/Dart para multiplataforma
- SQLite local para cache do cliente

### Isolamento de responsabilidades
```
agente/
├── app.py (ou app.rb)     — rotas HTTP apenas, sem lógica de negócio
├── agente_xxx.py          — lógica de negócio isolada
├── jobs/                  — background jobs separados por responsabilidade
├── requirements.txt       — dependências explícitas
└── Procfile               — comando de start explícito
```

### Deployment
- Um serviço por responsabilidade (web ≠ worker ≠ scheduler)
- Variáveis de ambiente para todos os segredos — nunca hardcode
- Health endpoint obrigatório (`GET /health`)
- Logs estruturados com nível de severidade

---

## 5. Testes para Agentes

### Princípios (padrão frank_fbi)
- **Isole dependências externas nos testes** — WebMock / responses / VCR para HTTP
- **Fixtures reais são ouro** — colete exemplos reais (`.eml`, JSONs, PDFs) como fixtures
- **Determinístico primeiro** — teste as camadas sem LLM antes de testar com LLM
- **Smoke test com caso real** — processe 1 exemplo real end-to-end como sanidade

### Estrutura de testes
```
tests/
├── unit/          — camadas individuais, sem network
├── integration/   — pipeline completo com mocks de APIs
├── fixtures/      — exemplos reais (~30 arquivos)
└── smoke/         — 1 teste end-to-end real
```

### Tarefas de manutenção (padrão frank_investigator)
Exponha rake tasks / comandos CLI para reprocessar sem refetch:
```
agente:reanalyze   — reprocessa análise sem rebuscar dados
agente:refresh     — reconstrói de snapshots armazenados
agente:backfill    — preenche dados faltantes em registros antigos
```

### O que sempre testar em agentes
1. Input inválido / malformado → deve retornar erro claro, não crash
2. API externa fora do ar → deve degradar gracefully
3. LLM retorna JSON inválido → deve ter fallback
4. Reprocessamento do mesmo input → idempotente (resultado igual)
5. Rate limit atingido → deve enfileirar, não dropar

---

## 6. Insights e Decisões de Design

### Escolhas que parecem erradas mas são certas
- **SQLite em produção**: com WAL mode, suporta workloads surpreendentes em single-server. Menos ops, sem servidor separado, backups triviais.
- **LLM como última camada**: não como primeira. Camadas determinísticas são mais rápidas, mais baratas e mais auditáveis — use LLM só onde precisar de raciocínio.
- **Conta Gmail dedicada para agentes de email**: nunca conta pessoal. Regra absoluta.
- **AGPL para projetos de IA**: força que derivações mantenham código aberto.

### Anti-padrões identificados
- ❌ Confiar em um único LLM para decisões críticas
- ❌ `shell=True` em subprocess com input de usuário
- ❌ Variáveis de ambiente sem validação de presença no startup
- ❌ Pipeline bloqueante (camada 6 esperando camada 1 sequencialmente)
- ❌ Sem fallback quando API externa falha
- ❌ Reusar conta pessoal para serviços automatizados
- ❌ Oversell de segurança — seja honesto sobre o que não é coberto

### Configuração como código
- Arquivo `.toml` ou `.yaml` no projeto para config do agente
- Flags CLI sobrescrevem config; config persiste entre sessões
- Modo "lockdown" / "paranoid" como opção explícita, não padrão

### Privacidade e dados
- LLM local (Ollama) quando dados são sensíveis ou custo importa
- Criptografar conteúdo após análise se não precisar ser legível
- Deduplicação por hash antes de processar — evita custo e duplicatas
- Community intelligence (reportar IOCs): opt-in, nunca opt-out

---

## Checklist rápido para novo agente

Antes de ir para produção, confirme:

- [ ] Validação de todos os inputs com whitelist de chars
- [ ] `shell=False` em todo subprocess
- [ ] Bearer token em endpoints não-públicos
- [ ] Rate limiting por remetente/IP
- [ ] Health endpoint retornando status das dependências
- [ ] Variáveis de ambiente validadas no startup (fail fast se faltam)
- [ ] Fallback para cada API externa opcional
- [ ] Jobs são idempotentes
- [ ] Logs com nível de severidade (INFO / WARN / ERROR)
- [ ] Conta dedicada para cada serviço externo
- [ ] Smoke test com dado real antes do deploy
