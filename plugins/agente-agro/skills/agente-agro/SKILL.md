---
name: agente-agro
description: "Mapa do agente-agro (Sementes Maná), Flask+Railway de inteligência geoespacial: NDVI Sentinel-2 com zonas de manejo K-Means, seleção de cena (menos nublada, mais atual, por data), croqui de talhão para CPR, busca CAR/SICAR com cache no banco-mana, clima Open-Meteo, painel Leaflet multi-talhão e Visão Macro (CARs do município + Clientes Maná do Simple Agro × CAR, data lake schema agro). Traz o que o código não diz: decisões, armadilhas, contratos e pendências. Use SEMPRE ao mexer no agente-agro ou ao citar NDVI, talhão, croqui para CPR, CAR, SICAR, Sentinel, Copernicus, STAC, zonas de manejo, taxa variável, shapefile, GeoJSON, Visão Macro, lake agro, lake_pedidos_raw."
---

# agente-agro — mapa

## O que é
- Serviço de geoprocessamento agrícola: NDVI e zonas de manejo por talhão, croqui para CPR, CAR/SICAR, clima e um painel Leaflet (`/painel`) com dois modos: Micro (talhões) e Macro (região/município, clientes Maná sobre os CARs).
- Repo `Sementesmana/agente-agro` (antes vivia em `hiperautomacao-mana/agente-agro`; as duas skills antigas ainda apontam o monorepo — defasado). Dono: o repo não diz.
- Produção: https://agente-agro-production.up.railway.app (conferida 2026-11-01 via /health). Railway, deploy por git push.
- Sem LLM e sem WhatsApp de saída: é serviço reativo, não agente de loop. Banco: banco-mana (tabela pública `car_imoveis` + schema próprio `agro`).

## Onde está a verdade
- `agente_agro.py` — pipeline NDVI (STAC → Processing API → rasterio → K-Means → vetorização), diagnóstico/dose por zona, croqui, clima, histórico NDVI.
- `sicar_client.py` — busca CAR (banco → API pública SICAR → grava no banco), por coordenada, por CPF/CNPJ, import bulk. `_get_conn()` é a conexão única do banco usada pelo `app.py` todo.
- `app.py` — rotas; bloco Visão Macro (simplificação, gzip, IBGE); bloco Clientes Maná (login e leitura do SA, regras de status/bags/coordenada); bloco DATA LAKE (`_lake_init` cria/migra o schema `agro` a cada uso).
- `templates/painel.html` — SPA inteira (estado por talhão, filtros client-side, polling do lake).
- `Dockerfile` + `railway.toml` mandam no runtime. `Procfile` e `nixpacks.toml` são legado IGNORADO (o build é DOCKERFILE).

## Regras e decisões que o código não explica sozinho

### NDVI / talhão
- **STAC-first**: acha a data da cena no catálogo (~1s) e só então chama o Processing API numa janela de ±1 dia — varrer 90 dias no Processing é lento. O STAC NÃO aceita `sortby` (dá 400); já devolve do mais recente para o mais antigo.
- Modo "mais atual" é troca consciente: evalscript SEM máscara SCL (aceita pixel de nuvem). Os outros exigem SCL limpo. Se sobram poucos pixels, cai para todos os finitos; abaixo de `num_zonas*10`, erro.
- Zona 0 = menor NDVI = vermelho = **dose mais alta** (taxa variável inversa ao vigor). Diagnóstico por faixa de NDVI e fator de dose ficam em `processar_ndvi_talhao` — não duplicar em outro lugar.
- Croqui usa os **polígonos vetorizados** já calculados (igual ao mapa), não o raster (ficava pixelado). Sem `zonas` no payload, o backend reprocessa o NDVI (30-90s): quem chamar deve mandar as zonas prontas. Aceita vários talhões (`talhoes_lista`) e o formato antigo de um talhão só (compatibilidade com agente-cpr).
- Painel: cada talhão tem sua própria camada de zonas (processar um não apaga o outro). Tiles padrão Google Satellite: o Esri tinha buracos em MT em zoom alto (ficou só como opção).

### CAR / SICAR
- Ordem da busca por código: banco-mana → `consultapublica.car.gov.br/publico/imoveis/search` (sem CAPTCHA) → grava no banco. Por coordenada: `getImovel`; HTTP 500/404 ou corpo vazio = "sem imóvel ali" (vira 404 limpo, não erro). Cobertura do `getImovel` é falha em área peri-urbana.
- CPF/CNPJ: só banco-mana. O SICAR público não expõe CPF e o shapefile AREA_IMOVEL não traz o campo: a base importada (MT, GO) tem `cpf_cnpj` nulo, então essa busca na prática não acha nada.
- **WMS do SICAR: não reimplementar.** `geoserver.car.gov.br` falha no handshake SSL; `getGeoserverImages` devolve 503 sem cookie de sessão do navegador, nem com proxy+Referer. O overlay saiu do painel; a rota `/wms-sicar` ficou como resto morto.
- Busca SICAR em tempo real para a Visão Macro foi DESCARTADA (instável, decisão Xayer): a Macro só usa o que já está importado em `car_imoveis`.
- CAR traz o imóvel inteiro, não talhões: o talhão é desenhado por cima ou importado (KML/GeoJSON de GPS, Avenza, Google Earth, drone exportado em KML/GeoJSON).

### Visão Macro e Clientes Maná
- Estatística regional em hectares e alqueire **paulista (2,42 ha)**, padrão do mercado de sementes em MT. Faixas de tamanho (Top Farmer >1.000 ha etc.) estão no código.
- Polígonos simplificados no backend com tolerância por volume + coordenadas arredondadas + gzip; no front, `L.canvas()` é obrigatório (milhares de polígonos travam o SVG).
- Pedidos lidos DIRETO do Simple Agro (`/api/orders`): exceção análoga ao ADR-0010 do gestor-comercial, porque `geolocalizacao_entrega` não sai pelo agente-financeiro-sa. Lógica de coordenada portada do agente-tms.
- Regras canônicas (mapa-pedidos/estoque/gestor-comercial): `item.quantidade` JÁ É BAGS; cultivar = `item.produto.nome`; ton = peso_embalagem × qtd / 1000; situação = `status_pedido` (o `status` cru do SA é booleano "integrado" e vazava como "True" — decisão Dayan 2026-07-03).
- Coordenada só vale se lat E lng forem válidas; 0/0 é ausente. Coordenada digitada sem ponto/sinal é autoconsertada (÷1e6, negativa) só se as duas caírem na caixa do Brasil (caso real: pedido 260000190015).
- Ponto em mais de um CAR → desempata pelo **menor** CAR. Pedido com coordenada fora de CAR vira pino.
- **Match estadual completo (regra Xayer)**: no builder, cada pedido é testado contra os CARs de TODAS as cidades da UF, não só a cidade escrita no pedido; só descarta o que está comprovadamente em OUTRO estado (malha IBGE da UF com buffer 0,02°). Visão Brasil: une os lakes por UF e mostra como pino tudo que não casou, inclusive UFs sem base CAR.
- Lista de safras é a canônica do agente-mapa-pedidos, hardcoded; ao virar safra, atualizar as duas (e `SA_SAFRA_ID`).
- **Acesso/LGPD**: a senha dos endpoints de clientes caiu em 2026-07-12 (decisão Xayer: painel interno embutido no SE). `?senha=` é aceito e ignorado; `PAINEL_SENHA` não protege nada hoje. CPF/CNPJ nunca sai da Camada de Clientes; razão social e vendedor saem.

### Data lake `agro` (banco-mana)
- Tabelas: `agro.lake_pedidos` = pedidos JÁ PROCESSADOS (lat/lng, cultivares/bags, status), uso interno; `agro.lake_pedidos_raw` = orders BRUTOS do SA, contrato com o agente-mapa-pedidos; `lake_visao` (por município), `lake_clientes_uf` (por UF+safra), `lake_status`.
- Motivo: cache em memória é por worker e morre a cada deploy. Lake-first + advisory lock, desenho da habilidade data-lake-pg mas INLINE (instalar a habilidade via git+https exigia PAT).
- Anti-452 do SA (2026-07-18): pedidos compartilhados no banco = 1 chamada SA por safra/30 min para a empresa toda; só um worker busca (os outros esperam o lake até 90s); retry 8s/20s em 452/429/5xx; se o SA continuar fora, serve o lake velho. Safra encerrada vale 7 dias.
- O builder roda em thread, por lotes paralelos (`LAKE_PARALELISMO`, padrão 6), com progresso no banco (visível a todos os workers; o painel faz polling). Recusa novo build se o status anterior tem menos de 5 min (a docstring diz 20 min — vale o código).

## Armadilhas conhecidas (sintoma → causa → o que fazer)
- Mudou `--workers/--timeout` no Procfile e nada mudou → o Railway builda o Dockerfile → mexer no `CMD` do Dockerfile.
- Painel inteiro trava enquanto o lake constrói / tiles enfileiram → worker `sync` (era o CMD antigo até 2026-07-18) → manter `gthread`; request acima do timeout mata o worker que carrega a thread do builder.
- `clientes-uf` devolve `cidades_pendentes` → é proposital: orçamento de ~35s por chamada e o painel rechama até esvaziar. Não "consertar" aumentando o loop.
- HTTP 452 do Simple Agro → rajada (workers × cliques × builder) → nunca chamar `/api/orders` fora de `_sa_pedidos_geo`.
- `Poucos pixels válidos (0)` → cena nublada com SCL mascarando tudo → modo "mais atual", aumentar `max_cloud_pct` ou escolher data.
- `KMeans: NaN in input` → máscara fora de sincronia com a banda NDVI → a máscara refinada exige SCL==1 E NDVI finito; manter.
- Mapa do croqui distorcido → `set_aspect("equal")` em latitude brasileira → manter `"auto"`.
- Zoom do mapa Brasil explode para o mundo → coordenada de vendedor fora da caixa do Brasil → já filtrada e listada em `coordenada_invalida`.
- Área por zona subestimada em talhão grande → resolução limitada a 512 px por eixo e a área conta 0,01 ha por pixel → acima de ~5 km de lado a área é aproximada; usar a área do polígono.
- Importou CAR novo e a Visão Macro não mudou → `agro.lake_visao` não tem TTL e a rota lê o lake antes do banco (mais cache de 6h por worker); o "Atualizar data lake" NÃO renova essa tabela, porque o builder chama a mesma rota, que pula município que já está no lake → apagar as linhas da UF/município em `agro.lake_visao` e então rodar o build ou reabrir o município (cache de worker: esperar 6h ou redeploy). Só `?tol=` ignora o lake, e nesse caso não grava nele.
- KML com vários polígonos importa só o primeiro; MultiPolygon não entra no cálculo de bbox. `.shp` e `.kmz` aparecem no seletor mas o browser recusa (só .geojson/.json/.kml).

## Contratos com sistemas externos
- **Copernicus Data Space (Sentinel Hub)**: OAuth2 client_credentials (`SENTINEL_CLIENT_ID/SECRET`, token em cache); STAC Catalog + Processing API; Sentinel-2 L2A, ~10 m, revisita ~5 dias; tier gratuito ~30 mil req/mês. Credencial: dataspace.copernicus.eu → User Settings → OAuth Clients. `/health` só diz se as variáveis existem, não se o token funciona.
- **SICAR** (`consultapublica.car.gov.br`): certificado ruim, chamadas com `verify=False`; timeout de leitura alto e retry porque fica lento pós-manutenção.
- **Simple Agro**: login `/api/auth/login` com `Origin/Referer` do painel SA (sem isso recusa), token 50 min; filtro do grupo soja (`SA_GRUPO_ID`). Credenciais `SA_*` iguais às do gestor-comercial.
- **IBGE** (malhas de município/UF e região imediata para "vizinhos"): público, cache em memória.
- **Open-Meteo**: público, sem auth.
- **banco-mana**: lê/escreve `car_imoveis` (cache do SICAR) e é dono do schema `agro`.
- **agente-mapa-pedidos** lê `agro.lake_pedidos_raw` (orders BRUTOS do SA) como fonte única anti-452: não mudar o formato. Esse lake só renova quando ESTE serviço consulta o SA (painel aberto ou builder) — não há cron aqui.
- **agente-whatsapp** (declarado nas skills; código no outro repo): pino de localização → `/buscar-car-por-localizacao`; texto com código CAR → `/buscar-car`; usa `AGENTE_AGRO_URL`.
- **agente-cpr**: contrato pensado, não ligado — chamar `/gerar-croqui` (PDF, com zonas) e anexar no workflow SE via SOAP (`newDocument` + `newAssocDocument`).
- **SoftExpert**: só como moldura — CORS liberado para `sementesmana(-test).softexpert.app` (painel embutido). Nada é lido ou escrito no SE.

## Como testar e subir
- CI só compila os `.py` e roda `test_*.py` se existirem (hoje não existem). Teste real = subir e conferir `/health`, `/painel`, um NDVI e `/api/macro/lake-status`.
- Deploy = git push na `main` → Railway builda o Dockerfile (GDAL/PROJ/GEOS: build mais lento que o dos outros agentes). Não usar `railway up`.
- Env que importam: `SENTINEL_CLIENT_ID/SECRET`, `BANCO_MANA_URL`, `SA_BASE_URL/USERNAME/PASSWORD/SAFRA_ID/GRUPO_ID`, `LAKE_PARALELISMO`. `ANTHROPIC_API_KEY`, `SE_URL`, `SE_API_KEY` e `PAINEL_SENHA` aparecem na doc mas o código não usa.
- Regra da casa: não alterar código sem o Xayer pedir ("verificar" = reportar); credenciais só em variável de ambiente.

## Pendências conhecidas
- **Senha do banco-mana hardcoded** como fallback de `BANCO_MANA_URL` em `sicar_client.py` e `app.py` (`/sample-cars`): remover o fallback e rotacionar a senha.
- Painel e endpoints sem autenticação (clientes com razão social; `/importar-car` grava no banco; `/debug/sample-cpf`, `/debug-stac`, `/sample-cars` expostos). Reavaliar à luz da LGPD.
- `/exportar-shapefile` importa `pyshp`, que não está no `requirements.txt` (a skill antiga dizia que estava). E as zonas vetorizadas não levam diagnóstico/recomendação/fator, então DIAG/RECOMEND/DOSE do DBF saem vazios.
- `/historico-ndvi` é SIMULADO (aleatório): falta a Statistical API.
- `_sa_pedidos_geo` usa `limit=-1` no `/api/orders`; a casa registra que o SA trunca/mente nesse modo (skill mana-memoria-operacional) — conferir a contagem contra o SA.
- `clientes-uf` grava o cache em memória com chave `uf` e lê com `(uf, safra)` → nunca acerta (o lake cobre).
- Backlog: PostGIS para talhões; croqui automático no fluxo da CPR; NDVI como indicador de produtividade (agente-estoque); alerta de queda de NDVI pelo hub WhatsApp; legenda de doses no mapa; taxa variável × fixa em R$/ha; Macro fase 3 (camadas SICAR reserva/APP/vegetação, mutuários SICOR/Bacen, ton/R$ por fazenda no popup); migrar o lake inline para a habilidade data-lake-pg.

## Para ir além
- Não há `CLAUDE.md` no repo. Nota do vault: `ManaVault/06-Agentes-e-Skills/agente-agro.md`.
- ADR-0010 do gestor-comercial (exceção de leitura direta do SA); skills `mana-simpleagro`, `mana-habilidade-data-lake-pg`, `agente-mapa-pedidos`.
- Os comentários dos blocos Clientes Maná e DATA LAKE no `app.py` têm o porquê datado de cada regra: ler antes de mudar.
