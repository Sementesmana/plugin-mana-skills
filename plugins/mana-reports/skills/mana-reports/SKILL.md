---
name: mana-reports
description: "Mapa do mana-reports (Sementes Maná): PWA de reports da diretoria, Flask+Railway, que NÃO calcula report — lê o contrato /api/reports e /api/report/<id> dos apps Maná com X-Report-Key server-side e desenha o envelope; MAIA (texto/voz, negociação do Maná Price via MANÁPRIC), Compartilhar PNG/PDF declarado, vigia do comitê no WhatsApp, acesso por código de 6 dígitos, embed no SoftExpert. Decisões, armadilhas, contratos e pendências. Use SEMPRE no mana-reports ou ao citar Reports Maná, app da diretoria, contrato de report, envelope, papel de coluna, bloco grupos, _so, compartilhar.pdf, REPORT_MESTRE, REPORT_APPS, chave-report.sh, MAIA, vigia do comitê, régua e glossário, frescor do dado."
---

# mana-reports — mapa

## O que é
- PWA de reports da diretoria (plataforma N1). Repo `Sementesmana/mana-reports`; dono não declarado no repo. Produção: https://mana-reports-production.up.railway.app (conferida 2026-11-01) (Railway, healthcheck `/health`).
- **Não calcula report**: desenha o envelope que o publicador (quem tem a fonte) entrega. ADRs `2026-09-04-report-como-contrato-e-mana-reports`, `2026-09-04-report-contrato-bloco-grupos`, `2026-09-23-interpretador-do-preco-mora-no-manapric`.
- Por que existe: os reports nasceram calculados no navegador do `/painel-reais`; refazer a conta no celular daria duas contas que divergem na primeira correção. O contrato leva o cálculo para o servidor do publicador.
- Banco-mana, schema `reports`: só acesso, códigos, telemetria de leitura, log de admin e estado do vigia. Nenhum número de report mora aqui.

## Onde está a verdade
- `REGISTRO-DE-PUBLICADOR.md` — o contrato inteiro (kpis, linhas, meta, compartilhar, pdf), como um agente entra, o que cada publicador declara e o checklist do que já quebrou. Referência; este mapa não repete.
- `bff.py` — descoberta de publicadores, chave derivada, cache, escrita (`gravar`). Os comentários ⚠️ contam cada cicatriz.
- `app.py` — rotas, sessão (cookie ou Bearer), segurança/embed, canal de servidor, MAIA, `/health` e `/api/status`. `VERSAO` aqui (terceiro número = correção, segundo = funcionalidade); `/health` diz qual está no ar.
- `static/mana-reports.js` — o renderizador genérico (não conhece report pelo nome). `maia.py`, `vigia.py`, `acesso.py`, `admin.py`, `imagem_envelope.py`/`pdf_envelope.py`, `imagem.py`, `zap.py`, `db.py` (DDL idempotente no boot; `admin.py` cria `admin_log`).
- `tests/test_mana_reports.py` — muitas regras daqui estão travadas por teste que LÊ o código (vocabulário proibido no JS, timeout×Procfile, papel de negociar fora do `maia.py`, 16px). Teste vermelho costuma ser doutrina.
- O detalhe de cada report (o que cada cartão soma, o que o Xayer decidiu) está na skill do **publicador**, não aqui.

## Regras e decisões que o código não explica sozinho
- **Se aparecer `if (report === 'x')` no renderizador, o contrato falhou.** Conserto é no publicador. Teste certo de report novo = gerar o envelope real e mandar para o renderizador, não procurar campo no JS.
- **A conta é UMA e é do publicador.** Quando desktop e celular discordam (já houve 79 × 90 × 99 mi), refaz-se a conta no publicador com teste que sabota cada regra — nunca ajuste no renderizador.
- Falha nunca vira vazio: fonte fora → 503 com motivo; cache só serve cópia velha ROTULADA (`_bff.em` = quando foi lida). Todo número mostra a idade (`meta.dado_de`, ISO com fuso).
- Regra de negócio é do servidor: quem é `fila`/`sala`/`decidido` vem em `_so`. Refiltrar no cliente fez painel e alerta darem números diferentes. Subtotal de grupo é declarado, nunca somado.
- **Escrita só declarada** (desde 2026-09-10): formulário (`formulario.campos[]` + `grava_em`), ações (`meta.acoes[]`, o BFF confere o `id` contra o envelope) e negociação. Três validações independentes, nenhuma confia na anterior: o app confere o campo em `formulario.campos[]` (o celular não pode escrever `papel_operacao`, que decide aba do ICP e entra na régua de crédito); o BFF monta o caminho de `grava_em`, nunca do corpo (senão seria proxy aberto com a chave que lê a carteira); o publicador recusa campo fora do escopo (403), e a recusa sobe COM o motivo. `gravar` esquece o cache só dos reports daquele app, nunca o catálogo. Sem senha nova: a mesma `X-Report-Key`, aceita só para campos de entrevista. Vocabulário copiado no JS é segunda declaração que envelhece.
- Imagem e PDF só leem o declarado em `compartilhar` (royalty/germoplasma do Maná Price nunca saem). PDF sem `compartilhar.pdf` = 404 de propósito: o que vai ao vendedor é decisão explícita; a imagem tem fallback (estrutura da tela com o recorte — Xayer: em qualquer report, manda a estrutura da tela).
- **Registro de publicador novo NÃO mexe no mana-reports**: o agente implementa o contrato com o próprio `REPORT_KEY`, entra na lista `AGENTES` do agente-monitor e recebe a chave de `bash chave-report.sh <id>` (HMAC do `REPORT_MESTRE`, mão única). Descoberta em até 15 min. Motivo: em 2026-09-10 uma aspa no JSON `REPORT_APPS` derrubou todos os reports em silêncio.
- Ordem de força: `REPORT_<AGENTE>_URL/_KEY` > `REPORT_APPS` (legado; agente-pedidos ainda entra por ele) > descoberto. Declarar na mão é também o jeito de tirar um agente do ar sem mexer no monitor. MANÁPRIC entra por `MANAPRIC_URL/KEY` (as mesmas credenciais da MAIA; não duplicar em `REPORT_AGENTE_PRECIFICACAO_*`).
- **A chave de contrato nunca sai do servidor**: `REPORT_MESTRE`, as derivadas e o `REPORT_APPS` só são lidos no `bff.py`. `/health` e `/admin` mostram a ORIGEM e se a chave serve, jamais a chave (nem pedaço, nem hash, nem em log). Para depurar 401, use o teste de chave do `/admin` → publicadores.
- O `rid` se repete entre apps (`endossos-revenda` existe no comite-credito e no agente-pedidos): sempre endereçar por `<app>/<rid>`.
- `REPORT_KEY` do publicador é variável própria — nunca reaproveitar `SECRET_KEY` (no comite-credito ela é o sal que pseudonimiza CPF/CNPJ).
- Report `por_usuario` não passa por cache (serviria a negociação de um diretor para outro) e leva `X-Report-Usuario`.
- **MAIA** lê o MESMO envelope da tela (segunda leitura daria direito de discordar da tela); filtro inventado pelo modelo é descartado (`filtros_validos`) porque vira lista vazia que se lê como "não há nada". Modelagem (`regua`/`glossario`) vai uma vez, após o system, para ficar cacheável. Corte de contexto (`MAX_CRITERIOS`, `_pior_dimensao`) levou de ~34 mil para ~14 mil tokens; medido ~US$ 0,036/pergunta em `mana-equilibrio`.
- Prompt caching DESLIGADO de propósito (sem como testar contra o gateway; MAIA muda é pior que custo alto).
- **Maná Price**: com `meta.modo == 'negociacao'` a MAIA não interpreta — repassa `{frase, historico}` para `/interpretar` do publicador e só redesenha se `_maia.aplicou`. Não recriar `SYSTEM_NEGOCIAR`/`negociar` aqui (o bot do grupo usa a mesma regra; correção de prompt vai no `interpretador.py` do MANÁPRIC).
- **Canal de servidor** (`X-Servico-Key`, cadastro `SERVICO_KEYS` nome:chave, fail-closed): PDF (agente-preco-zap), PNG e MAIA (agente-financeiro-gestao, Comitê de Fluxo de Caixa, 2026-10-24). Só atende conversa `g:<id>` (telefone de diretor → 400); envelope sempre do publicador pelo BFF; a porta da MAIA recusa report de negociação (chave de bot só lê) e devolve `dado_de`/`idade_seg` porque no grupo ninguém vê o selo.
- **Vigia do comitê**: gatilho é VAGA de sala, não horário (aviso sem ação ensina a ignorar). Um PNG só com crédito direto + endosso (faixa no fim). Fila = `"fila" in _so`, sem repetir regra. Estado no banco (restart não pode re-disparar); primeira leitura não alerta; ao vagar, primeiro pede ingestão e adia (até `VIGIA_ESPERA_MAX_SEG`), depois alerta. Destinatário é opt-in por pessoa (`alerta_comite`).
- **Acesso**: telefone da lista + código pelo hub, classe `conversacional` (tem alguém esperando). Resposta idêntica dentro/fora da lista. Hash do código, nunca o código. Sessão sem prazo (`SESSAO_DIAS=0`); revogação = `ativo = FALSE`, conferido a cada request. `ADMIN_TELEFONES` resolve o primeiro admin e é porta dos fundos.
- Sem lib de gráfico/npm: peso no 4G da fazenda. Service worker: shell cache-first, `/api/**` sempre rede.
- Chave do gateway própria, alias `mana-reports`, sem `mana-juridico` (não pode custar 25× por engano), teto US$ 20/30d.

## Armadilhas conhecidas (sintoma → causa → o que fazer)
- Celular diz "nenhum report disponível" → JSON do `REPORT_APPS` quebrado, ou entrada com `"key":""` (bloqueia a chave derivada daquele agente → 401) → conferir `/health` (`apps_publicadores`, `apps_origem`, `descoberta`) e `/admin` → publicadores (testa cada chave sem revelá-la).
- Agente não é descoberto → id diferente do monitor (`agente-estoque` ≠ `agente_estoque`), URL fora de `REPORT_DOMINIOS` (padrão `.up.railway.app`, só https), agente offline no monitor, ou falta `REPORT_MESTRE`/`MONITOR_URL`.
- `chave-report.sh` gera chave errada com cara de certa → colar dois comandos juntos fazia o `read` engolir a 2ª linha; o script lê de `/dev/tty` e recusa mestre < 32 chars. Não "simplificar".
- "Atualizei e veio o mesmo número" → cache é POR WORKER do gunicorn → recarga da tela vai com `?t=` (fresco). E "Buscar dados novos" só ingere se o publicador declara `meta.atualizar`; espera silenciosa (10 s, até 10 min) — a versão com banner/loop foi reprovada pelo Xayer.
- Respondi e não mudou → `gravar` esquece o cache só daquele app; se mexer, manter.
- Cartão com buraco, sem erro → ícone fora do sprite (`tag` não existe; foi a 1.8.2).
- Hora errada na tela ("16:33… agora é 13:34") → `dado_de` sem fuso vira UTC; servidor formata em Brasília (`pdf_envelope.hoje()`), nunca `datetime.now()` cru.
- Acentos viram "?" na imagem/PDF → container sem DejaVu → fontes em `static/fontes`; `/health.imagem_com_acento` avisa.
- Alerta do vigia chega só texto → hub recebe PNG em base64 no JSON (`imagem`, `caption`, `extension`), não multipart (multipart é aceito e a imagem some).
- Sessão "some" dentro do SoftExpert → cookie de terceiro bloqueado pelo Chrome mesmo com `SameSite=None` → a página embutida manda `Authorization: Bearer`; cookie e token se recompõem. `/admin?k=<ADMIN_EMBED_KEY>` entra sem código na aba do SE (Origin/Referer não servem de prova).
- MAIA não abre o microfone → `Permissions-Policy` precisa `microphone=(self)`.
- `/interpretar` cortado → `TIMEOUT_INTERPRETAR` (50) tem de caber no `--timeout 60` do gunicorn (teste lê Procfile e railway.toml).
- PWA preso em versão velha → mandar abrir `/limpar` (desregistra SW e caches sem apagar a sessão). O carimbo do cache é hash dos arquivos + `VERSAO`.
- Botão de ação perigosa trava a MAIA → nada de `confirm()` nativo; dois toques em 4 s.
- Zoom no iPhone ao responder → controle abaixo de 16px. Etiqueta longa sai cortada ("SEM PRE…"). Tema escuro: caixas usam `--azul-caixa`/`--crit-caixa`. Variável CSS inventada é pega por teste.
- Trocar `SESSAO_SECRET` derruba todas as sessões e invalida códigos pendentes.
- Sem hub configurado o código não sai, mas a tela diz "se estiver na lista, o código chegou" de propósito; o resultado real fica em `/admin` (`envio_resultado`).
- Alerta com número cru ("13000000.00") → defeito do publicador: semântica no texto, números em `valores[]`.
- `/key/list` do gateway pagina (10 é página) e o monitor só mostra chave COM alias.

## Contratos com sistemas externos
- **Publicadores** (agente-pedidos, agente-comite-credito, agente-estoque, agente-precificacao/MANÁPRIC): `GET /api/reports`, `GET /api/report/<id>`, `POST …/atualizar`, `POST` em `grava_em`/`<id>/<acao>`/`interpretar`, sempre com `X-Report-Key`. Resposta 404 na sonda = "não publico", não erro.
- **agente-monitor**: fonte das URLs (`/api/status` → `agentes`); consome nosso `/api/status` (degradado sem banco, sem segredo ou sem publicador).
- **Hub agente-whatsapp** (porta única, ADR 2026-06-13): `/send-whatsapp`, `/send-image` com `X-API-Key`, `classe` + `idempotency_key` por requisição + `agente=mana-reports`. Z-API direto proibido.
- **mana-llm-gateway**: `LLM_GATEWAY_URL` raiz (o código acrescenta `/v1/chat/completions`), modelo `MAIA_MODELO` (padrão `mana-equilibrio`). A negociação gasta na chave do agente-precificacao, não na nossa.
- **OpenAI direto** para voz: Whisper (ouvir, no servidor porque o reconhecimento do navegador difere entre iPhone e Android) e TTS `tts-1` (voz `nova`).
- **SoftExpert**: só embed (iframe); `EMBED_ORIGENS` padrão com os dois domínios do SE; vazio = iframe proibido. Nada é escrito no SE.

## Como testar e subir
- `pip install -r requirements.txt -r requirements-dev.txt` e `python -m pytest tests/ -q`; suíte verde antes de push.
- Defeito daqui muitas vezes não dá erro (linha que se contradiz, ícone buraco, filtro que não filtra): gerar envelope real, servir com publicador de mentira (`servir.py` + `dados.json`; mudou o JSON, reinicie), Playwright 390×844, `device_scale_factor=2`, dois temas, e OLHAR. Para regra nova, um guarda de sabotagem que fique vermelho antes do código certo.
- Deploy = `git push` (Railway, Nixpacks, gunicorn 2 workers × 4 threads). Depois: `/health` (versão, `apps_origem`, `descoberta`, `imagem_com_acento`, `maia`) e `/api/status`.
- Subir `VERSAO` a cada entrega que muda o que o diretor vê.

## Pendências e desalinhamentos
- **Vigia em 2 workers**: `VIGIA_ESTE_WORKER` vale `1` por padrão e a env é a mesma para os dois workers do Procfile → os dois rodam a ronda (o estado no banco reduz, mas não elimina, alerta duplicado). A skill antiga dizia que a variável restringe a um worker; não restringe. Resolver com advisory lock ou worker dedicado.
- Migrar agente-pedidos do `REPORT_APPS` para chave derivada e então apagar o JSON. O diagnóstico de `/admin` ainda fala só em `REPORT_APPS`.
- F2: `/painel-reais` consumir o contrato e a cópia JS morrer (1º passo: `reports.exposicao_painel` no publicador). F3: habilidade `mana-habilidade-report-contract` na Maná Builder. Sala "carregamento" fora do comitê por enquanto.
- Prompt caching na MAIA quando der para testar no gateway.
- Docstrings defasadas (não confiar): `app.py` diz "nenhuma escrita"; `bff.py` diz registro só por `REPORT_APPS`; `requirements-dev.txt` diz que Pillow não é usado em produção (é); `REGISTRO-DE-PUBLICADOR.md` cita `/negociar` (hoje `/interpretar`). `.env.example` lista só o básico (faltam `REPORT_MESTRE`, `MONITOR_URL`, `MANAPRIC_*`, `SERVICO_KEYS`, `LLM_GATEWAY_*`, `OPENAI_API_KEY`, `ADMIN_EMBED_KEY`, `VIGIA_*`). CLAUDE.md diz cadastro por SQL; hoje é pelo `/admin`.

## Para ir além
- `CLAUDE.md` do repo; `README.md` (por que existe, acesso, service worker, fases); `REGISTRO-DE-PUBLICADOR.md`.
- Nota do vault `ManaVault/06-Agentes-e-Skills/mana-reports.md`; ADRs em `ManaVault/08-Decisoes/` (os três acima + 2026-06-13 porta única).
- Skills dos publicadores (agente-pedidos, agente-comite-credito, agente-estoque, agente-precificacao) para o significado de cada número.
