---
name: agente-financeiro-gestao
description: "Mapa do agente-financeiro-gestao (Sementes Maná), Flask+PG (schema financeiro)+Railway: painel Gerencial Financeiro portado (front GERADO por ferramentas/portar_painel.py), contas a pagar/receber, fluxo de caixa, aging, carga vigente, anotações, poller do Protheus e do Simple Agro, Report do Caixa para o mana-reports e a MAIA no grupo de WhatsApp. Traz o que o código não diz: decisões, armadilhas, contratos e pendências. Use SEMPRE no agente-financeiro-gestao ou ao citar Gerencial Financeiro, planilha da Clélia, títulos em aberto, baixas, aging, saldo Itaú/ABC, bankItau, ruptura de caixa, /painel-embed, Report do Caixa, Comitê de Fluxo de Caixa, Maia, Rastreio de Parceiro, Cessão de Crédito."
---

# agente-financeiro-gestao — mapa

## O que é
- Gestão financeira diária: substitui o `Gerencial_Financeiro.html` da equipe (arquivo único, dados no `localStorage` de cada máquina, nada auditável) por serviço com banco. Em produção desde 2026-08-07.
- Repo `Sementesmana/agente-financeiro-gestao` (privado). Railway por git push (Procfile; não há `railway.json` no repo). Produção: https://agente-financeiro-gestor-production.up.railway.app (atenção: "gestor", não "gestao"; conferida em 2026-11-01, é a URL do catálogo do agente-monitor). Healthcheck `/api/status` (`SELECT 1` no banco, 503 se cair). Não existe `/health` (404).
- Banco-mana, schema `financeiro` (nunca `public`: em 2026-05-24 um ORM apagou o public e derrubou vários agentes).
- Porta de entrada oficial: aba no SoftExpert (widget "Página WEB" → `/painel-embed`); o link direto não é distribuído.
- Dono: não declarado no repo. A skill previa repasse à Lorena (POP `09-Runbooks/pop-passagem-bastao-dono-agente.md`).

## Onde está a verdade
- `legado/Gerencial_Financeiro_EmBranco.html` (painel da equipe, sem dados) + `ferramentas/portar_painel.py` (TODA mudança nossa) → `static/index.html` GERADO. Nunca editar o gerado à mão.
- `app/poller_protheus.py` — docstring do topo = as decisões das fontes (fato × estado × acervo). `app/cargas.py` — `gravar_carga`, o único caminho de gravação (planilha e poller).
- `app/parsers/campos.py` — tradução nome curto ↔ coluna + `bruto`. `app/blueprints/anotacoes.py` — `TIPOS` (prefixo → tipo) e `SO_LOCAL`.
- `app/reports_contrato.py` (envelope do mana-reports, `periodos()`) · `app/blueprints/report.py` · `app/fluxo_zap.py` (bot do grupo; o docstring do topo diz que o resumo vem do mana-reports — DEFASADO, hoje é `resumo_png.py`) · `resumo_png.py`, `calendario_png.py`, `dia_png.py` (as imagens).
- `app/auth.py` — ver regra de acesso abaixo (a docstring do topo descreve perfis que hoje não são aplicados).
- `tests/` — muitos testes LEEM o painel gerado ou o legado (ids duplicados, prefixos, `fxLote`, carregamento do script). Vermelho ali costuma ser regra, não bug do teste.

## Regras e decisões que o código não explica sozinho

### Front gerado
- Porte = só trocar de onde vêm e para onde vão os dados: ponte `window.MANA` (shim do `localStorage` que lê cache no boot e grava na API em lote), `DATA` preenchido pelos endpoints, setters que transformam importação em `POST /api/cargas` (`CARGA_DE`), mais as abas nossas (Gráfico Fluxo, Report do Caixa, Rastreio de Parceiro, ajustes da Agenda).
- A equipe do financeiro evolui o `.html` por fora (com o próprio `build_gerencial.py`). Reconciliar: o legado DELES é a base, o nosso se reaplica por cima. Comparar funções nome a nome, rodar o gerador (as âncoras abortam onde o legado mudou) e NÃO reaplicar o que o legado já faz (em 21/09 saíram logo na sidebar, filtro do `renderBaixas`, relatório por período e máscara).
- Mudou o texto do cabeçalho do canvas de fechamento → muda a âncora no gerador, senão "não achei o texto do canvas de fechamento".
- Prefixo de id por aba nova: `rcx` (Report), `rtp` (Rastreio), `fxPj` (busca na projeção). `rp` é do legado (Recebimentos Projetados).

### Dados e cargas
- **Carga vigente**: leitura usa sempre a última carga OK de cada tipo. Reimportar não duplica, apagar uma carga volta a anterior. É isso que permite janela móvel sem dedup.
- **O nome curto é o contrato**: o que se grava é `n`, `tot`, `v`… (o painel lê o `bruto`). Gravar o nome do gateway deixa o SQL certo e a TELA VAZIA. O campo `s` dos títulos compara literal `'Vencido'`, `'Não'` (com acento) e `'0'` (realizado do mês) — não normalizar.
- `n` = razão social (no receber o nome do cadastro é a fazenda truncada); `v` = vencimento ORIGINAL, não o prorrogado.
- Baixas: **corte em D−1** (dia fechado; decisão do Xayer 25/08) e **janela móvel de 90 dias, não incremental** (o Protheus muda o passado, sem CDC). Botão manual manda `ate=hoje` e o rótulo vira "tempo real" (pedido da Lorena, 24/09) — só no botão, nunca no cron.
- Títulos = ACERVO inteiro (aberto e baixado, desde 2001), sem recorte: o realizado por mês usa os baixados. Cortar para "só em aberto" mata essa tela.
- Pedidos de compra = ESTADO: recorte do ano + `INCLUIR_ENCERRADOS=S` (a tela mostra encerrados com saldo zero; não infla o caixa). O agrupamento item→pedido replica as regras do importador do painel: conferir contra a TELA, não contra o arquivo.
- Pedidos de venda vêm do **Simple Agro** via `/api/dataset` do agente-financeiro-sa, não do Protheus. Grão = PARCELA; parcela paga entra com `pago` (sem isso ~R$ 11 mi já recebidos virariam entrada futura). Só Aprovado/Integrado; tipos bonificação/difusão/doação/exceção/indenização ficam fora (Lorena, 29/09). `cod` = 8 primeiros dígitos do CPF/CNPJ (para CPF não significa nada; reproduzido, não consertado).
- O rótulo do sistema (`protheus`/`simple-agro`) vai no `arquivo_nome` da carga e o `manaFonte` do painel lê por regex: são contrato. Rótulo errado manda conferir no sistema errado.
- Planilha não morre: baixas por planilha vencem a tela quando mais recentes ("vence quem carregou por último", `manaBaixas`). Nunca limpar o `localStorage` das baixas: é a única casa delas.
- Saldo em banco: fonte 1 = anotação `banco_manual` (`bankItau`/`bankABC`, gravada pelo PDF do extrato); fallback = carga `extrato`.
- Anotação só sobe se o prefixo da chave estiver em `TIPOS`; senão vira `console.warn` que ninguém lê. `SO_LOCAL` é estado da máquina (versão de semeadura, flags, token, rascunho da cessão): sincronizar faria uma máquina sobrescrever a outra.
- CNPJ completo do cliente (Duplicata/Cessão de Crédito) é consulta pontual ao vivo no gateway (dataset `cliente`), não carga; falha = `null`, nunca erro. Fornecedor fica de fora (não há dataset equivalente).

### Fluxo de caixa (tela)
- Gráfico: passado vem das BAIXAS (por data de baixa), de hoje em diante dos TÍTULOS EM ABERTO; vencido em barra separada FORA do acumulado; escala comprimida (log simétrica) com valor real no tooltip. Saldo de abertura fora de hoje é reconstruído a partir do extrato e é aproximado por construção (o rodapé diz).
- `fxVal` (cheio) × `fxValEf` (com % e "fora"): lista e card de vencidos usam a MESMA regra (`fxVal`, inclui o "fora"), o calendário usa `fxValEf`. Misturar faz o subtotal divergir dentro da mesma figura.
- `fxLote()` é o ÚNICO aplicador de marca em lote (Vencidos, busca na projeção e Rastreio). Age só no que está VISÍVEL, seleção por bloco, sempre com confirmação. "Devolver" tem dois sentidos (à projeção × à data original) = dois botões; 100% não vira anotação; mover sem data não faz nada.
- Busca na projeção ignora o filtro 30/90/180 de propósito e não inclui vencido.
- Rastreio de Parceiro: pareia por NOME (receber e pagar têm numerações de código independentes). "Fora" já é encontro de contas feito: não entra no compensável (= MIN dos totais, sobre `fxVal`). Não tem marca própria: grava em `fxfora_`/`fxdata_`/`fxpct_`.
- Agenda/fechamento: o a pagar é quinta→quarta, o a receber vai da quinta anterior até a quinta. Decisão do Xayer: não alinhar (mudaria o painel inteiro), só declarar. Data de vencimento só no drill-down (a linha do resumo soma várias datas). A imagem do gestor sai mascarada (LGPD: nome 8 caracteres, natureza 2 palavras) e sem data.

### Report do Caixa e a MAIA
- **A conta é da TELA**: a aba calcula no navegador (onde moram os tratamentos do gestor) e publica o número pronto. `reports_contrato.py` não pode conhecer `Titulo`/`select(`/`db.session` (teste trava): ler o banco direto mostraria um fluxo que não existe (caso 79 × 90 × 99 mi do Comitê de Crédito).
- Sem publicação → 503, nunca envelope de zeros ("R$ 0,00, sem quebra" seria afirmação falsa). Acima de 36 h o envelope se declara degradado.
- Bot do grupo: só responde quando chamam **Maia** pelo nome; sem o nome, silêncio total (nem erro). Imagem só quando a frase É a palavra-chave (fluxo de caixa, recebimento, pagamento); o resto vai à MAIA. Este bot não entende nem calcula (teste trava): quem entende é a MAIA do mana-reports.
- Listas sempre POR CLIENTE, nunca por título (título a título → texto mandando ao SoftExpert/painel; checado antes do dia). Sem lado declarado vão os dois. Mês inteiro vira imagem por parceiro; ano é recusado sem citar contagem.
- O resumo NÃO fala de vencido (Xayer desfez em 26/10): vencido é report próprio (`Maia vencidos`).
- Corte de relevância é PISO e só vale com pista na frase (acima, a partir, relevantes…); número nu < R$ 10 mil não é dinheiro. Subtotal continua cheio, o que saiu é declarado e o corte vai na legenda.
- Layout de report é de quem publica: a imagem genérica do mana-reports foi recusada ("tripa de gigante"); largura de coluna medida e altura calculada, nunca fixas.
- Nome de cliente/fornecedor vai ao modelo (decisão do Xayer, 24/10); CPF/CNPJ não (teste trava).

## Regra de acesso — ATENÇÃO
- Desde 2026-09-22 (pedido da Lorena) `require_auth` está DESATIVADO: qualquer um com a URL é `admin`, lê e escreve. Perfis consulta/carga/admin e o token do embed existem mas não barram nada, e o autor das anotações vira "Acesso público". Restaurar exige decisão do Xayer (o histórico do git tem a versão anterior).
- Não adicionar `X-Frame-Options` nem `frame-ancestors`: o validador do widget do SE recusa QUALQUER restrição de frame (comprovado 2026-08-03).
- Dado real nunca entra no repo (`.gitignore`); a bancada do painel antigo vive fora, em `ORQUESTRADOR/_bancada-financeiro/`. Nada disso vai a LLM.

## Armadilhas conhecidas (sintoma → causa → o que fazer)
- Painel abre na tela de login / em branco → erro de execução no script gerado (ex.: atribuição antes do `var`, função `mana*` comida pelo porte) → `node --check` não pega; rodar `tests/test_painel_carrega.py`, que EXECUTA o script.
- Aba nova em branco sem erro no console → id duplicado (`getElementById` pega o escondido) → prefixo próprio; o teste de ids trava.
- Testes do painel passam "verdes" sem node → os que dependem de node dão skip → ter `node` na máquina antes de confiar na suíte.
- Gerador aborta com "<div> não fecha" → trava de balanço (conta div dentro de string JS também; o legado já acusa saldo −1, compara antes × depois).
- Coluna nova não aparece no banco → `create_all` não altera tabela → `migracao.alinhar_colunas()` faz só `ADD COLUMN IF NOT EXISTS` no boot.
- Deploy "sobe" mas o comportamento é o antigo → `JWT_SECRET`/banco ausente derruba o boot e o Railway mantém o deploy anterior ACTIVE → o log aberto é do velho.
- Carga de pedidos de venda menor que o relatório do SA → descarte silencioso (saíram da aprovação) → ler a nota de `conferir_pedidos_venda`; o `/api/dataset` tem cache de 20 min (`idade_origem_seg`).
- Número não bate com a planilha → não investigar do zero: runbook `ManaVault/09-Runbooks/protheus-x-excel-por-que-divergem.md` (tempo, fórmula do Excel, situação congelada, descarte; "devolva o descartado e veja se a soma fecha").
- 502 no botão Atualizar → timeout da cadeia: gunicorn 600s > `PROTHEUS_TIMEOUT` 300s > gateway 300s > query 120s. Manter essa ordem.
- Imagem/calendário não sai no grupo → thread sem app context ou report sem publicação → `_carregador` com `app_context`; republicar a aba (Ctrl+F5). Resposta duplicada → reentrega da Z-API: dedup por `messageId` (em memória, 15 min).
- Anotação some entre máquinas → prefixo fora de `TIPOS` ou baixa importada por planilha (só `localStorage`).

## Contratos com sistemas externos
- **agente-protheus** (gateway): `/query/<dataset>` com `X-API-Key` própria (prefixo `financeiro:` no `API_KEYS` do gateway). 404 = gateway sem o dataset nesta versão.
- **agente-financeiro-sa** (Simple Agro): `/api/dataset`, sem chave hoje (devolve nome e CPF/CNPJ — fechar é decisão do dono de lá). Ninguém abre sessão no SA daqui (452). `SA_SAFRA_ID` trava a safra: trocar na virada.
- **mana-reports**: lê `GET /api/reports` e `/api/report/<rid>` com `X-Report-Key` (fail-closed: sem `REPORT_KEY` → 503). `REPORT_KEY` é variável PRÓPRIA (gerar com `chave-report.sh` no mana-reports), nunca `JWT_SECRET`. A MAIA responde por `POST /api/servico/maia/<app>/<rid>` com a chave de SERVIÇO (`MANA_REPORTS_KEY`, ≠ `REPORT_KEY`); teto de linhas no contexto da MAIA mora lá. Descoberta automática: o agente está na lista do agente-monitor.
- **agente-router → `/api/zap/webhook`**: raw Z-API, áudio já transcrito; Bearer `ROUTER_SHARED_SECRET` (fail-closed); responde 200 na hora e processa em thread (o router espera 8 s).
- **hub agente-whatsapp**: texto por `/send-whatsapp` com `classe=conversacional` + `idempotency_key` do messageId + `agente`. Imagens por `/send-image`.
- **SoftExpert**: só embute o painel (widget Página WEB); nada é escrito no SE.

## Como testar e subir
- `python -m pytest tests -q` (SQLite em memória, não toca produção) + `node ferramentas/testar_ponte.mjs`, antes de QUALQUER push. Mexeu no painel: rodar o gerador antes dos testes.
- Boot (Procfile): `flask init-schema` (recusa public + alinha colunas) → `flask bootstrap-admin` (só com banco vazio) → gunicorn 1 worker gthread.
- Cron = `flask puxar-protheus` (sai ≠ 0 se QUALQUER tipo falhar). O agendamento não está no repo (fica no Railway). Botão e cron chamam o mesmo `puxar_todas`; o botão devolve 200 com `erros[]` se algum tipo falhar e 502 só se todos falharem.
- Checar `/api/status` e `/api/zap/health` após deploy.

## Pendências
- **Bug no CLI do cron**: `puxar-protheus` imprime `r['periodo']`, chave que o resumo por tipo não tem (só o geral) → `KeyError` depois de gravar; o job sai vermelho mesmo com sucesso. Corrigir com teste.
- Login/perfis desativados (ver Regra de acesso) — decidir se volta.
- `/send-image` vai sem `classe`/`idempotency_key` (o texto vai com): conferir contra a regra da porta única.
- Validar a regra das baixas num SEGUNDO mês (tela filtrada × relatório extraído no mesmo intervalo de minutos) antes de aposentar a planilha.
- Baixas por planilha não estão no `CARGA_DE` (por máquina): virar carga como os outros tipos.
- `MOTL` do painel sem `DAC`/`CRE` (entram no total, sem opção no filtro de motivo do pagar).
- Rastreio: parear pela raiz do CNPJ quando a carga trouxer CNPJ.
- Apagar `ADMIN_INICIAL_*` do Railway; `.env.example` não lista as variáveis do poller, zap e reports.
- Dono do agente a redefinir (repasse previsto à Lorena).
- O espelho da skill no marketplace está defasado (descreve uma versão antiga do agente): substituir por este mapa.

## Para ir além
- Não há `CLAUDE.md` no repo. Nota do vault `ManaVault/06-Agentes-e-Skills/agente-financeiro-gestao.md`.
- ADR `ManaVault/08-Decisoes/2026-08-26-baixas-do-protheus-por-carga-janela-movel-e-d-menos-1.md`; ADR 2026-06-13 (porta única WhatsApp); runbook protheus-x-excel.
- Lições na `mana-memoria-operacional`: `create-all-nao-altera-tabela.md`, `carga-grande-insert-em-lote.md`, `se-embed-frame-validador.md`.
- O porquê de quase tudo está nas docstrings de `poller_protheus.py`, `fluxo_zap.py`, `report.py` e no topo de cada teste.
