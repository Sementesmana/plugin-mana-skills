---
name: agente-dm
description: "Mapa do agente-dm / Maná Mercado (Sementes Maná), plataforma de Desenvolvimento de Mercado em Flask+Alpine+PG (banco-mana, schema dm)+Railway. Lê pedidos de bonificação, difusão e doação do Simple Agro pelo lake (SEM login no SA) e cobre solicitações com aprovação, protocolo DM-ano-seq, termos, Clientes e Áreas, carteira, visitas (5 etapas), lado a lado, emplacamentos, Dias de Campo, estoque de sacarias, metas das obtentoras e resultado de produtividade. Traz o que o código não diz: decisões, armadilhas, contratos e pendências. Use SEMPRE no agente-dm, plataforma DM, Maná Mercado, Vincular Pedidos, segregação por vendedor/agente, termo de uso de imagem, mana-mercado.html."
---

# agente-dm — mapa (Maná Mercado)

## O que é
- Plataforma do Desenvolvimento de Mercado: vincula os pedidos DM do Simple Agro (bonificação/difusão/doação) a uma solicitação justificada com aprovação, e acompanha o cliente no campo (visitas, lado a lado, emplacamento, Dia de Campo, resultado). Porta a maquete validada do Dayan (`docs/referencia/mana-mercado.html`) — portar, não reinventar.
- Repo `Sementesmana/agente-dm` (privado). Co-donos **Xayer + Dayan**, "um motorista por vez" (`git pull` antes, `git push` depois). Quem especifica as regras de tela é o Dayan.
- Railway, deploy por `git push` (Nixpacks, healthcheck `/health`). Produção: `https://agente-dm-production.up.railway.app (conferida 2026-11-01)`.
- Banco-mana, schema `dm`, criado/migrado no boot por `db.py`. Sem LLM e sem WhatsApp hoje (conformidade com `mana-arquitetura-padrao` por ausência).

## Onde está a verdade
- `config.py` (docstring = por que não loga no SA) · `lake_sa.py` (leitura do lake, `tipo_dm`, `visivel` = segregação) · `auth.py` (papéis, Bearer, `vendedor_pode`).
- `db.py` — DDL inteira + comentários do porquê de cada tabela; seeds "uma vez só" marcados no `audit_log`.
- Módulos: `solicitacoes.py` (estados, arquivos, protocolo) · `clientes.py` (Clientes e Áreas, carteira, termos, situação, acompanhamento) · `emplacamentos.py` · `eventos.py` (Dias de Campo) · `estoque.py` · `lado_a_lado.py` · `produtividade.py`+`registro_docx.py` · `visita_etapas.py` (puro) · `metas.py`. As docstrings de topo registram a spec do Dayan com data — ler antes de mexer.
- `templates/app.html` (SPA Alpine; `DM_MENU`, `VENDEDOR_ABAS`) + `static/js/dm-*.js` (mixins por módulo).
- `docs/referencia/` — pacote original do Dayan (maquete, FLUXOS, MODELO-DADOS, TERMO, BACKLOG, `mana-dm-sistema.html` = protótipo dos Dias de Campo).

## Regras e decisões que o código não explica sozinho
- **Não loga no Simple Agro** (Xayer, 2026-09-24; ADR 2026-08-27 "dado entre agentes trafega pelo banco"). Ordem: `agente_financeiro_sa.data_lake` chave `orders:<safra_id>` (dono Dayan, tem safra encerrada) → `agro.lake_pedidos_raw` (agente-agro, só safra corrente). Dado AO VIVO só se alguma tela precisar de atualização toda hora, e aí pelo `mana-sa-gateway` (`/v1/pedidos` existe lá, parado).
- **Não há lake de cadastro de clientes do SA**: Clientes e Áreas é montado dos PEDIDOS (todas as vendas). Só existe cliente que tem pedido. Chave = `_id` do cliente no SA, ou `n:<NOME>` sem id.
- **Tipos DM** por substring sem acento (`BONIFICA`/`DIFUS`/`DOACAO`). No SA 26/27 só existem VENDA BONIFICAÇÃO e VENDA DIFUSÃO; doação ainda não apareceu.
- **Dono do pedido = vendedor + agente(s)**, todos enxergam. Usuário liga ao SA pelo ID (`sa_vendedor_id`), nunca pelo nome; vendedor sem vínculo não vê nada. Segregação no servidor/SQL, não só na tela.
- **Solicitação**: uma por pedido; aprovação em um nível (admin = time de desenvolvimento); só rascunho edita; sem aprovação não gera documento/resultado final. Motivo que exige lado a lado pede concorrente + autorização + termo.
- **Protocolo `DM-<ano>-<seq>`**: UMA sequência (`protocolo_seq`) para solicitações, termos do cliente, Lado a Lado e Resultados. O Resultado se liga à autorização do produtor pelo protocolo dela.
- **Perfis** (Dayan, 2026-09-30): vendedor SÓ Emplacamentos + Vincular Pedidos + Solicitações, negado NO SERVIDOR (`vendedor_pode`, 403). Consequência: Desenvolvedor de Mercado que precisa de Clientes/carteira/Metas/Dias de Campo/Resultados tem de ser admin; a carteira é que divide os clientes entre eles.
- **Carteira** (um cliente → um usuário): o desenvolvedor vê os clientes da carteira inteiros + o que já vê pelo SA. Vale só na aba Clientes.
- **Termos chegam prontos de fora**: o sistema só anexa a via assinada + metadados e gera o protocolo; nada é enviado ao produtor. Arquivo fica no banco (`dm.arquivos`), não em nuvem pública — Cloudinary descartado (dado pessoal, e o DM já tem servidor). Termos em `static/termos/` são MINUTA até o jurídico validar.
- **Resultado de Produtividade é REGISTRO INTERNO**, não termo e sem assinatura: a autorização de uso de imagem/resultado já assinada pelo produtor prevê a apuração. Só aceita termo do MESMO cliente. A 1ª variedade Maná é a principal; dif % = (principal − concorrente) ÷ concorrente; resumo usa a melhor concorrente. Word gerado por código (python-docx), sem .docx binário modelo no repo.
- **Status/tipo de acompanhamento do cliente são CALCULADOS** (decisão do Dayan, sem campo manual). Filtro Safra = cliente NO DESENVOLVIMENTO na safra (pedido DM, LxL, resultado ou emplacamento), não quem só comprou. Variedade difundida = item de pedido DM com solicitação aprovada, nunca digitada.
- **Cancelar cliente é marcador**: continua em listas/relatórios com CANCELADO; nada é apagado. Situação/entrega/plantio só admin altera.
- **Lado a Lado e aviso de plantio são ponte, sem trava**. Excluir LxL é bloqueado se houver resultado ligado.
- **Visitas**: cliente e fazenda sempre escolhidos do cadastro. Roteiro de 5 etapas (plantio, stand 10–14 dias após plantio, floração, reprodutivo, colheita); a colheita SÓ registra, não gera Resultado.
- **Emplacamento**: sem papel novo (consultor = quem cadastra; desenvolvedor = `responsavel_id`, sugerido pela carteira). **Sem mapa**: Leaflet removido (dava erro) e Google Maps avaliado e NÃO adotado (chave com billing, env nova, instável no iframe do SE); nem Waze/"Ir até o local", nem nas fazendas de Clientes. Não reintroduzir sem pedido do Dayan.
- **Neogen** (obtentora contém NEOGEN): 3 fotos DIFERENTES em Foto 1/2/3; md5 bloqueia a mesma imagem no emplacamento, no original e nas extensões; foto trocada fica como substituída. Vale no finalizar — concluídos antigos não mudam. Placa a cada 200 m é só sugestão.
- **Extensão** = novo emplacamento apontando sempre para o ORIGINAL (extensão de extensão também), nunca de cancelado.
- **Metas: tipo de meta é CADASTRO, não código**. O código só tem o catálogo de FONTES de apuração; tipo novo nasce manual e, se ganhar módulo, cria-se a fonte. Tipo usado não se exclui, só inativa. Obtentora casa por nome (upper/trim).
- **Dias de Campo**: obtentoras/consultores/responsáveis são cadastro manual (não vêm do SA). Sacaria agrupa por cultivar × EMBALAGEM (bag não soma com kg); sacaria antiga sem embalagem conta como Saca. Estoque de sacarias: saldo pode ficar negativo de propósito; DC cancelado sai da necessidade.
- **Regra de ouro das migrações** (já há dado lançado): DDL só aditiva; PUT sem os campos novos PRESERVA o gravado (tela antiga em cache não pode apagar nada) — travado por teste.
- Fotos de Dia de Campo e anexos de Clientes não abrem para vendedor; foto só entra em registro se foi a própria pessoa que subiu (ids de arquivo são sequenciais).

## Armadilhas conhecidas (sintoma → causa → o que fazer)
- Tela diz "nenhum pedido" com o lake fora → violaria "falha nunca vira dado" → `LakeIndisponivel` vira 503; com cache, serve a última leitura com aviso DECLARADO. Nunca devolver lista vazia; em todas as safras, safra que falha vira aviso, todas falhando = erro.
- Citar id de arquivo alheio como "foto" liberava o arquivo (inclusive termo com dado pessoal) → sempre `checar_fotos_proprias`; admin não é exceção.
- Download com nome contendo –/’/emoji dava 500 (gunicorn recusa header não-Latin-1) → nome ASCII + `filename*=UTF-8''`.
- Fazenda sem área/coordenada → o payload do SA varia e a extração é tolerante → antes de mexer no parser, `GET /api/clientes/sonda` (admin) mostra as CHAVES reais do pedido.
- Termo ilegível → foto sobe reduzida no navegador, mas termo/documento sobe ORIGINAL (`dmSubirArquivo` com `original`) por legibilidade → não reduzir documento.
- Upload aceito com tipo errado → o mime do navegador é ignorado; tipo vem da assinatura dos bytes (`tipo_real`). Word baixa como attachment; PDF/imagem abrem.
- CSV de presença abrindo fórmula no Excel → prefixar `'` em célula iniciada por = + - @.
- Dois gravando o mesmo Dia de Campo → trava otimista `versao` (409 e a tela recarrega). Não remover.
- Deploy novo e antigo subindo juntos → DDL e seeds sob `pg_advisory_xact_lock`; CHECK de `cadastros.tipo` refeito idempotente num bloco DO. Seed apagado não volta porque a marca fica no `audit_log`.
- Console com unhandled rejection `{isFromCancelledTransition:true}` → é do próprio Alpine quando uma transição é cortada; silenciado só esse caso em `dm.js`. Não fechar+reabrir modal no mesmo tick.
- CSS da maquete extraído começando com `<style>` anula o `:root` inteiro. `mana-mercado.css` fica intacto.
- Login some dentro do SoftExpert → cookie de terceiro bloqueado pelo Chrome e o validador do SE recusa qualquer diretiva de frame → `SE_EMBED=1` tira os headers de frame e o front anda por Bearer (token no corpo do login, cookie tem precedência); anexo abre via fetch com token, não `<a href>`. GPS no iframe depende de `allow="geolocation"` e HTTPS.
- Mutação recusada sem motivo aparente → falta o header `X-DM: 1` (proteção CSRF); fetch de fora não manda.

## Contratos com sistemas externos
- **Simple Agro**: só leitura via lake do banco-mana (acima). CPF/CNPJ, telefone e e-mail não saem do lake: o DM guarda cliente por id SA/nome. No Word de resultado o CPF fica em branco para preencher à mão.
- **agente-financeiro-sa (aba Growth)**: consome `GET /api/integracao/clientes-dm` (Xayer, 2026-10-16) para pintar de verde quem está em DM. Sem sessão: header `X-Integracao-Key` = env `DM_INTEGRACAO_KEY`; sem env → 503, nunca aberto. Visão admin, só campos de whitelist LGPD + números de pedido (chave de cruzamento).
- **SoftExpert**: só embed (widget Página WEB, ver armadilha). Nada é lido ou escrito no SE.
- **banco-mana**: escreve só no schema `dm`; lê `agente_financeiro_sa` e `agro`.
- **LLM / WhatsApp**: quando entrarem (OCR da lista de presença, alerta de pedido sem solicitação), pelo `mana-llm-gateway` e pelo hub `agente-whatsapp`.

## Como testar e subir
- `pytest -q` sem banco; ponta a ponta com `DM_PG_TESTE=<Postgres DESCARTÁVEL e vazio>` — nunca o banco-mana.
- Regras do CLAUDE.md: não alterar código sem o dono pedir ("verificar" = reportar); antes de commitar `git diff --cached --stat` (diff fantasma de CRLF) e `pytest -q`; deploy só por `git push`, nunca `railway up`; credenciais só em env do Railway.
- Boot: sem `DATABASE_URL`/`SECRET_KEY` não sobe (fail-fast); `init_db` falhando, sobe e `/health` mostra `degraded`. 1º admin só é semeado com a tabela de usuários vazia.
- `SAFRAS` tem default no código (só 26/27): sem a env o app sobe CALADO na 26/27; só `{}` ou JSON inválido derruba. Safra nova = definir `SAFRAS` no Railway (label → id do SA; a 1ª é a padrão das telas).
- Mudança que afeta URL/env/endpoint/consumidor → atualizar a nota do vault.

## Pendências
- Próximas fases (portar da maquete): Relatórios gerais · Treinamento · Lado a Lado Plantio/Colheita · lista de presença A4 + OCR.
- Termos (`static/termos/`) aguardando validação do jurídico.
- Housekeeping: `.env.example` e README dizem upload 8 MB, o código usa 10 MB por padrão; `.env.example` não lista `SE_EMBED`, `TOKEN_HORAS`, `DM_INTEGRACAO_KEY`; o BACKLOG ainda fala em JWT, mas o token é próprio (itsdangerous).

## Para ir além
- `CLAUDE.md` do repo; nota do vault `ManaVault/06-Agentes-e-Skills/agente-dm.md`; `docs/referencia/BACKLOG.md` e `FLUXOS.md` (Dayan).
- Skills irmãs: `agente-financeiro-sa` (dono do lake de pedidos e consumidor da integração), `agente-agro` (lake da safra corrente), `mana-arquitetura-padrao`.
