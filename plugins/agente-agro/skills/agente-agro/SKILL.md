---
name: agente-agro
description: >
  Agente de inteligência geoespacial para agricultura de precisão — Sementes Maná LTDA. Serviço Flask
  no Railway que processa imagens Sentinel-2 para gerar mapas NDVI, zonas de manejo via K-Means,
  buscar imóveis pelo CAR, gerar croquis de talhão para CPRs e consultar clima. Painel web Leaflet
  com múltiplos talhões simultâneos. Seleção de cena: menos nublada, mais atual ou por data.
  Use este skill SEMPRE que precisar trabalhar com o agente-agro — NDVI, croqui, CAR, painel.html,
  Sentinel Hub, K-Means, zonas de manejo, shapefile, GeoJSON, deploy, ou qualquer análise geoespacial
  agrícola. Também use quando mencionar: talhão, Sentinel-2, SICAR, Copernicus, geoprocessamento,
  agricultura de precisão, taxa variável, mapa de fazenda, croqui para CPR.
---

# Agente Agro — Sementes Maná

Serviço Flask implantado no Railway que fornece inteligência geoespacial para agricultura de precisão.
Processa imagens Sentinel-2, gera mapas NDVI com zonas de manejo, busca imóveis rurais no CAR,
produz croquis para CPRs, e consulta clima. Integrado ao SoftExpert e ao agente-cpr.

## Infraestrutura

| Item | Valor |
|---|---|
| **URL produção** | `https://agente-agro-production.up.railway.app` |
| Projeto Railway | `agente-agro` |
| Root Directory | `/agente-agro` |
| Repositório | `github.com/Sementesmana/hiperautomacao-mana` |
| Branch | `main` |
| Arquivos principais | `agente-agro/app.py`, `agente-agro/agente_agro.py`, `agente-agro/sicar_client.py`, `agente-agro/templates/painel.html` |

## Variáveis de ambiente (Railway)

| Variável | Descrição |
|---|---|
| `SENTINEL_CLIENT_ID` | OAuth Client ID do Copernicus Data Space |
| `SENTINEL_CLIENT_SECRET` | OAuth Client Secret do Copernicus Data Space |
| `SE_URL` | URL do SoftExpert (`https://sementesmana.softexpert.app`) |
| `SE_API_KEY` | Token JWT do SoftExpert |
| `ANTHROPIC_API_KEY` | Chave da API Anthropic (Claude) |
| `PAINEL_SENHA` | Senha do painel web (padrão: `mana2026`) |
| `BANCO_MANA_URL` | URL pública do PostgreSQL banco-mana (para busca CAR) |

## Endpoints disponíveis

| Método | Rota | Função |
|---|---|---|
| `GET` | `/health` | Status do serviço + verificação Sentinel Hub |
| `GET` | `/` | Documentação JSON da API |
| `GET` | `/painel` | Painel web Leaflet interativo |
| `POST` | `/buscar-car` | Busca polígono de imóvel rural pelo código CAR ou CPF/CNPJ |
| `GET` | `/sample-cars/<uf>` | Retorna 10 CARs de amostra do banco-mana por UF (debug) |
| `POST` | `/importar-car` | Importa CAR/shapefile para o banco-mana |
| `POST` | `/listar-cenas` | Lista datas de cenas Sentinel disponíveis para um talhão (STAC) |
| `POST` | `/processar-ndvi` | Processa NDVI de um talhão (GeoJSON → zonas de manejo) |
| `GET` | `/historico-ndvi` | Série temporal NDVI (MVP com dados simulados) |
| `POST` | `/gerar-croqui` | Gera croqui PNG/PDF com polígonos vetorizados para a CPR |
| `GET` | `/clima` | Clima atual + previsão 7d + histórico 30d |
| `POST` | `/exportar-shapefile` | Exporta zonas NDVI como arquivo ZIP com .shp/.shx/.dbf/.prj |
| `GET` | `/debug-stac` | Testa conexão STAC (debug) |

## Arquivos do agente

```
agente-agro/
├── app.py                 ← Flask + todas as rotas
├── agente_agro.py         ← Pipeline NDVI: Sentinel Hub → rasterio → K-Means → vetorização + croqui
├── sicar_client.py        ← Busca CAR no banco-mana (PostgreSQL) e portal SICAR
├── templates/
│   └── painel.html        ← SPA: Leaflet + dark theme + múltiplos talhões + seleção de cena
├── requirements.txt       ← Flask, rasterio, geopandas, scikit-learn, matplotlib, pyshp, etc.
├── Procfile               ← gunicorn --timeout 180 (Sentinel pode ser lento)
├── railway.toml           ← Config Railway com healthcheck
├── nixpacks.toml          ← GDAL, PROJ, GEOS (obrigatório para rasterio/geopandas)
└── Dockerfile             ← Alternativa ao nixpacks para deps de sistema
```

## Pipeline NDVI (core do agente)

**Abordagem STAC-first** (implementada): antes de chamar o Processing API (lento),
consulta o STAC Catalog (~1s) para encontrar a data exata da melhor cena. Em seguida
chama o Processing API com janela de ±1 dia (muito mais rápido que varrer 90 dias).

### Modos de seleção de cena

| Modo | `cena_opcao` | Comportamento |
|---|---|---|
| Menos nublada | `"menos_nublada"` | STAC busca 10 cenas → escolhe a de menor % nuvem |
| Mais atual | `"mais_atual"` | STAC busca 10 cenas → escolhe a mais recente (ignora nuvem) |
| Por data | `"por_data"` | Usa `data_especifica` ("YYYY-MM-DD") diretamente, sem STAC search |

### Evalscripts Sentinel Hub

| Nome | Bandas | Uso |
|---|---|---|
| `EVALSCRIPT_NDVI` | B04 + B08 + SCL | Modo padrão — pixels de nuvem (SCL 3,8,9,10) viram NaN |
| `EVALSCRIPT_NDVI_SEM_MASCARA` | B04 + B08 | Modo mais_atual — todos os pixels calculados, sem filtro SCL |

### Máscara de pixels válidos

```python
# menos_nublada / por_data:
valid_mask_refined = (valid_band == 1) & np.isfinite(ndvi_band)

# mais_atual (aceita pixels com nuvem):
valid_mask_refined = np.isfinite(ndvi_band)
```

Se pixels válidos < `num_zonas * 10`, fallback automático para todos os pixels finitos.

### Parâmetros de `processar_ndvi_talhao()`

```python
processar_ndvi_talhao(
    geojson: dict,          # GeoJSON Polygon do talhão
    num_zonas: int = 3,     # 2-5 zonas de manejo
    data_inicio: str = None,  # ISO — padrão: 90 dias atrás
    data_fim: str = None,     # ISO — padrão: hoje
    cena_opcao: str = "menos_nublada",  # ver tabela acima
    max_cloud_pct: int = 80,  # filtro % máx nuvem no STAC
    data_especifica: str = None,  # "YYYY-MM-DD" — só para por_data
)
# Retorna: {zonas, estatisticas, imagem_base64, periodo, data_imagem, cloud_cover}
```

### Cores e diagnósticos das zonas (3 zonas padrão)

| Zona | Nome | Cor | NDVI típico | Diagnóstico | Recomendação |
|---|---|---|---|---|---|
| 0 | Baixa | `#e74c3c` vermelho | < 0.4 | Vegetação esparsa / estresse hídrico | Dose Alta |
| 1 | Média-Baixa | `#f39c12` laranja | 0.4–0.7 | Bom desenvolvimento vegetativo | Dose Média-Alta |
| 2 | Média | `#27ae60` verde | > 0.7 | Excelente cobertura vegetal | Dose Média |

## Painel web (`/painel`) — Estado e funções principais

### State global (JavaScript)

```javascript
const state = {
    // Cada talhão: {nome, geojson, layer, area, zonasLayer, zonas, estatisticas, dataImagem, cloudCover}
    talhoes: [],
    carLayer: null,
    climaMarker: null,
};
```

**Importante:** cada talhão tem seu próprio `zonasLayer` no mapa — processar NDVI de um talhão
não remove as zonas de outro. O state NÃO tem mais `ultimasZonas` global.

### Funções principais do frontend

| Função | O que faz |
|---|---|
| `processarNDVI(idx)` | Processa NDVI do talhão idx, salva resultado em `state.talhoes[idx]` |
| `processarTodosNDVI()` | Loop em todos os talhões |
| `exibirZonas(idx, zonas, ...)` | Remove zonasLayer anterior do idx, cria novo, chama `atualizarSidebarZonas()` |
| `atualizarSidebarZonas()` | Reconstrói sidebar com TODOS os talhões que têm zonas (agrupados com cabeçalho) |
| `removerTalhao(idx)` | Remove layer do desenho + zonasLayer do mapa, chama `atualizarSidebarZonas()` |
| `toggleCenaOpcao()` | Mostra/oculta filtro de nuvem vs dropdown de datas conforme radio selecionado |
| `buscarCenasDisp()` | Chama `/listar-cenas` e popula dropdown com datas + % nuvem |
| `gerarCroqui()` | Envia `talhoes_lista` (todos com zonas) para `/gerar-croqui` |
| `exportarShapefile()` | Usa zonas do último talhão processado |
| `buscarCAR()` | Chama `/buscar-car` → exibe polígono do imóvel no mapa |
| `adicionarGeoJSON(geojson, filename)` | Importa .shp/.kml/.kmz/.geojson como talhão |

### Tiles do mapa

```javascript
// Google Satellite (maxZoom 21) — cobertura total do Brasil incluindo MT
L.tileLayer("https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", {maxZoom: 21})
// Esri World Imagery tinha buracos em MT — não usar como padrão
```

## Croqui vetorizado (`/gerar-croqui`)

O croqui renderiza **polígonos vetorizados** (geopandas + matplotlib), idêntico ao que aparece
no mapa — não o raster bruto de pixels (que era pixelado). Aceita múltiplos talhões com subplots.

### Payload para múltiplos talhões

```json
{
    "formato": "png",
    "talhoes_lista": [
        {
            "geojson": {...},
            "titulo": "Talhão 1",
            "zonas": {"type": "FeatureCollection", "features": [...]},
            "estatisticas": [...],
            "data_imagem": "30/03/2026",
            "cloud_cover": 2.9
        },
        {...}
    ]
}
```

### Layout de subplots automático

| Qtd talhões | Layout | figsize |
|---|---|---|
| 1 | 1×1 | 12×10 |
| 2 | 1×2 | 22×10 |
| 3 | 1×3 | 30×10 |
| 4+ | grid 2 colunas | 22×(10×linhas) |

**Compatibilidade backward:** aceita também `geojson` + `zonas` + `estatisticas` diretamente
(sem `talhoes_lista`) para chamadas de outros agentes (ex: agente-cpr).

### Fallback raster

Se `zonas` não for fornecido para um talhão, o backend processa NDVI do zero e usa o raster bruto.
Isso é lento (~30-60s) — sempre preferir enviar as zonas já processadas quando disponível.

## Busca CAR / banco-mana / SICAR

O `sicar_client.py` tem 3 funções principais:

### buscar_car_por_codigo(codigo_car)
1. Consulta banco-mana (cache PostgreSQL) — resposta ~ms
2. Fallback: `consultapublica.car.gov.br/publico/imoveis/search?text={codigo}` — sem CAPTCHA, sem SSL issue
3. Cacheia resultado no banco-mana para próximas consultas

### buscar_car_por_localizacao(lat, lng)
- Endpoint: `consultapublica.car.gov.br/publico/imoveis/getImovel?lat=&lng=`
- Retorna o imóvel rural que **contém** aquele ponto (qualquer ponto dentro do polígono funciona)
- HTTP 500/404 = sem imóvel na coordenada (tratado como ValueError, não propagado como erro)
- JSONDecodeError = resposta vazia = sem imóvel (também tratado silenciosamente)
- **Limitação**: API SICAR tem cobertura incompleta — áreas peri-urbanas frequentemente retornam vazio
- Caches resultado no banco-mana automaticamente

### buscar_car_por_cpfcnpj(cpf_cnpj)
- Somente banco-mana (SICAR público **não expõe CPF/CNPJ**)
- Shapefile AREA_IMOVEL do SICAR não inclui campo CPF — confirmado inspecionando o .zip
- Dados MT e GO importados (401k registros) mas todos com cpf_cnpj=null

```python
# Tabela: car_imoveis
# Campos: cod_imovel, cpf_cnpj, uf, municipio, geometria (JSONB com GeoJSON)
# Índices: cod_imovel, cpf_cnpj, uf, municipio
```

**Variável necessária:** `BANCO_MANA_URL` (URL pública: `junction.proxy.rlwy.net:18184`)

## WMS SICAR — limitações críticas

**NÃO usar** `geoserver.car.gov.br` para tiles WMS — SSL SSLV3_ALERT_HANDSHAKE_FAILURE.

O endpoint correto para renderização é:
`consultapublica.car.gov.br/publico/mosaicos/getGeoserverImages`
Layer para imóveis rurais: `sig:consulta_publica_iru` (version 1.3.0, tiled=true, crs=EPSG:3857)

**Porém:** o servidor SICAR retorna **503** para qualquer request sem cookies de sessão autenticada.
Nem proxy Flask com `Referer` correto consegue contornar — SICAR exige cookies do browser.
O overlay WMS foi removido do painel por isso. **Não tentar reimplementar** sem solução de autenticação.

## Integração com agente-cpr

O endpoint `/gerar-croqui` é projetado para o fluxo de CPR:

```python
# No agente-cpr, após gerar o documento Word:
resp = requests.post(f"{AGENTE_AGRO_URL}/gerar-croqui", json={
    "geojson": talhao_geojson,
    "zonas": zonas_geojson,          # opcional mas recomendado
    "estatisticas": estatisticas,     # opcional mas recomendado
    "data_imagem": "30/03/2026",
    "formato": "pdf",
    "titulo": f"Croqui - {nome_fazenda} - Talhão {num}",
})
croqui_pdf = resp.content
# Anexar ao workflow SE via SOAP: newDocument() + newAssocDocument()
```

## Exportar Shapefile (`/exportar-shapefile`)

```json
// Request:
{"zonas": {...GeoJSON FeatureCollection...}, "nome": "talhao_1", "insumo": "Herbicida"}

// Response: ZIP com .shp / .shx / .dbf / .prj (WGS84)
// Atributos: zona, ndvi_medio, area_ha, cor, insumo
// Lib: pyshp (não geopandas — mais leve)
```

## Listar Cenas Sentinel (`/listar-cenas`)

```json
// Request:
{"geojson": {...GeoJSON Polygon...}}

// Response:
{
    "total": 8,
    "cenas": [
        {"data_iso": "2026-04-02", "data_br": "02/04/2026", "cloud_cover": 97.7, "plataforma": "S2B"},
        {"data_iso": "2026-03-30", "data_br": "30/03/2026", "cloud_cover": 2.9, "plataforma": "S2A"},
        ...
    ]
}
// Período buscado: últimos 90 dias. Sem sortby (API Copernicus não suporta) — já retorna desc.
```

## Clima (Open-Meteo)

```
GET /clima?lat=-14.5&lon=-56.8

Retorna: {atual: {temperature_2m, relative_humidity_2m, precipitation, wind_speed_10m, weather_code},
          previsao_7d: [...], historico_30d: {precipitacao_acumulada_mm}}
```

## Como fazer deploy/atualização

```bash
# 1. Clonar repo (só necessário uma vez por sessão)
git clone https://[TOKEN]@github.com/Sementesmana/hiperautomacao-mana.git

# 2. Copiar arquivo(s) modificado(s)
cp /sessions/.../ORQUESTRADOR/agente-agro/app.py hiperautomacao-mana/agente-agro/
cp /sessions/.../ORQUESTRADOR/agente-agro/agente_agro.py hiperautomacao-mana/agente-agro/
cp /sessions/.../ORQUESTRADOR/agente-agro/templates/painel.html hiperautomacao-mana/agente-agro/templates/

# 3. Commit e push
cd hiperautomacao-mana
git add agente-agro/
git commit -m "feat: descrição da mudança"
git push origin main
# Railway detecta e faz deploy automático em ~2 minutos
```

> Gerar token em github.com/settings/tokens — permissão `repo`. Não salvar em memória.

## Dependências de sistema (obrigatório)

```toml
# nixpacks.toml
[phases.setup]
nixPkgs = ["gdal", "proj", "geos"]
```

GDAL, PROJ e GEOS são necessários para rasterio, geopandas e shapely. Build Railway demora
mais que outros agentes por conta dessas dependências (~5-8 min no primeiro deploy).

## APIs externas

### Sentinel Hub (Copernicus Data Space)
- **Token**: OAuth2 `client_credentials` em `identity.dataspace.copernicus.eu`
- **STAC Catalog**: `sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search`
  - ⚠️ Não suporta `sortby` — retorna desc por padrão
- **Processing API**: `sh.dataspace.copernicus.eu/api/v1/process`
- **Tier gratuito**: 30.000 requests/mês
- **Criar credenciais**: dataspace.copernicus.eu → Dashboard → User Settings → OAuth Clients

### banco-mana (PostgreSQL centralizado)
- **URL pública**: `postgresql://postgres:***@junction.proxy.rlwy.net:18184/railway`
- **Variável**: `BANCO_MANA_URL`
- **Tabela CAR**: `car_imoveis` (cod_imovel, cpf_cnpj, uf, municipio, geometria JSONB)

### Open-Meteo
- Gratuito, sem auth, sem limite explícito

## Painel web — estado atual (2026-04-05)

**O que funciona:**
- Busca por código CAR → polígono laranja do imóvel no mapa ✅
- Botão "🌐 Localizar no SICAR oficial →" — abre consultapublica.car.gov.br ✅
- Importar talhão: `.geojson`, `.kml`, `.kmz` ✅ / `.shp` ❌ (não suportado no browser)
- NDVI, croqui, clima, exportar shapefile ✅

**Removido (não funciona):**
- Botão "Clique no mapa para buscar imóvel" — SICAR getImovel tem cobertura incompleta peri-urbana
- Overlay WMS SICAR — requer cookies de sessão (retorna 503 externamente)

**Mensagem quando clique não acha imóvel:**
- Antes: banner vermelho de erro assustador
- Agora: status bar discreta + toast laranja com link direto para o SICAR naquela coordenada

**Gunicorn (Procfile):**
`gunicorn app:app --worker-class gthread --workers 4 --threads 8 --timeout 60`
gthread é necessário para requests paralelos. Timeout 60s (antes era 180s — NDVI pode ser lento).

**Importar talhão aceita arquivos de:**
- GPS apps: Avenza Maps, Google Earth (KML) ✅
- Drone: DJI Terra, Pix4D, DroneDeploy (exportar como KML ou GeoJSON) ✅
- Qualquer GeoJSON com polygon de área ✅

## WhatsApp Bot — integração com agente-agro

No `agente-whatsapp/app.py`, `/webhook-incoming`:
- `LocationMessage` com `location.latitude/longitude` → chama `/buscar-car-por-localizacao` → responde com dados do imóvel
- Texto com regex `[A-Z]{2}-\d{7}-[A-F0-9]{32}` → chama `/buscar-car` → responde com dados
- Ignora mensagens `fromMe=True`
- Variável `AGENTE_AGRO_URL` no Railway do agente-whatsapp

## Erros conhecidos e soluções

| Erro | Causa | Solução |
|---|---|---|
| `Poucos pixels válidos (0)` | Cena com muita nuvem + SCL mascarando tudo | Usar modo "mais atual" ou aumentar `max_cloud_pct` |
| `KMeans: NaN in input` | `valid_mask` não estava sincronizado com `ndvi_band` | Fix: `valid_mask_refined = (valid_band==1) & np.isfinite(ndvi_band)` |
| Tiles "Map data not yet available" | Esri sem cobertura em MT a zoom alto | Fix: trocar para Google Satellite tiles |
| STAC retorna 400 | `sortby` na payload | Fix: remover sortby — API já retorna desc |
| Raster pixelado no croqui | Usava `imagem_base64` (raster bruto) | Fix: usar `gdf_zonas.plot()` com geopandas |
| Zonas somem ao processar 2º talhão | `state.zonasLayer` era global | Fix: `talhao.zonasLayer` por índice |
| `set_aspect("equal")` distorce mapa | Lat brasileira faz graus distorcerem | Fix: `ax.set_aspect("auto")` |
| SICAR getImovel retorna 500 | Sem imóvel nessa coordenada | Tratar como ValueError (não ConnectionError) — fix implementado |
| SICAR getImovel retorna corpo vazio | Coordenada sem propriedade cadastrada | Capturar JSONDecodeError e tratar como "sem imóvel" — fix implementado |
| WMS tiles retornam 503 | SICAR exige cookies de sessão | Não tem fix — WMS overlay removido do painel |
| Gunicorn trava com tiles paralelos | Workers síncronos bloqueados esperando SICAR | Fix: gthread com --workers 4 --threads 8 |

## Regras críticas

- **NUNCA alterar código sem Xayer pedir.** "Verificar" = reportar, não editar.
- **Credenciais são variáveis de ambiente** — nunca hardcode.
- **Deploy via git push** (não `railway up`).
- **Timeout alto**: Sentinel Hub leva 30-90s. Gunicorn configurado com `--timeout 180`.

## Próximas evoluções (backlog)

1. **Statistical API** — série temporal NDVI real (hoje retorna dados simulados)
2. **Integração agente-cpr** — chamar `/gerar-croqui` automaticamente no fluxo CPR
3. **Integração agente-estoque** — NDVI como indicador de produtividade esperada
4. **Alertas via agente-whatsapp** — queda brusca de NDVI → notificação
5. **ADEasy-style**: legenda flutuante no mapa com doses por zona sobrepostas
6. **Taxa Variável vs Fixa** — cálculo de economia + custo em R$/ha
