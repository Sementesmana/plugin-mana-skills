---
name: agente-precificacao
description: "Mapa do agente-precificacao / Maná Price (MANÁPRIC) da Sementes Maná, Flask+PG (schema precificacao)+Railway: catálogo de cultivares por tier, Preço Exceção (desmontagem royalty+germoplasma), motor de preço único, TSI, frete OSRM, PDF de orçamento, Plano de Plantio e o report Maná Price com o interpretador da MAIA. Traz o que o código não diz: decisões, armadilhas, contratos e pendências. Use SEMPRE no agente-precificacao ou ao citar precificação, Maná Price, tier de preço, germoplasma, royalties, desmontagem, vencimento, tabela de frete, OSRM, TSI, cotação de sementes, API externa de preço, MAIA, interpretador, plano de plantio, plantas/ha, bags, sacarias, microrregião."
---

# agente-precificacao (Maná Price / MANÁPRIC) — mapa

## O que é
- Cotação e orçamento de semente de soja: painel dos vendedores (`/painel`, JWT), motor de preço determinístico que todo consumidor consulta, API de leitura para agentes, e publicador do report "Maná Price" (MAIA/app da diretoria e bot do grupo no WhatsApp).
- Repo `Sementesmana/agente-precificacao`, branch `main`, Railway por git push (NIXPACKS, healthcheck `/health`). Produção: https://agente-precificacao-sm.up.railway.app
- Dono/mantenedor: Dayan (cabeçalho do `app.py`). O `.claude/CLAUDE.md` manda não alterar código sem o Dayan pedir e explicar em linguagem de negócio antes de qualquer push.
- Banco: banco-mana, schemas `precificacao` + `comum` (safras, ICMS). Várias tabelas novas nascem por `CREATE TABLE IF NOT EXISTS` dentro do `app.py`/`negociacao.py`, não por migration.

## Onde está a verdade
- `precos.py` — A CONTA e as regras de mês: vencimento, mês do royalty, ordem dos meses, fórmulas, interno × comercial. Sem banco, sem HTTP, sem Flask.
- `precos_fonte.py` — o provider que lê a base real (royalties, TSI, germoplasma sugerido, safra, nomes do catálogo). Só procura; não decide.
- `rota_preco.py` — portas do motor (`/api/preco/*`) e do contrato de report (`/api/reports`, `/api/report/orcamento*`), guardas de chave.
- `negociacao.py` — estado do orçamento por conversa, vocabulário do delta (`CAMPOS_DELTA`), casamento nome dito × catálogo, consultas, envelope, a `fala`.
- `interpretador.py` — frase → delta via LLM (única chamada de IA do app); o `SYSTEM_NEGOCIAR` é doutrina travada por teste.
- `app.py` — painel, catálogo, admin, plantio, orçamentos, fertilizantes, receitas TSI, API externa v1 (casca sobre o motor).
- `templates/painel.html` — frontend único (Tailwind, Leaflet, jsPDF). Desmontagem só PINTA o que o motor devolve.
- `auth.py` — JWT, hash, `API_KEYS_EXTERNAS`. `tests/` — boa parte das regras abaixo é cobrada por teste.
- `references/endpoints.md` — referência de rotas (pode estar atrás do código; conferir no `app.py`).

## Regras e decisões que o código não explica sozinho
- **A conta mora num lugar só** (Xayer, 10/09): painel, app da diretoria e MAIA perguntam ao motor e recebem o MESMO número. Tela não soma preço; célula sem preço do motor diz "sem preço" e não deixa ir para o carrinho.
- **A IA não faz conta**: a MAIA só produz o delta; número vem do motor; listas e nomes vêm do catálogo, nunca escritos pelo modelo.
- **Fórmula** (consenso Alex·Dayan, 10/09): `preço = royalty + germoplasma + TSI líquido + frete`, inversa exata para descobrir germoplasma, **sem travar em zero** (negativo = preço não cobre os custos).
- Sem germoplasma informado, a API externa usa o preço de tabela (`precificacao.precos`, que já embute royalty+germo) — é lido, não calculado.
- **Germoplasma sugerido** é valor CADASTRADO por mês (`germoplasma_sugestoes`), referência de tela; quem decide o germo é o comercial. Nunca entra sozinho numa conta (o mês a mês sem germo sai como custo e pede o germo).
- **Mês do royalty** (Xayer, 12/09): 1:1 com o mês de pagamento, exceto À VISTA → MARÇO e À VISTA 2 → ABRIL (antes ambas puxavam MAIO e apagavam a diferença). MAIO/27 usa royalty próprio `MAI/27` — não é o MAIO da safra.
- **Vencimento** (Xayer, 12/09): dia 30 do PRÓPRIO mês; fevereiro = último dia real (bissexto conta); à vista não tem vencimento. Data fora da regra é recusada, nunca arredondada. Ano vem das datas da safra ativa.
- **Ausência é resposta**: sem dado oficial → 422 com o motivo (nunca 500, nunca 200 vazio, nunca mês/região vizinha nem média). Uma cultivar sem dado não derruba as outras; um mês sem dado não derruba a grade.
- Busca normaliza acento dos dois lados (cadastro está sem acento; `unaccent` pode não existir → `TRANSLATE` no SQL); tolera só o código entre parênteses do nome; **não** aproxima região. Cultivar/TSI fora de linha é cotado com aviso.
- **Nome dito × catálogo**: mesmo nome escrito diferente vira o do catálogo em silêncio; nome inexistente NUNCA é trocado sozinho (orçar a cultivar errada é o pior defeito) — vai com as parecidas e a pergunta. Vale também para o TSI (FORTENZA DUAL não vira FORTENZA DUO).
- **PDF/visão do cliente não mostra royalty nem germoplasma** (`para_comercial` constrói objeto novo de propósito). O royalty aparece só na fala interna do grupo. PDF do Maná Price leva `REGIÃO:` no subtítulo; PDF do plantio é técnico, sem preço.
- **Escopo da negociação é a conversa**: `negociacoes.usuario` é texto livre — telefone no app, `g:<id-do-grupo>` no grupo. Uma negociação ativa por escopo; excluir encerra e mantém a auditoria.
- **Pergunta não muda orçamento**: pergunta inversa e consultas (listas, preço mês a mês) não são gravadas. Delta vazio não é erro. Delta e consulta juntos → vale o delta (Alex, 30/09).
- **Um cadastro de chave técnica só**: `API_KEYS_EXTERNAS` (`nome:chave,...`) vale para `/api/v1/*`, `/api/preco/*` (que aceita também o JWT do painel) e o report (`X-Report-Key` ou `X-API-Key`). Fail-closed: cadastro vazio = ninguém entra. Rotacionar = editar a env no Railway.
- Frete: tabela de KM (OSRM, fallback Haversine ×1,3) OU valor digitado por bag (Xayer, 12/09: "ambos"); no digitado a distância é "—", não 0. CIF no PDF quando há frete cobrado, de qualquer origem.
- Tier: banco e filtro `?tier=` usam ALTO/MEDIO/BAIXO; a tela mostra OURO/PRATA/BRONZE (ALTO=Ouro…). Os descontos 3%/4,8%/6,7% estão chumbados em `RANKING_DESCONTOS` no painel.html — `config_tier_descontos` e a tela admin existem, mas o painel não lê. Catálogo só mostra `condicao='AGRICULTOR'` e `ativo`.
- Plano de Plantio é independente do catálogo (FK opcional). `plantas_ha = 0` = "não recomendado pelo agrônomo" (diferente de variedade bloqueada). Soma de hectares tem de bater (tolerância 0,01) senão o cálculo é bloqueado.
- Permissões por perfil (`PERMISSOES_PERFIS` em `config_geral`) só escondem abas no front. No backend, o admin é protegido por `@perfil_required` (admin+gerente ou só admin, conforme a rota); rotas só com `@login_required` (ex.: POST `/api/desmontagem/germoplasma`) aceitam qualquer token, inclusive o do `/painel-embed`.
- Royalties são **por bag**, não por hectare — nunca aplicar multiplicador de área.
- Dinheiro em Decimal no motor; envelope marca todo valor `exato: true` (senão 10.240 e 10.440 saem "R$ 10 mil"). Carimbo do report sempre com fuso UTC.

## Armadilhas conhecidas
- **"Espelha X, manter sincronizado" é defeito anunciado**: vencimento já viveu em três tabelas que discordavam (tela 30/11, PDF 31/10, API "30/10" → SETEMBRO), sem erro nenhum. Regra que dois lugares usam: um serve, o outro pergunta.
- Push recusado passa despercebido: conserto do fuso ficou 9 dias fora de produção (14→23/09). `ahead 1` não existe para ninguém — conferir `main` × `origin/main` antes de encerrar.
- Catálogo grava nome colado (`NEO700 I2X`) e ninguém fala colado: `_chave` separa letra de número nos dois lados. Não "simplificar".
- Modelo manda marcações (`listar_cultivares`, `gerar_pdf`, `consultar`) DENTRO do delta → valem nos dois lugares; chave fora de `CAMPOS_DELTA` é descartada e anunciada. Mudar o vocabulário exige mudar prompt e contrato juntos (teste cobra).
- Meses com /27 são o ponto frágil: `precos` grava `MARÇO/27`, `tsi_precos` grava `MARÇO`, royalty grava `MAI/27`. O mês a mês já traduz; `precos.calcular` com `mes_ref: 'MARÇO/27'` + TSI ainda não acha o TSI (dívida conhecida).
- Consulta `preco_meses` custa ~3 queries por mês (~48 por pergunta, sem cache): não chamar em loop nem aumentar meses sem cache (4 workers, timeout 120).
- Inputs editáveis em tabela: nunca re-renderizar a tabela no `oninput` (perde foco a cada tecla) — atualizar modelo + célula derivada.
- Estado com sufixo (`MATO GROSSO (NORTE)`, `PARANA ALTO`…): buscar pelo nome completo; tirar o sufixo esvazia 8 microrregiões.
- PyJWT 2.x: `sub` tem de ser string. Consequência ainda viva: checagens `orcamento.usuario_id != g.usuario['sub']` comparam int com str (vendedor barrado no próprio orçamento) — o fluxo de orçamentos do servidor não é usado pelo painel hoje.
- Hash de senha com salt fixo `mana-salt-2026`; `banco/criar_admin.py` tem de usar o mesmo. Esse script APAGA e recria admin@mana.com com a senha padrão — não rodar sem querer.
- PUT `/api/admin/frete` espera array direto, sem wrapper.
- CORS só aceita SoftExpert (prod/test) e localhost.
- Testes: sem as dependências instaladas, os de rota são PULADOS (skip) e o pytest fica verde — instalar `requirements.txt` antes de confiar.
- Health tenta semear royalties e regiões de plantio a partir de `banco/*_seed.json`, que não estão no repo: é no-op silencioso.

## Contratos externos
- **mana-llm-gateway**: só o interpretador; `LLM_GATEWAY_URL` = raiz https **sem `/v1`**, chave virtual própria (alias `agente-precificacao`, custo no cockpit), modelo `mana-equilibrio`. Via `urllib`. Env errada não derruba o app: loga no boot e a rota responde 503 com o motivo; gateway fora → 503, nunca delta vazio.
- **mana-reports / MAIA (app da diretoria)**: contrato de report (ADR 2026-09-04), report por usuário (`X-Report-Usuario`, BFF não cacheia). O MANÁPRIC não desenha PDF: declara `compartilhar.pdf` (só com orçamento completo) e o mana-reports desenha (`/api/servico/report/agente-precificacao/orcamento.pdf`, chave `SERVICO_KEYS` lá).
- **Bot do grupo Maná Price (WhatsApp)**: usa `/api/report/orcamento/interpretar` com escopo `g:<id>`; a auditoria registra o grupo, não quem falou.
- **Agente de preço do Alex**: consome `/api/v1/precificacao/*` (só leitura, `X-API-Key`). Os `§` nos comentários do motor referem o documento/skill do Alex.
- **SoftExpert**: `/painel-embed` (iframe) entra sem login com token de vendedor.
- **OSRM público** (`router.project-osrm.org`) para rota; Haversine ×1,3 se cair.
- LGPD: telefone só aparece pelos 4 últimos dígitos no envelope e nos logs; `orcamentos.cliente_cnpj` é dado de cliente.

## Como testar e subir
- `pip install -r requirements.txt` e `python -m pytest -q` (motor, fonte, negociação e interpretador rodam sem banco; API externa sobe o app com banco falso).
- Deploy: `git push origin main` → Railway (~2 min); conferir `/health` (mostra safra ativa e status do banco, sempre 200).
- Migration do plantio: `banco/2026-05-15_plano_de_plantio.sql` (idempotente) + seed `banco/popular_plantio_inicial.py` (uma vez).
- Ao confirmar caso real do interpretador, ler o log `[INTERPRETADOR]` (mostra delta com valores e a consulta).

## Pendências
- `/api/debug-token` ("remover depois") é público e devolve o prefixo do `JWT_SECRET`; `decodificar_token` também loga o prefixo. Remover.
- `/painel-embed` emite a qualquer visitante um token de vendedor de 30 dias; com ele dá para gravar `/api/desmontagem/germoplasma` (só exige login) e consultar o motor.
- Senha em SHA256 com salt fixo (comentário pede bcrypt); defaults de `JWT_SECRET`/`PAINEL_SENHA` no código.
- Sem versionamento da base: `comum.safras` não tem versão (`versao: None` de propósito); `royalties_por_cultivar` não tem carimbo de atualização. Reprodutibilidade de cálculo antigo é trabalho futuro.
- mana-reports ainda tem a própria cópia do prompt (`maia.negociar`) e compõe a resposta: migrar para `/interpretar` é o 2º commit do ADR 2026-09-23.
- Auditoria do grupo sem autor da frase (pede o bot mandar quem falou).
- Front ainda carrega cópias de `MESES_PAGAMENTO` e da tabela de vencimento (`VENC_MES`) como fallback; docstring de `precos.mes_do_royalty` diz que a regra tem dois donos (já não tem — vem de `/api/preco/vencimento`).
- `banco/criar_admin.py` traz a string de conexão do banco com senha chumbada no repo — rotacionar a credencial e passar a ler `BANCO_MANA_URL`; trocar a senha do admin@mana.com em prod.
- As consultas do interpretador (regioes, cultivares, tsi, tsi_meses, royalty_meses, germoplasma, preco_meses) foram ao ar sem rodar as queries contra o banco real; aba Orçamentos do painel "em breve"; fertilizantes só com GOIAS cadastrado.

## Para ir além
- `.claude/CLAUDE.md`, `.claude/COMMON_MISTAKES.md`, `.claude/QUICK_START.md` (⚠ `ARCHITECTURE_MAP.md` traz o mapa de meses antigo, MAIO→A VISTA — está errado).
- Vault: `ManaVault/06-Agentes-e-Skills/agente-precificacao.md`; ADRs 2026-05-15 (módulo Plano de Plantio), 2026-09-04 (contrato de report), 2026-09-23 (interpretador mora no MANÁPRIC), 2026-06-13 (porta única LLM).
