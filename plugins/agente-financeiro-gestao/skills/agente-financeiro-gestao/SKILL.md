---
name: agente-financeiro-gestao
description: >-
  Gestão financeira diária da Sementes Maná — contas a pagar/receber, fluxo de
  caixa, orçamento, projeção, aging e crédito por cliente. Flask + PostgreSQL
  (schema financeiro no banco-mana) no Railway; front = painel do financeiro
  portado FIEL (168 funções intactas, porte gerado por
  ferramentas/portar_painel.py — NUNCA editar static/index.html à mão).
  Use SEMPRE que trabalhar com o agente-financeiro-gestao: painel Gerencial,
  cargas de planilha (Protheus/pedidos/orçamento/projetado/baixas/extrato),
  carga vigente, tabela anotacao (justificativa/responsável/banco_manual),
  gráfico de fluxo de caixa, escala comprimida, ruptura de caixa,
  /painel-embed no SoftExpert, perfis consulta/carga/admin, migração aditiva,
  poller do Protheus. Também quando mencionar: Gerencial Financeiro, planilha
  da Clélia, títulos em aberto, aging, saldo Itaú/ABC, bankItau, DRE diária,
  23 mil títulos, contas a pagar Maná.
---

# agente-financeiro-gestao — Gestão Financeira Diária

> **EM PRODUÇÃO (2026-08-07).** Substitui o `Gerencial_Financeiro.html` da
> equipe do financeiro (arquivo único, dados no `localStorage` de cada máquina)
> por serviço com banco de verdade. **Porta de entrada oficial: aba no
> SoftExpert** (widget "Página WEB" → `/painel-embed`); o link direto não é
> distribuído.
>
> - **Repo:** `Sementesmana/agente-financeiro-gestao` (privado)
> - **Railway:** `agente-financeiro-gestor-production.up.railway.app`
> - **Banco:** banco-mana, schema `financeiro` (NUNCA public)
> - **Healthcheck:** `/api/status`

## Por que existe

O painel antigo funcionava, mas cada pessoa via a própria versão (localStorage),
nada era auditável e nada alimentava outro sistema. Agora os mesmos números
viram tabela no banco-mana — base para indicador, alerta e artefatos de IA.
Hoje a Clélia sobe planilhas 1×/semana; o destino é o **poller do Protheus**
gravar nas MESMAS tabelas (carga `origem='protheus'`) sem nenhuma tela mudar.

## Regra de ouro nº 1 — o front é GERADO

`static/index.html` (3.500+ linhas) **não se edita à mão**. Ele nasce de:

```
legado/Gerencial_Financeiro_EmBranco.html   (o painel da equipe, intocado)
        + ferramentas/portar_painel.py       (as ~8 mudanças do porte)
        → static/index.html
```

Mudou algo? Edita o GERADOR (ou o legado) e roda
`python ferramentas/portar_painel.py`. O gerador tem trava de balanço de
`<div>` (aborta se comer/sobrar tag — já quebrou a sidebar uma vez) e a ponte
`window.MANA` tem testes próprios: `node ferramentas/testar_ponte.mjs`.

O que o porte injeta: (1) ponte `window.MANA` — espelho do `localStorage` que
lê cache no boot e grava na API em lote com debounce 800ms; (2) `DATA`
preenchido pelos endpoints antes do primeiro `render()`; (3) setters nas
chaves do `DATA` — importar planilha dispara `POST /api/cargas` sozinho, com
aviso na tela ("✓ N linhas salvas" / "✗ NÃO foi salvo: <erro real>");
(4) login (que o embed pula); (5) logo Maná (sidebar, favicon, imagem de
fechamento, assinatura dos e-mails de cobrança); (6) aba Gráfico Fluxo de
Caixa; (7) escala comprimida.

## Conceitos-núcleo

**Carga vigente** — toda linha aponta pra `carga` que a criou; a leitura usa
SEMPRE a última carga OK de cada tipo. Reimportar não duplica; apagar uma
carga volta pra anterior; `GET /api/cargas/vigentes` diz o que vale.
9 tipos: `titulos_pagar/receber`, `baixas_pagar/receber`,
`pedidos_venda/compra`, `orcamento`, `projetado`, `extrato`.

**Tradução + bruto** — o painel manda nomes curtos (`n`, `c`, `v`, `b`,
`sal`…) vindos do parseSheet dele. `app/parsers/campos.py` traduz para as
colunas (SQL enxerga) E guarda o registro original em `bruto` JSONB — a
leitura devolve o `bruto`, então as 168 funções recebem exatamente o que
produziriam. Mapeamento conferido contra os arquivos reais da Clélia.

**Anotações** (`tabela anotacao`, tipo+chave únicos) — o que a equipe escreve
por cima do dado: justificativa, responsável, ajuste de aging, saldo manual
de banco, confirmações, acertos, snapshots de CR, controle de NF. Com autor,
data e histórico das versões (sobrescrever guarda o anterior; regravar igual
não polui). 14 tipos mapeados por prefixo de chave do painel
(`just_v_`, `resp_v_`, `bank`, `ped_ok_`/`ped_confirmado_`, `cr_obs_`/
`cr_lobs_`, `nfctrl_`…) — prefixo novo no painel EXIGE entrada em
`TIPOS` (app/blueprints/anotacoes.py) senão a anotação não sobe.
Conferidor: `ferramentas/conferir_manuais.py <export.json>`.

**Saldo em banco** — fonte 1: anotações `banco_manual` (`bankItau`/`bankABC`,
string JSON `{"val":...,"data":...}` — é o que o PDF do extrato grava e o que
a tela mostra); fonte 2 (fallback): carga `extrato` → tabela `saldo_conta`
(por onde o poller entra). `_saldo_em_banco_detalhado()` devolve origem e
contas — o cartão do gráfico mostra "Itau X · ABC Y · extrato de dd/mm".

**Perfis** — `consulta` (aba do SE, só lê; escrita = 403 no `require_auth`),
`carga` (Clélia), `admin`. `/painel-embed` injeta token de consulta
(`EMBED_TOKEN`) quando `SE_EMBED_ORIGIN` está definido. ⚠️ **Não adicionar
X-Frame-Options nem frame-ancestors** — o validador do widget do SE recusa
QUALQUER restrição de frame (memória viva: `se-embed-frame-validador.md`).

**Gráfico de fluxo de caixa** — `GET /api/fluxo-caixa/grafico?granularidade=
dia|semana|mes&meses=N`. Agrega no banco (23 mil títulos → ~50 pontos),
devolve ruptura (1º período negativo), pior ponto, vencidos em barra
separada FORA do acumulado, e `banco` (origem do saldo). Front: barras
receber/pagar + linha acumulada, **escala comprimida** (log simétrica —
R$ 435 mil e R$ 151 mi no mesmo eixo; botão Linear ao lado; tooltip/tabela
sempre com valor real).

## Boot (roda em todo deploy — Procfile e railway.json)

```
flask init-schema      → cria schema+tabelas (recusa public) + ALINHA COLUNAS
flask bootstrap-admin  → 1º admin por env ADMIN_INICIAL_* (SÓ com banco vazio)
gunicorn wsgi:app --workers=1 --worker-class gthread --threads=8 --timeout=180
```

`app/migracao.py alinhar_colunas()`: create_all NÃO adiciona coluna em tabela
existente — a migração aditiva compara model×banco e faz só
`ADD COLUMN IF NOT EXISTS` (nunca DROP/ALTER TYPE). Log do deploy mostra
`+ coluna titulo.parceiro_alt (TEXT)`.

## Cargas grandes

Insert em **lotes de 1000** (`insert(model)` executemany); lote que falha é
reprocessado linha a linha pra isolar a culpada. Linha ruim não derruba a
carga (vira `linhas_ignoradas` + amostra em `erros`). Dedup de arquivo por
md5 (409; `forcar=1` passa).

## Endpoints principais

`POST /api/auth/login` · `GET/POST/PUT /api/usuarios` (admin) ·
`POST /api/cargas` (multipart OU JSON `{tipo, registros}`) ·
`DELETE /api/cargas/<id>` · `GET /api/cargas/vigentes` ·
`GET /api/titulos[?natureza=&aberto=1&q=]` · `/api/titulos/resumo` ·
`/api/titulos/por-categoria` · `/api/fluxo-caixa` ·
`/api/fluxo-caixa/grafico` · `/api/baixas` `/api/pedidos` `/api/orcamento`
`/api/projecao` `/api/saldos` · `GET/PUT/DELETE /api/anotacoes[...]` ·
`GET /api/anotacoes/tipos` · `GET /painel-embed` · `GET /api/status`.

## Env vars (Railway)

`BANCO_MANA_URL` (ou DATABASE_URL) · `DB_SCHEMA=financeiro` · `JWT_SECRET`
(fail-fast: sem ele o boot cai — e o Railway MANTÉM o deploy antigo ACTIVE,
o log que você abre é do velho!) · `SE_EMBED_ORIGIN` (vazio = embed off) ·
`EMBED_TOKEN_HORAS` · `MAX_UPLOAD_MB=40` · `ADMIN_INICIAL_USUARIO/SENHA/NOME`
(apagar depois do 1º boot) · `DB_POOL_SIZE/DB_MAX_OVERFLOW`.

## Testes — 82, rodar antes de QUALQUER push

```bash
python -m pytest tests -q          # 82 testes (SQLite memória, não toca prod)
node ferramentas/testar_ponte.mjs  # 25 testes da ponte window.MANA
```

Cobrem: permissões por perfil, carga vigente/reimportação, tradução
ida-e-volta campo a campo, anotações (autor/histórico/lote), saldo em banco
(as 2 fontes, precedência), gráfico (ruptura/vencido/granularidade),
bootstrap-admin (trava de 2º admin), embed.

## Dados sensíveis

O repo NUNCA recebe dado real (`.gitignore` bloqueia xlsx/csv/pdf, `GF/`,
`manuais_gerencial*.json`). A bancada do painel antigo (com 23 mil títulos
embutidos em HTML) vive FORA do repo em `ORQUESTRADOR/_bancada-financeiro/`.
Arquivos de exemplo da Clélia em `ORQUESTRADOR/agente-financeiro-gestao/GF/`
(ignorado). Nada disso entra em chamada LLM.

## Pendências / roadmap

1. Clélia operando as cargas semanais (usuária perfil `carga` criada pela aba
   Usuários).
2. **Poller do Protheus** (fase 2 do plano Protheus): lê SE1/SE2 via
   agente-protheus e grava carga `origem='protheus'` diária — planilha morre.
3. Apagar `ADMIN_INICIAL_*` do Railway após confirmar o admin.
4. Handoff planejado: **Lorena** (repasse via POP
   `09-Runbooks/pop-passagem-bastao-dono-agente.md`, caminho veterano).

## Lições que este agente gerou (memória viva)

`create-all-nao-altera-tabela.md` · `carga-grande-insert-em-lote.md` ·
`se-embed-frame-validador.md` — na skill `mana-memoria-operacional`.
