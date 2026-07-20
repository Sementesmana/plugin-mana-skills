---
name: agente-km
description: >
  PWA mobile de registro de visitas com GPS, foto e cálculo de km para Sementes Maná LTDA.
  Flask + Railway que captura coordenadas no celular, calcula distância Haversine até o ponto-base,
  grava latcampo/lngcampo/kmrodados no SoftExpert e anexa a foto com overlay GPS (cidade, lat/lng, data/hora).
  Use este skill SEMPRE que precisar trabalhar com o agente-km — corrigir bugs do PWA mobile,
  ajustar overlay de GPS na foto, modificar integração SOAP com SE, depurar sessão/token,
  alterar cálculo de distância, ou qualquer coisa relacionada ao registro de visitas de campo.
  Também use quando mencionar: agente-km, registro de visitas, km rodados, foto de visita,
  GPS campo, latcampo, lngcampo, kmrodados, registrovisitas, overlay foto, Haversine.
---

# Agente KM — Registro de Visitas com GPS + Foto

## O que faz
PWA mobile que o vendedor/técnico abre pelo link no processo SoftExpert. Ele captura o GPS do celular,
tira uma foto da visita, e o servidor calcula a distância (Haversine) entre o ponto-base do processo
e o ponto capturado no campo. A foto é salva no SE com overlay de cidade, lat/lng e horário.

## Arquitetura

```
SE processo (latbase/lngbase preenchidos)
  → usuário clica link → GET /app?idprocess=XXX  (abre no celular)
  → Flask lê coords-base via SOAP (fm_ws.php / getTableRecord)
  → Gera token de sessão in-memory (TTL 1h)
  → Renderiza PWA (pwa.html)
  → Usuário captura GPS + tira foto → POST /registrar
  → Flask valida sessão + coords (faixas Brasil)
  → Calcula Haversine server-side
  → Grava campos SE via editEntityRecord (wf_ws.php)
  → Processa foto (resize + EXIF + overlay GPS via Pillow)
  → Reverse geocode Nominatim → cidade/estado
  → Anexa foto ao SE via newAttachment (wf_ws.php)
  → Renderiza sucesso.html com km calculados
```

## Arquivos do projeto

```
agente-km/
├── app.py              — Flask + rotas (/app, /registrar, /health)
├── agente_km.py        — Lógica: SEClient, AgentKm, haversine_km, preparar_foto, overlay GPS
├── config.py           — Variáveis de ambiente via Railway
├── Dockerfile          — python:3.11-slim + libjpeg + fonts-dejavu-core
├── requirements.txt
├── railway.toml
└── templates/
    ├── pwa.html        — PWA mobile (GPS + câmera + submit)
    ├── sucesso.html
    └── erro.html
```

## Variáveis de ambiente (Railway)

| Variável | Valor padrão | Obrigatório |
|---|---|---|
| `SE_URL` | — | ✅ |
| `SE_API_KEY` | — | ✅ |
| `SECRET_KEY` | — | ✅ |
| `SE_ENTITY_ID` | `registrovisitas` | — |
| `SE_ACTIVITY_ID` | `""` | Para newAttachment |
| `SE_FIELD_LAT_BASE` | `latbase` | — |
| `SE_FIELD_LNG_BASE` | `lngbase` | — |
| `SE_FIELD_LAT_CAMPO` | `latcampo` | — |
| `SE_FIELD_LNG_CAMPO` | `lngcampo` | — |
| `SE_FIELD_KM_RODADOS` | `kmrodados` | — |
| `PAINEL_SENHA` | `mana2026` | — |
| `SESSION_TTL` | `3600` | — |
| `FOTO_MAX_PX` | `1400` | — |
| `FOTO_QUALITY` | `82` | — |

## Processo SE associado
- **Processo:** `SM.CV.PR.NE.COM-001`
- **Tabela SE:** `registrovisitas`
- **Link na atividade SE:** `https://agente-km-production.up.railway.app/app?idprocess={idprocess}`

---

## ⚠️ Gotchas críticos — erros já resolvidos (NÃO repetir)

### 1. Gunicorn DEVE ter `--workers 1`
Sessões ficam em dict in-memory (`_sessions`). Com 2+ workers, o POST `/registrar` pode
cair num worker diferente do que criou a sessão → 401 "Sessão expirada".
```dockerfile
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-5000} --workers 1 --timeout 60
```

### 2. Gravar campos SE: usar `editEntityRecord` via `wf_ws.php` + `urn:workflow`
`editAttributeValue` retorna HTTP 200 mas não grava nada em campos de formulário de workflow.
O padrão correto (igual agente-cpr) é:
```python
# wf_ws.php com namespace urn:workflow
xml = '''
<urn:editEntityRecord>
  <urn:WorkflowID>{idprocess}</urn:WorkflowID>
  <urn:EntityID>{entity_id}</urn:EntityID>
  <urn:EntityAttributeList>
    <urn:EntityAttribute>
      <urn:EntityAttributeID>kmrodados</urn:EntityAttributeID>
      <urn:EntityAttributeValue>4.22</urn:EntityAttributeValue>
    </urn:EntityAttribute>
  </urn:EntityAttributeList>
</urn:editEntityRecord>
'''
```

### 3. Campos numéricos SE: separador PONTO, não vírgula
SE retorna erro `"Este valor não respeita o formato do campo [kmrodados]"` se enviar `4,22`.
Usar sempre `f"{km:.2f}"` (ponto como separador decimal).

### 4. newAttachment: usar `urn:workflow` + `WorkflowID` + `ActivityID`
```python
# wf_ws.php com namespace urn:workflow
xml = '''
<urn:newAttachment>
  <urn:WorkflowID>{idprocess}</urn:WorkflowID>
  <urn:ActivityID>{activity_id}</urn:ActivityID>
  <urn:FileName>{filename}</urn:FileName>
  <urn:FileContent>{base64}</urn:FileContent>
</urn:newAttachment>
'''
```
`ActivityID` é obrigatório no SE 3.0. Configurar `SE_ACTIVITY_ID` no Railway.

### 5. PWA Android Chrome — câmera recarrega a página
`capture="environment"` em `<input type="file">` pode causar reload da página no Android Chrome.
Solução: usar `sessionStorage` para persistir lat/lng antes do reload e restaurar no `DOMContentLoaded`.

### 6. `var` em vez de `let` para `fotoBlob`
`let` com TDZ (Temporal Dead Zone) causa `Cannot access fotoBlob before initialization`
em certas sequências de execução no mobile. Usar `var fotoBlob = null`.

### 7. `URL.createObjectURL` trava no Android para fotos grandes
Para fotos 2MB+, setar `img.src = URL.createObjectURL(file)` pode crashar o renderer
do Android Chrome silenciosamente. Solução: não usar preview de imagem, apenas confirmar
o nome/tamanho do arquivo.

### 8. Botão submit: `type="button"` em vez de `type="submit"`
`type="submit"` dispara submit nativo do form simultaneamente ao handler JS,
causando duplo envio e spinner infinito. Usar `type="button"` + fetch manual.

### 9. Cache-Control no-store na rota /app
Sem esse header, o Android reusa a página cacheada (com token expirado):
```python
r = make_response(resp)
r.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
r.headers["Pragma"] = "no-cache"
return r
```

### 10. Emoji no overlay da foto (Pillow)
Pillow com TrueType no Ubuntu não renderiza emoji — aparece quadrado □.
Usar texto puro: `f"{cidade}, {estado}"` sem 📍 ou qualquer emoji.

### 11. Acentos no overlay: instalar fonts-dejavu no Dockerfile
Sem DejaVu, Pillow cai no fallback bitmap que não suporta caracteres acentuados.
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev zlib1g-dev fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
```

---

## Overlay GPS na foto (Pillow)

### Fluxo
```
preparar_foto(bytes, max_px, quality, lat, lng, timestamp)
  → _corrigir_orientacao(img)       # EXIF rotation
  → resize se > max_px
  → _reverse_geocode(lat, lng)      # Nominatim → "Indiara, Goiás"
  → _draw_gps_overlay(img, lat, lng, ts, local)
      → 3 linhas: cidade/estado, lat/lng, data/hora
      → barra semitransparente preta (alpha 170) no rodapé
      → fonte DejaVu Bold (tamanho proporcional: w//45)
      → fallback para bitmap se TrueType não carregar
  → salva JPEG otimizado
```

### Resultado visual
```
Indiara, Goiás
Lat: -17.148650   Lng: -49.996555
24/04/2026 05:45
```

### Reverse geocoding — Nominatim
```python
requests.get(
    "https://nominatim.openstreetmap.org/reverse",
    params={"lat": lat, "lon": lng, "format": "json", "accept-language": "pt"},
    headers={"User-Agent": "agente-km/1.0 (sementesmana@gmail.com)"},
    timeout=5,
)
# Prioridade: city > town > village > municipality
# Fallback silencioso: se timeout/erro, foto vai sem cidade
```

---

## Ler coordenadas-base do SE

`getTableRecord` via `fm_ws.php` busca por `IDPROCESS`:
```python
se.get_table_record("registrovisitas", idprocess)
# Retorna dict com campos em lowercase: {"latbase": "-17.14", "lngbase": "-49.99", ...}
```
Os campos `lat_base` e `lng_base` precisam estar preenchidos no formulário SE antes de
abrir o link no celular.

---

## Cálculo de distância
```python
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1; dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(max(0.0, a)))
```
Calculado **server-side** — nunca confiar no valor vindo do cliente.

---

## Validações de entrada (segurança)

```python
# idprocess — whitelist
IDPROCESS_RE = re.compile(r"^[\w\-\.]{1,120}$")

# Faixas geográficas Brasil
if not (-35.0 <= lat_campo <= 6.0):   raise ValueError("latitude fora do Brasil")
if not (-75.0 <= lng_campo <= -28.0): raise ValueError("longitude fora do Brasil")

# Foto mínima (evita arquivo vazio)
if len(foto_bytes) < 1000: return erro

# Rate limiting
RATE_LIMIT_APP      = "30 per hour"   # /app
RATE_LIMIT_REGISTRAR = "15 per hour"  # /registrar
```

---

## Deploy

```powershell
# Na pasta agente-km
git add <arquivo>
git commit -m "feat/fix: descrição"
git push origin main
# Railway auto-deploya em ~2 min
```

URL produção: `https://agente-km-production.up.railway.app`

### Backup antes de mexer
```powershell
copy agente_km.py agente_km.py.bak
```
Para reverter: `copy agente_km.py.bak agente_km.py`

---

## LGPD
- **Dado tratado:** coordenadas GPS de imóvel rural (dado patrimonial)
- **Base legal:** execução de contrato / interesse legítimo (Art. 7 II/IX)
- **Retenção:** conforme política do processo SE (recomendado 5 anos)
- **Minimização:** apenas lat/lng, km e foto — sem CPF/nome em log
