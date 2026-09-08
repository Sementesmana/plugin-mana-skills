---
name: mana-reports
description: App de reports da diretoria da Sementes Maná (PWA instalável) — Flask no Railway que NÃO calcula report: lê o contrato GET /api/reports + GET /api/report/<id> dos apps Maná com a chave em header (server-side) e desenha o envelope (meta/kpis/series/colunas/grupos/linhas/filtros/regua/glossario). Renderizador genérico: report novo aparece na home sem uma linha de código nova. Traz a MAIA (pergunta em texto ou voz sobre o report aberto, com a modelagem da nota no contexto), o vigia do comitê (alerta com PNG no WhatsApp quando abre vaga na sala), admin de quem acessa, e embed no SoftExpert. Acesso por telefone da lista + código de 6 dígitos pela porta única do WhatsApp, sessão em cookie assinado; banco-mana schema reports (acessos, codigos, leituras). Use SEMPRE no mana-reports — renderizador do envelope, bloco grupos, papel de coluna, BFF e cache, MAIA e custo de token, vigia e alerta do comitê, acesso por WhatsApp, service worker, telemetria de leitura. Também quando mencionar: Reports Maná, app da diretoria, PWA de reports, REPORT_APPS, X-Report-Key, contrato de report, explicação da nota, régua e glossário, frescor do dado na tela.
---

# mana-reports

PWA de reports da diretoria. Plataforma **N1**. Versão **1.9.1** em produção.
ADRs `2026-09-04-report-como-contrato-e-mana-reports` e
`2026-09-04-report-contrato-bloco-grupos`.

## A regra que organiza tudo

**Este app não calcula report.** Ele desenha o envelope que o publicador entrega. O
renderizador (`static/mana-reports.js`) não conhece nenhum report pelo nome — ele lê
`colunas[].papel` (`titulo`/`subtitulo`/`metrica`/`detalhe`/`grupo`) para decidir o que
sobe ao cartão e o que abre na folha de detalhe.

> Se aparecer um `if (report === 'x')` no renderizador, o contrato falhou. O conserto é
> no contrato do publicador, não aqui.

⭐ **Report de outro app não pede código nenhum.** O Perfil Clientes do comitê entrou
inteiro — régua, classe, completude, detalhe por dimensão — com zero linha nova aqui.
Procurar o nome de um campo no JS do cliente para "ensinar" o PWA é o teste errado; o
teste certo é **gerar o envelope real e mandar para o renderizador**.

## Arquivos

| arquivo | responsabilidade |
|---|---|
| `app.py` | rotas, sessão, cabeçalhos de segurança, telemetria, versão do cache estático |
| `bff.py` | lê os contratos com a chave em header, cache com TTL, **serve cache rotulado** quando a fonte cai |
| `acesso.py` | código de 6 dígitos pelo hub do WhatsApp, hash, sessão assinada |
| `admin.py` | cadastro de quem acessa, teste de envio, diagnóstico, log de ação, leituras |
| `maia.py` | contexto enxuto do report aberto + pergunta/ouvir/falar |
| `vigia.py` | ronda do comitê: lê salas e fila, decide se manda alerta |
| `imagem.py` | PNG do alerta (Pillow) — a fila desenhada para cair no grupo |
| `zap.py` | envio pelo hub (texto e imagem), sempre com `classe` e `idempotency_key` |
| `db.py` | schema `reports` (acessos, codigos, leituras) — DDL idempotente no boot |
| `static/mana-reports.js` | o renderizador do envelope |
| `static/mana-reports.css` | tokens da identidade Maná (verde/ouro, Playfair + DM Sans) |

## Invariantes (não quebre)

1. **Falha nunca vira vazio.** Fonte indisponível é 503 com motivo. Lista vazia só quando
   o publicador disser que está vazia.
2. **Todo número na tela exibe a idade do dado** (`meta.dado_de`). Sem frescor, não desenha.
3. **A chave dos contratos não sai do servidor.** `REPORT_APPS` é lido só no `bff.py`.
4. **Subtotal de grupo é declarado**, nunca somado das linhas (a meta não está nas linhas).
5. **Regra de negócio é do servidor.** Quem pertence a `fila`/`sala`/`decidido` vem em
   `_so`, declarado pelo publicador. Refiltrar no cliente é como painel e alerta passaram
   a dar números diferentes.
6. **Resposta igual** para telefone de dentro e de fora da lista no pedido de código.
7. **WhatsApp só pelo hub**, com `classe`, `idempotency_key` e `agente` (ADR 2026-06-13).

## Registrar um publicador novo

Env `REPORT_APPS` (JSON): `{"agente-x": {"url": "https://…", "key": "<REPORT_KEY dele>"}}`.
Nada além disso — o catálogo e os reports aparecem sozinhos, o BFF agrega todos os apps
registrados (não existe lista para editar no código).

⚠️ **`REPORT_KEY` é variável separada — nunca reaproveite a `SECRET_KEY` do publicador.**
No `agente-comite-credito` ela é o sal do HMAC que pseudonimiza CPF/CNPJ; vazá-la em
header HTTP quebraria os hashes de todas as safras, em silêncio.

⚠️ **Ícone que o sprite não tem NÃO dá erro:** o `<use>` aponta para nada e o cartão sai
com um buraco (foi a 1.8.2). Report novo pede o ícone no sprite.

⚠️ **JSON quebrado no `REPORT_APPS` esvazia o catálogo** sem estourar exceção. Depois de
mexer, confira `/health` → `apps_publicadores`.

## MAIA — o que a tela mostra, ela tem de receber

Pergunta em texto ou voz sobre **o report aberto**. O contexto sai de
`maia.montar_contexto(env)`: KPIs, colunas com papel, linhas enxutas, e a **modelagem** —
`regua` (pesos e cortes) e `glossario` (o que cada dimensão mede, como cada critério
pontua). Sem a modelagem ela sabe a nota e nenhuma das contas, e responde "não tenho isso".

- **O modelo vai UMA vez**, como mensagem própria depois do system. É igual para todos, e
  é isso que o torna cacheável — cache só funciona em prefixo estável.
- `MAX_LINHAS = 160`. `MAX_CRITERIOS = 12` (medido: 12 clientes com detalhe cheio ~9 mil
  tokens de entrada; 25 dariam ~18 mil, mais que a lista inteira em modo compacto).
- Lista grande manda por linha só **onde perdeu mais ponto** (`_pior_dimensao`), não o
  placar por dimensão.

⚠️ **CUSTO:** o placar cheio em 160 linhas custava ~20.700 tokens em **toda** pergunta,
inclusive nas que não eram sobre cliente nenhum. Com o corte: 34.100 → 14.300 (−58%).
Medido em produção: **US$ 0,036 por pergunta** com `mana-equilibrio` (Sonnet).

**Prompt caching não está ligado** de propósito: mandar `cache_control` sem poder testar
contra o gateway arrisca derrubar toda pergunta, e MAIA muda é defeito pior que custo
alto. O prefixo já está isolado para quando der para testar.

## Custo no gateway

Chave virtual própria, alias `mana-reports`, **sem `mana-juridico`** — uma chave que não
alcança Opus não pode custar 25× por engano. Teto de US$ 20/30d como disjuntor.

⚠️ A aba Consumos do `agente-monitor` **não tem lista fixa**: lê `/key/list` e monta uma
linha por `key_alias`. Chave sem alias não aparece; a master é ignorada de propósito.
"Não aparece no monitor" quase sempre é chave sem nome ou sem chave própria.
⚠️ `/key/list` **pagina** — 10 é o tamanho da página, não o total.

## O vigia do comitê

Ronda de `VIGIA_INTERVALO_MIN` em `VIGIA_INTERVALO_MIN` minutos: lê as salas do report do
comitê e, quando abre vaga, manda **um** PNG com a fila para os destinatários.

- **É um relatório só.** Crédito direto e endosso esperam a mesma sala e vão na mesma
  lista, com os endossos numa faixa no fim. Duas imagens obrigariam a somar duas filas na
  cabeça — o trabalho que o alerta veio poupar.
- A fila é `"fila" in l["_so"]` — já sem quem está em sala e sem quem a ata decidiu. O
  vigia **não repete essa regra**.
- `VIGIA_ESTE_WORKER=1` para um worker só rodar a ronda; `VIGIA_ESPERA_MAX_SEG` segura
  alerta com dado velho.

## Embed no SoftExpert

`EMBED_ORIGENS` (já vem com os dois domínios do SE). Com ela: sai o
`X-Frame-Options: DENY` e entra `Content-Security-Policy: frame-ancestors`, o cookie vai
como `SameSite=None` (dentro do iframe o `Lax` não viaja e a sessão "some" sem erro) e as
POSTs de admin passam a conferir a `Origin`. Vazia = iframe proibido.

## Gotchas

- `sw.js` é servido da **raiz**: em `/static/` o service worker não controlaria a home.
- A sessão **não expira** por padrão (`SESSAO_DIAS=0`). Revogação é `ativo = FALSE` em
  `reports.acessos`, conferido a cada request.
- Trocar `SESSAO_SECRET` derruba todas as sessões **e** invalida códigos pendentes (ele
  entra no hash do código).
- Sem `WHATSAPP_HUB_URL`/`KEY` o código não é enviado e o log avisa — a tela continua
  dizendo "se estiver na lista, o código chegou", de propósito.
- Quem formata dinheiro é o cliente. Alerta com número cru no texto
  ("faltam 13000000.00") é defeito do publicador: ele declara a semântica no texto e
  manda os números em `valores[]`.

## Como testar de verdade

Este app tem uma classe de defeito que **não dá erro**: linha que se contradiz, ícone
ausente virando buraco, filtro que não filtra. Teste não pega; olhar pega.

1. Gere o **envelope real** do publicador e sirva com um publicador de mentira.
2. Suba a app local apontada para ele.
3. `playwright` em viewport de celular, screenshot, e **olhe**.

Três vezes no mesmo dia a prévia renderizada pegou "falta: BRUNO, CARLA" ao lado de
"todos se manifestaram". Quem lê acredita na segunda, que parece conclusão.

A paridade JS×Python (no publicador) extrai o JS real da f-string do painel e prova que
painel e contrato casam a ata com **as mesmas linhas** — sabotando a função de chave o
teste acusa na hora.
