---
name: agente-km
description: >
  PWA mobile de registro de MÚLTIPLAS visitas/rotas com GPS, foto e cálculo de km para Sementes Maná LTDA.
  Flask + Railway que captura coordenadas no celular, acumula rotas na sessão e envia tudo pro SE
  de uma só vez via botão "Finalizar Visitas do dia". Cada rota tem: lat/lng ini+fim, km (Haversine),
  foto com overlay GPS, geocode automático do ponto de partida (endpartida) e do destino (enddestino),
  e campos manuais partida/destino para o vendedor descrever o trajeto.
  Use este skill SEMPRE que precisar trabalhar com o agente-km — corrigir bugs do PWA mobile,
  ajustar overlay de GPS na foto, modificar integração SOAP com SE, depurar sessão/token,
  alterar cálculo de distância, campos da grid, finalizar visitas, geocode, ou qualquer coisa
  relacionada ao registro de visitas de campo.
  Também use quando mencionar: agente-km, registro de visitas, km rodados, foto de visita,
  GPS campo, latcampo, lngcampo, kmrodados, registrovisitas, overlay foto, Haversine,
  grid de rotas, gridregvisita, sincronizar SE, ordem rota, finalizar visitas,
  partida, destino, endpartida, enddestino, geocode.
---

# Agente KM — Registro de Visitas com GPS + Foto (v3 — Finalizar em Lote)

## O que faz
PWA mobile que o vendedor abre pelo link no processo SoftExpert. Ele registra múltiplas rotas
durante o dia (GPS ini + GPS fim + foto cada rota). As rotas ficam **acumuladas na sessão servidor**
com campos preenchíveis (partida/destino) e endereços geocodificados automaticamente (endpartida/enddestino).
No final do dia, clica **"Finalizar Visitas do dia"** → tudo vai pro SE em lote de uma vez.

## Arquitetura v3 — Acumulação + Finalizar em Lote

```
SE processo (latbase/lnhbase preenchidos)
  → usuário clica link → GET /app?idprocess=XXX
  → Flask lê coords-base via SOAP (fm_ws.php / getTableRecord)
  → Gera token de sessão in-memory (TTL 12h)
  → Renderiza PWA com rotas já na sessão

Por rota:
  → Usuário captura GPS início → POST /registrar-inicial (salva em _pending_initial)
  → Usuário captura GPS fim + foto → POST /registrar-final
      → Haversine km server-side
      → Geocode PARALELO: endpartida + enddestino via Nominatim (ThreadPoolExecutor)
      → Processa foto: resize + EXIF + overlay GPS (fuso America/Sao_Paulo)
      → Salva na sessão: {ordem, km, lat/lng, endpartida, enddestino, foto_bytes, foto_nome}
      → NÃO insere no SE ainda
      → Retorna {ok, km, ordem, endpartida, enddestino} para o PWA

No final do dia:
  → Vendedor preenche campos partida/destino em cada rota (opcionais)
  → Clica "Finalizar Visitas do dia" → POST /finalizar
      → Coleta partida_N e destino_N do form
      → Loop: inserir_rota_grid para cada rota (newChildEntityRecordList)
      → Campos: ordem, lat/lng ini+fim, km, partida, endpartida, destino, enddestino, foto
      → Limpa sessão apenas se 100% das rotas gravaram com sucesso
```

## Arquivos do projeto

```
agente-km/
├── app.py              — Flask: /app, /registrar-inicial, /registrar-final,
│                                /finalizar, /foto, /limpar-sessao, /health
├── agente_km.py        — SEClient, AgentKm, haversine_km, preparar_foto,
│                         _reverse_geocode, _draw_gps_overlay
├── config.py           — Variáveis de ambiente via Railway
├── Dockerfile          — python:3.11-slim + libjpeg + fonts-dejavu-core
├── requirements.txt
├── railway.toml
└── templates/
    └── pwa.html        — PWA mobile (3 steps + lista rotas + Finalizar)
```

## Variáveis de ambiente (Railway)

| Variável | Valor padrão | Notas |
|---|---|---|
| `SE_URL` | — | ✅ obrigatório |
| `SE_API_KEY` | — | ✅ obrigatório |
| `SECRET_KEY` | — | ✅ obrigatório |
| `SE_ENTITY_ID` | `registrovisitas` | tabela pai |
| `SE_GRID_ID` | `gridregvisita` | grid de rotas |
| `SE_RELATIONSHIP_ID` | `gridvisitaxvisi` | relação pai→grid |
| `SE_FIELD_LAT_BASE` | `latbase` | — |
| `SE_FIELD_LNG_BASE` | `lnhbase` ⚠️ | typo no SE, com H |
| `SESSION_TTL` | `43200` (12h) | — |
| `FOTO_MAX_PX` | `1400` | px max da foto |
| `FOTO_QUALITY` | `82` | qualidade JPEG |

> ⚠️ **`lnhbase` (com H)** — typo no cadastro SE. Nunca corrigir para `lngbase`.

## Processo SE

- **Processo:** `SM.CV.PR.NE.COM-001`
- **Tabela pai:** `registrovisitas`
- **Grid:** `gridregvisita` (relação `gridvisitaxvisi`)
- **Link:** `https://agente-km-production.up.railway.app/app?idprocess={idprocess}`

---

## Campos da grid SE (gridregvisita)

| Campo SE | Tipo | Origem |
|---|---|---|
| `ordem` | Int | Calculado (len sessão + 1) |
| `latitudeini` | Decimal | GPS celular |
| `longitudeini` | Decimal | GPS celular |
| `latitudefim` | Decimal | GPS celular |
| `longitudefim` | Decimal | GPS celular |
| `kmrodado` | Decimal | Haversine server-side |
| `partida` | Texto | Manual pelo vendedor no app |
| `endpartida` | Texto | Geocode automático do lat_ini/lng_ini |
| `destino` | Texto | Manual pelo vendedor no app |
| `enddestino` | Texto | Geocode automático do lat_fim/lng_fim |
| `fotovisita` | Arquivo | JPEG processado (overlay GPS) |

---

## ⚠️ Limitação crítica: SE SOAP ignora filtro IDPROCESS na grid

```python
# SE SOAP getTableRecord com filtro IDPROCESS funciona para a tabela pai (registrovisitas)
# MAS para grid (gridregvisita) retorna TODOS os registros de TODOS os processos
# → Contaminação cruzada: processo 000332 vazio mostraria rotas do 000330/000331

# SOLUÇÃO DEFINITIVA: desabilitar leitura de grid via SOAP, usar sessão como fonte da verdade
def ler_registros_grid_se(self, grid_id, idprocess):
    log.info("filtro SE não confiável, retornando []")
    return []  # sessão in-memory (TTL 12h) é a fonte de verdade

def contar_registros_grid(self, grid_id, idprocess):
    return 0   # mesma razão
```

> A sessão in-memory (12h TTL) cobre qualquer dia normal de trabalho.
> Railway restart zera as sessões — risco aceitável (raro).

---

## Geocode reverso — _reverse_geocode

Usa Nominatim (OpenStreetMap) com `zoom=18` para nível de rua:

```python
from concurrent.futures import ThreadPoolExecutor

# Em registrar_final: geocoda AMBOS os pontos em paralelo (~5s max em vez de 10s)
with ThreadPoolExecutor(max_workers=2) as pool:
    fut_ini = pool.submit(_reverse_geocode, lat_ini, lng_ini)
    fut_fim = pool.submit(_reverse_geocode, lat_fim, lng_fim)
    endpartida = fut_ini.result()
    enddestino = fut_fim.result()
```

Formato retornado: `"Rod. BR-163, Zona Rural, Sorriso - MT"`
ou em área urbana: `"Rua das Acácias, 123, Centro, Cuiabá - MT"`

Lógica de montagem:
1. Via (`road` / `path` / `track` / `highway`) + número
2. Bairro (`suburb` / `neighbourhood` / `district`) ou "Zona Rural"
3. Município (`city` / `town` / `village` / `municipality`)
4. UF (via mapa de estados ou `state_code`)

---

## Fuso horário na foto

```python
from zoneinfo import ZoneInfo
_SP = ZoneInfo("America/Sao_Paulo")

# Em registrar_final:
timestamp = datetime.now(_SP).strftime("%d/%m/%Y %H:%M")
# Railway roda em UTC — sem ZoneInfo a foto mostraria UTC no overlay
```

---

## Endpoint /foto — thumbnail no app

```python
@app.route("/foto")
def foto():
    token = request.args.get("token", "")
    ordem = int(request.args.get("ordem", ""))
    sessao = _sessions.get(token)
    rota = next((r for r in sessao["rotas"] if r["ordem"] == ordem), None)
    return Response(rota["foto_bytes"], mimetype="image/jpeg",
                    headers={"Cache-Control": "no-store"})
```

No PWA: `<img src="/foto?token=SESSION_TOKEN&ordem=N">` com fallback `onerror` para ✅.

---

## Endpoint /finalizar — batch insert

```python
@app.route("/finalizar", methods=["POST"])
def finalizar():
    # Coleta partida_N e destino_N do form
    for r in rotas:
        r["partida"] = request.form.get(f"partida_{r['ordem']}", "")
        r["destino"] = request.form.get(f"destino_{r['ordem']}", "")

    resultado = agent.finalizar_visitas(idprocess, rotas)

    if resultado["ok"]:
        sessao["rotas"] = []  # limpa sessão só se 100% OK
    # Se erros parciais: sessão mantida, frontend mostra quais ordens falharam
```

---

## Inserção na grid (inserir_rota_grid) — XML SOAP correto

```python
# wf_ws.php + namespace urn:workflow + MainEntityID + ChildRelationshipID
xml = """
<urn:newChildEntityRecordList>
  <urn:WorkflowID>{idprocess}</urn:WorkflowID>
  <urn:MainEntityID>registrovisitas</urn:MainEntityID>
  <urn:ChildRelationshipID>gridvisitaxvisi</urn:ChildRelationshipID>
  <urn:EntityRecordList>
    <urn:EntityRecord>
      <urn:EntityAttributeList>
        <urn:EntityAttribute><urn:EntityAttributeID>ordem</urn:EntityAttributeID>
          <urn:EntityAttributeValue>{ordem}</urn:EntityAttributeValue></urn:EntityAttribute>
        <!-- latitudeini, longitudeini, latitudefim, longitudefim, kmrodado -->
        <!-- partida, endpartida, destino, enddestino -->
      </urn:EntityAttributeList>
      <urn:EntityAttributeFileList>
        <urn:EntityAttributeFile>
          <urn:EntityAttributeID>fotovisita</urn:EntityAttributeID>
          <urn:FileName>rota_1_000344_xxx.jpg</urn:FileName>
          <urn:FileContent>{base64}</urn:FileContent>
        </urn:EntityAttributeFile>
      </urn:EntityAttributeFileList>
    </urn:EntityRecord>
  </urn:EntityRecordList>
</urn:newChildEntityRecordList>
"""
```

---

## Atualizar campo pai (atualizar_campo_pai)

```python
# CORRETO: editEntityRecord via wf_ws.php + urn:workflow (usa WorkflowID diretamente)
# ERRADO:  editAttributeValue via fm_ws.php → retorna HTTP 500 em campos de workflow

xml = """
<urn:editEntityRecord>
  <urn:WorkflowID>{idprocess}</urn:WorkflowID>
  <urn:EntityID>registrovisitas</urn:EntityID>
  <urn:EntityAttributeList>
    <urn:EntityAttribute>
      <urn:EntityAttributeID>{field_id}</urn:EntityAttributeID>
      <urn:EntityAttributeValue>{value}</urn:EntityAttributeValue>
    </urn:EntityAttribute>
  </urn:EntityAttributeList>
</urn:editEntityRecord>
"""
# endpoint: WF_WS = "/apigateway/se/ws/wf_ws.php"
```

---

## ⚠️ Gotchas críticos — erros já resolvidos

### 1. Gunicorn DEVE usar `--workers 1`
Sessões ficam em dict in-memory. Com 2+ workers, o token de uma requisição
pode cair num worker diferente → 401 "Sessão expirada".
```
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 60
```

### 2. `editAttributeValue` via `fm_ws.php` retorna HTTP 500 para campos de workflow
Usar sempre `editEntityRecord` via `wf_ws.php` com namespace `urn:workflow`.

### 3. Grid SE ignora filtro IDPROCESS
`getTableRecord` com filtro IDPROCESS funciona para tabela pai mas ignora para grid.
Resultado: todos os registros de todos os processos são retornados.
**Solução:** sessão in-memory como única fonte de verdade. Métodos retornam `[]` e `0`.

### 4. Campos numéricos: separador PONTO
SE retorna `"Este valor não respeita o formato do campo"` com vírgula.
Sempre usar `f"{km:.2f}"` e `.replace(",", ".")` ao ler do formulário.

### 5. `lnhbase` com H (não `lngbase`)
Typo no cadastro do SE. Variável `SE_FIELD_LNG_BASE=lnhbase`. Nunca alterar.

### 6. PWA Android Chrome — câmera recarrega a página
`capture="environment"` pode causar reload no Android Chrome.
**Solução:** salvar lat/lng no `sessionStorage` antes do reload; restaurar em `onFotoSelecionada`.

### 7. `var` em vez de `let` para variáveis do PWA
`let` com TDZ causa erros em alguns mobile browsers.
Usar `var fotoBlob = null`, `var iniLat = null`, etc.

### 8. Emoji no overlay da foto
Pillow com TrueType Ubuntu não renderiza emoji. Usar texto puro no overlay (sem 📍).
Emoji só no HTML do PWA (não na imagem).

### 9. Acentos no overlay: instalar fonts-dejavu no Dockerfile
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev zlib1g-dev fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
```

### 10. Fuso horário: Railway roda em UTC
Sem `ZoneInfo("America/Sao_Paulo")`, o overlay da foto mostra horário UTC.
Sempre usar `datetime.now(_SP)` onde `_SP = ZoneInfo("America/Sao_Paulo")`.

### 11. `type="button"` em botões do form
`type="submit"` causa duplo envio. Usar `type="button"` + fetch manual.

---

## Overlay GPS na foto

```
preparar_foto(bytes, max_px, quality, lat, lng, timestamp)
  → _corrigir_orientacao(img)    # EXIF rotation (celular)
  → resize se > max_px
  → _draw_gps_overlay(img, lat, lng, ts, local)
      → 3 linhas rodapé: cidade/estado · lat/lng · data-hora
      → barra semitransparente preta (alpha 170)
      → fonte DejaVuSans-Bold, tamanho proporcional (w//45)
  → JPEG otimizado

# local vem de _reverse_geocode(lat_fim, lng_fim)
# timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
```

Resultado na foto:
```
Rua Los Angeles, Jardim Califórnia, Cuiabá - MT
Lat: -15.624776   Lng: -56.071310
27/04/2026 12:53
```

---

## Sessão in-memory — estrutura

```python
_sessions = {
    "token_32bytes": {
        "idprocess": "000344",
        "expires": time.time() + 43200,
        "rotas": [
            {
                "ordem":      1,
                "km":         0.1,
                "lat_ini":    -15.62329,
                "lng_ini":    -56.07027,
                "lat_fim":    -15.62387,
                "lng_fim":    -56.07105,
                "endpartida": "Rua Los Angeles, Centro, Cuiabá - MT",
                "partida":    "Escritório Cuiabá",     # manual
                "enddestino": "Rua Sete, Jardim Califórnia, Cuiabá - MT",
                "destino":    "Jardin california",     # manual
                "foto_bytes": b"...",   # JPEG processado
                "foto_nome":  "rota_1_000344_1234.jpg",
            }
        ]
    }
}

_pending_initial = {
    "000344": {"lat_ini": -15.62, "lng_ini": -56.07, "ordem": 1}
}
```

---

## Deploy

```powershell
# Remover locks se necessário
Remove-Item ".git\index.lock" -ErrorAction SilentlyContinue
Remove-Item ".git\HEAD.lock"  -ErrorAction SilentlyContinue

git add <arquivo>
git commit -m "feat: descrição"
git push origin main
# Railway auto-deploya em ~2 min
```

URL: `https://agente-km-production.up.railway.app`

---

## LGPD

- **Dado tratado:** coordenadas GPS de imóvel rural + foto da visita
- **Base legal:** execução de contrato / interesse legítimo (Art. 7 II/IX)
- **Retenção:** conforme política do processo SE (recomendado 5 anos)
- **Minimização:** apenas lat/lng, km e foto — sem CPF/nome em log
- **Foto:** contém lat/lng visível no overlay — não compartilhar fora do processo SE
