---
name: mana-builder-guia
description: >-
  Skill de ENTRADA do Maná Builder. Guia interativamente o dev Maná (Xayer, Dayan, Lorena,
  futuros) a criar artefato novo (agente, app, habilidade, painel, atividade-SE) na estrutura
  Sementes Maná — Sementesmana no GitHub + Railway. Faz perguntas em ordem, aponta pra
  habilidades reusáveis disponíveis, hubs institucionais (LLM/WhatsApp/router), templates,
  runbooks e outras skills complementares. Termina com checklist e comandos concretos.
  Use SEMPRE que o dev disser: "quero criar", "novo agente", "nova habilidade", "app novo",
  "criar coisa nova", "não sei como começar", "por onde começo no Maná", ou variações.
  Também use quando o dev perguntar "que habilidades tem?", "onde tá o hub de X?",
  "que template usar?". É skill CATÁLOGO + GUIA — orienta, não implementa. Depois de
  usar, roteia pra skills específicas (novo-agente-mana, nova-habilidade-mana, etc).
categoria: governanca
owner: xayer-mana
versao-skill: 1.0.1
ultima-revisao: 2026-06-30
ativacao:
  - quero criar
  - novo agente
  - nova habilidade
  - app novo
  - criar coisa nova
  - por onde começo
  - por onde comeco
  - não sei como começar
  - nao sei como começar
  - guia mana builder
  - que habilidades tem
  - marketplace mana
---

# mana-builder-guia — o guia do dev autônomo Maná

> Você (Claude do Cowork) foi ativado pra guiar o dev na criação de artefato novo no ecossistema Maná. Faça as perguntas na ordem abaixo, uma por vez, e aponte pras peças certas conforme a resposta.

## 🧭 Filosofia (leia ANTES de qualquer coisa)

**Habilidades Maná NÃO são código pronto pra copiar.** Elas são **primitivas reusáveis + API wrappers** que dão RECURSOS. Você (Cowork) lê o SKILL.md canônico da habilidade → entende a API → **COMPÕE código NOVO** específico pro caso do dev.

Exemplos:
- `se-dataset-reader` é wrapper genérico pra ler **QUALQUER** Conjunto do SoftExpert. O dev cria o Conjunto próprio no SE (via skill `softexpert-dataset-integration`), e você usa o wrapper com o `id_dataset` específico dele. Não copia o exemplo — usa o wrapper como referência da API.
- `data-lake-pg` é cache genérico pra **QUALQUER** fonte lenta. O dev define a chave lógica + a função pesada dele. Você compõe o `read_or_compute()` com isso.
- Hubs (`agente-whatsapp`, `mana-llm-gateway`) são endpoints HTTP institucionais. Dev decide o quê/quando enviar; você monta o payload.
- Habilidades de utilitário (PDF, PII, áudio) dão primitivas; você compõe o layout/lógica.

**Fluxo mental correto:**

```
1. Você (Cowork) lê o SKILL.md canônico da habilidade no GitHub
2. Você aprende: que API ela expõe, que parâmetros aceita, que retorna
3. Você COMPÕE código específico do que o dev pediu, USANDO essa API
4. Se algo não bate, você adapta a lógica (não a habilidade)
```

**Nunca faça:** copiar bloco de exemplo da habilidade e trocar valores. Isso é anti-padrão — perde a flexibilidade que o wrapper foi feito pra dar.

**Sempre faça:** ler a API, entender os parâmetros, e escrever código novo usando os primitivos.

## Papel da skill

Você é o **guia** — pergunta o que o dev quer, mapeia pros recursos disponíveis (habilidades + hubs + fontes de dados + skills complementares), e monta o checklist. **Não implementa** — só orienta o próximo passo. Ao final, roteia pras skills específicas (novo-agente-mana, nova-habilidade-mana, etc) que fazem o scaffold real.

## Contexto Maná (o que o dev precisa saber)

- **GitHub:** organização `Sementesmana` (member do dev já configurado)
- **Railway:** workspace pessoal do Xayer, dev é Admin (pode criar projects/services)
- **Vault:** `~/Desktop/ORQUESTRADOR/ManaVault/` — memória compartilhada
- **Fluxo autônomo:** dev cria repo privado direto no Sementesmana + service no Railway, sem passar por Xayer (Caminho A, ADR 2026-06-14 modelo federado)
- **Se precisar repo público** (só pra habilidade): Dayan cria privado → avisa Xayer → Xayer promove pra público em Settings do repo (limitação plano Free)

## 0️⃣ Antes de começar — sincronize (OBRIGATÓRIO todo dia)

Antes de tocar em QUALQUER coisa, puxe o estado atual do GitHub. Sem isso você trabalha em cima de estado velho e bate conflito na hora do push.

```bash
cd ~/Desktop/ORQUESTRADOR/ManaVault
git pull

# E se você já tem clone local do agente/habilidade que vai mexer:
cd ~/Desktop/ORQUESTRADOR/<nome-do-repo>
git pull
```

**Por quê:** modelo federado (ADR 2026-06-14) trata GitHub como fonte da verdade e cada máquina como cópia descartável. Outros donos (Xayer, Dayan, Lorena, futuros) podem ter empurrado notas novas, ADRs, novas habilidades, mudanças em SDKs desde ontem. Se você não puxa, você:
- Recria coisa que já existe (drift)
- Consome versão antiga de habilidade/SDK (bug fantasma)
- Ignora ADR que virou regra ontem
- No push, dá `non-fast-forward` e você trava

**Ao terminar de mexer:** `git push` no repo do agente/habilidade E no ManaVault (se editou nota). Sem push, seu trabalho fica só na sua máquina e você bloqueia os outros — o modelo federado quebra.

**Se der conflito no pull** (raro se você seguir "1 motorista por solução"): pare e chame Xayer. Não force merge sem entender o que o outro dono mudou.

## Perguntas — faça UMA por vez, aguarde resposta

### 1️⃣ Que tipo de artefato quer criar?

Opções (o dev escolhe uma):

| Tipo | Descrição | Skill específica |
|---|---|---|
| **Agente** | Serviço Flask que roda no Railway (chatbot, cron, orquestrador) | `novo-agente-mana` |
| **App/Painel** | Dashboard HTML/Alpine, front-end pra usuário Maná | `novo-agente-mana` (mesmo scaffold) |
| **Habilidade** | Pacote Python reusável (`mana-habilidade-*`) — repo separado | `nova-habilidade-mana` (a criar) OU template `Sementesmana/template-habilidade-mana` |
| **Atividade SE** | Endpoint chamado por Sistêmica do SoftExpert | `novo-agente-mana` + skill `softexpert-wf-ws` |

### 2️⃣ Que INTEGRAÇÕES ele vai precisar?

Vai pra cada uma que ele confirmar. Depois de todas, monta o checklist final.

#### 🤖 Chama Claude/LLM?

**SIM → USE o `mana-llm-gateway`** (regra ADR 2026-06-13: proibido chamar `api.anthropic.com` direto).

- URL: `https://mana-llm-gateway-production.up.railway.app`
- Precisa de **chave virtual** — dev pede pro Xayer criar via admin (ou skill `mana-llm-gateway` se existir)
- Env vars: `LLM_GATEWAY_URL` (raiz, sem `/v1`) + `LLM_GATEWAY_KEY` + `LLM_MODEL=mana-rapido`
- Aliases disponíveis: `mana-rapido` (Haiku), `mana-equilibrio` (Sonnet), `mana-juridico` (Opus)
- **Skill de referência:** carregar skill `mana-arquitetura-padrao` pra padrão obrigatório

#### 📱 Manda WhatsApp?

**SIM → USE o hub `agente-whatsapp`** (regra ADR 2026-06-13: proibido Z-API direto).

- URL: `https://agente-whatsapp-production.up.railway.app`
- Endpoint: `POST /send-whatsapp`
- Env vars: `AGENTE_WHATSAPP_URL` + `AGENTE_WHATSAPP_API_KEY` (=`WEBHOOK_SECRET` do hub)
- Payload obrigatório: `{telefone, mensagem, classe: "conversacional|transacional|massa", idempotency_key, agente}`
- **Áudio/PDF/documento:** `POST /send-document` no mesmo hub
- **Recebe WhatsApp?** Precisa passar pelo `agente-router` (relay central) — endpoint dele encaminha pra você via webhook

#### 📊 Lê dados do SoftExpert (workflows, formulários)?

**SIM → USE a habilidade `mana-habilidade-se-dataset-reader` v0.1.0**

- Instalação: `pip install "git+https://github.com/Sementesmana/mana-habilidade-se-dataset-reader.git@v0.1.0"`
- Pré-requisito: criar Conjunto de Dados no SE (fonte SESUITE). Skill `softexpert-dataset-integration` ensina como.
- Uso mínimo:
  ```python
  from mana_habilidade_se_dataset_reader import SEDatasetReader
  reader = SEDatasetReader(se_url=SE_URL, se_token=SE_TOKEN)
  linhas = reader.ler("NOME_DO_CONJUNTO")
  ```
- **Baixar SKILL.md canônico:** https://github.com/Sementesmana/mana-habilidade-se-dataset-reader/blob/main/SKILL.md

#### 💾 Vai ter painel com fonte lenta (SE/SA/APIs)?

**SIM → USE a habilidade `mana-habilidade-data-lake-pg` v0.1.0**

- Instalação: `pip install "git+https://github.com/Sementesmana/mana-habilidade-data-lake-pg.git@v0.1.0"`
- Pré-requisito: `BANCO_MANA_URL` (banco Postgres compartilhado)
- Uso mínimo:
  ```python
  from mana_habilidade_data_lake_pg import DataLake
  lake = DataLake(db_url=DATABASE_URL, schema="agente_meu", advisory_lock_id=12345)
  lake.init_schema()
  # Ingestão (cron/botão): lake.upsert("workflows", get_workflows())
  # Leitura: lake.read_or_compute("workflows", get_workflows, max_age_hours=24)
  ```
- **Baixar SKILL.md canônico:** https://github.com/Sementesmana/mana-habilidade-data-lake-pg/blob/main/SKILL.md

#### 🎤 Transcreve áudio (Whisper)?

**SIM → USE a habilidade `mana-habilidade-transcrever-audio` v0.1.0**

- Instalação: `pip install "git+https://github.com/Sementesmana/mana-habilidade-transcrever-audio.git@v0.1.0"`
- **Baixar SKILL.md:** https://github.com/Sementesmana/mana-habilidade-transcrever-audio/blob/main/SKILL.md
- **Cuidado:** hoje chama OpenAI direto. Roadmap: rotear via `mana-llm-gateway-v2` quando ele cumprir gate

#### 📄 Gera PDF timbrado (identidade visual Maná)?

**SIM → USE a habilidade `mana-habilidade-gerar-pdf-timbrado` v0.3.0**

- Instalação: `pip install "git+https://github.com/Sementesmana/mana-habilidade-gerar-pdf-timbrado.git@v0.3.0"`
- **Baixar SKILL.md:** https://github.com/Sementesmana/mana-habilidade-gerar-pdf-timbrado/blob/main/SKILL.md

#### 🛡️ Manda dados de cliente (CPF/CNPJ/nomes) pra LLM?

**SIM → USE a habilidade `mana-habilidade-pseudonimizar-pii` v0.1.0** (obrigatório pelo ADR de pseudonimização)

- Instalação: `pip install "git+https://github.com/Sementesmana/mana-habilidade-pseudonimizar-pii.git@v0.1.0"`

#### 🌾 Consome pedidos do Simple Agro? (LEITURA)

**Opção preferida — HUB `agente-financeiro-sa`** (fonte única de leitura consolidada, cache 20min):

- Chama HTTP `GET {AGENTE_FINANCEIRO_SA_URL}/api/financeiro?cnpj=X`
- Também tem `/api/dataset` (dados brutos) e `/api/productgroups` (enrichment)
- Credenciais SA ficam no hub, não vazam

#### 🌾 Precisa LER e ESCREVER no Simple Agro (login, orders, clients, wallets)?

**SIM → USE o SDK `mana-simpleagro` v0.1.0** (SDK Camada 2A da Maná Builder, publicado 2026-06-30)

- Instalação: `pip install "git+https://github.com/Sementesmana/mana-simpleagro.git@v0.1.0"`
- Cobre TUDO: login OAuth + auto-relogin, CRUD Orders/Clients/Wallets/Properties, catálogos, pricing com juros, geoloc, ERP classificado
- **14 módulos, 2221 linhas, 116 testes, 82% cobertura**
- Uso mínimo:
  ```python
  from mana_simpleagro import SimpleAgro
  sa = SimpleAgro()   # lê env vars SA_BASE_URL, SA_USERNAME, SA_PASSWORD, SA_SAFRA_ID, SA_GRUPO_ID
  pedidos = sa.orders.list()
  cliente = sa.clients.buscar(cpf_cnpj="123")[0]
  pid, numero = sa.orders.criar_pedido(cabecalho, itens, parcelas)
  ```
- **Baixar SKILL.md canônico:** https://github.com/Sementesmana/mana-simpleagro/blob/main/SKILL.md
- **Env vars:** `SA_BASE_URL`, `SA_USERNAME`, `SA_PASSWORD`, `SA_SAFRA_ID`, `SA_GRUPO_ID`
- ⚠️ Aparece no cockpit `/portfolio` do agente-monitor no card **SDKs** (não Habilidades) — SDK ≠ Habilidade na arquitetura Maná.

#### 🌾 Só quer ENRIQUECER pedidos SA já lidos (obtentora/tecnologia/terceiro)?

**SIM → USE `mana-habilidade-enriquecer-sa` v0.1.0** (utilitário focado, mais leve)

- Instalação: `pip install "git+https://github.com/Sementesmana/mana-habilidade-enriquecer-sa.git@v0.1.0"`

#### 📎 Extrai texto de PDF (OCR + pdfplumber)?

**SIM → USE a habilidade `mana-habilidade-extrair-pdf` v0.1.0**

- Instalação: `pip install "git+https://github.com/Sementesmana/mana-habilidade-extrair-pdf.git@v0.1.0"`

### 3️⃣ Vai precisar de FONTES de dados externas?

Perguntar cada uma. **Todas essas são REFERÊNCIAS/wrappers** — você (Cowork) lê a skill correspondente pra entender a API e COMPÕE código específico do caso do dev.

| Fonte | Como acessar | Skill/hub (referência) | O que compor |
|---|---|---|---|
| **SoftExpert Workflow** (escrever/instanciar/executar) | SOAP `wf_ws.php` | skill `softexpert-wf-ws` (23 métodos SOAP) | Chamada específica pro processo/formulário do dev |
| **SoftExpert Leitura** (workflows, formulários, histórico) | REST `dataset-integration` | habilidade `se-dataset-reader` + skill `softexpert-dataset-integration` (como montar Conjunto no SE) | Cria Conjunto próprio no SE + chama reader.ler("SEU_CONJUNTO") |
| **Simple Agro** (pedidos, clientes) | REST — preferir hub `agente-financeiro-sa` | skill `agente-financeiro-sa` | Chama endpoints do hub (fonte canônica) |
| **Simple Agro escrita** (lançar pedido, cadastrar cliente) | REST direto SA | notas em `ManaVault/03-Sistemas/Simple-Agro/api/` | Cliente REST próprio (não tem wrapper canônico) |
| **Protheus** (leitura) | REST via `agente-protheus` (gateway do SE dataset) | skill `agente-protheus` | Chama endpoints do gateway |
| **banco-mana** (Postgres compartilhado) | Env var `BANCO_MANA_URL` — cada agente tem SCHEMA próprio | consultar `ManaVault/03-Sistemas/banco-mana.md` | Cria schema `agente_<nome>` + tabelas próprias |

**Regra:** o dev NUNCA duplica o wrapper. Se ele precisa de algo que não existe no wrapper, ele contribui de volta (PR) ou pede pro Xayer estender a habilidade. Isso mantém 1 fonte de verdade.

### 4️⃣ Já sabe todas as respostas? Monte o CHECKLIST FINAL

Sintetize o que o dev precisa fazer, na ORDEM:

```
✅ SCAFFOLD
1. Abra Cowork → invoque skill `novo-agente-mana` (agente/app) ou clone `Sementesmana/template-habilidade-mana` (habilidade)
2. Renomeie placeholders, ajuste README/manifest

✅ CÓDIGO
3. Instale as habilidades identificadas na etapa 2 (pip install de cada)
4. Configure env vars locais (.env) pras URLs dos hubs + chaves virtuais
5. Implemente sua lógica de negócio
6. Testes pytest (mínimo 70% cobertura pra habilidade; smoke pra agente)

✅ PUBLICAR NO GITHUB
7. git init + commit + criar repo Sementesmana/<nome> (privado no browser, ou via gh CLI)
8. git push + git tag v0.1.0 (se habilidade) + git push --tags

✅ DEPLOY NO RAILWAY
9. Railway → + New Project → Deploy from GitHub Repo → escolhe seu repo
10. Configure env vars no painel Variables (todas as vars que você usou local)
11. Aguarde build + ver