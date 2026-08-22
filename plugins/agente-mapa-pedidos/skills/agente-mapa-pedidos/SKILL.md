---
name: agente-mapa-pedidos
description: Mapa de atuação comercial da Sementes Maná LTDA (painel N2, produção) — onde a Maná vende soja, por município. Flask + Leaflet + Chart.js + Alpine no Railway, sem banco próprio: lê pedidos do Simple Agro pelo lake agro.lake_pedidos_raw do banco-mana (fonte única anti-452, do agente-agro) com fallback SA ao vivo e cache de 30min. Agrega por município (volume, faturamento, produtores, cultivar dominante, top clientes), classifica o município pela faixa do MAIOR cliente (top >100 ton, médio 10-100, pequeno <10) e resolve coordenadas por JSON local + Nominatim, com fila de pendentes. Filtros multi-select (safra, UF, cultivar, status, vendedor), toggle TON/BAG e comparativo entre 2 safras. LGPD: senha no painel, CPF/CNPJ mascarado. Use SEMPRE no agente-mapa-pedidos — GeoJSON, agregação por município, coordenadas, faixas de cliente, comparativo de safras, filtros, cache SA. Também quando mencionar: mapa comercial, /api/mapa, /api/mapa-comparativo, /api/pendentes, coords_municipios.json, lake_pedidos_raw.
---

# agente-mapa-pedidos — Mapa Comercial (V1 municipal)

> **Painel N2, produção** · URL: `https://agente-mapa-comercial-production.up.railway.app` — **atenção: o serviço no Railway se chama `mapa-comercial`, o repo se chama `mapa-pedidos`.**

## O que é

Painel Leaflet que responde "**onde a Maná vende soja**": círculos por município, tamanho proporcional ao volume, cor pela faixa do maior cliente daquela praça. Hover mostra top clientes, cultivar dominante, faturamento e número de produtores.

## Pipeline

```
Simple Agro (/api/orders)
   └─ sa_client → lake agro.lake_pedidos_raw (banco-mana) · fallback SA ao vivo · cache 30min
        └─ agregador.py  → consolida por município (cliente.cidade + cliente.estado)
             └─ coords.py → lookup em coords_municipios.json; se faltar, Nominatim (1 req/s)
                  └─ /api/mapa → GeoJSON → painel.html (Leaflet + Chart.js + Alpine)
```

**O lake é a defesa contra o 452**: uma chamada ao SA por safra a cada 30 min pra empresa toda, em vez de cada painel batendo no ERP. Sem `BANCO_MANA_URL` o agente cai no fluxo SA direto (fail-soft); se o SA falhar 3 vezes e não houver lake, aí sim erra explicitamente.

## Faixas de cliente (cor do município)

| Faixa | Volume/safra | Cor |
|---|---|---|
| Top | > 100 ton | verde escuro `#1D6B3E` |
| Médio | 10–100 ton | verde claro `#2E8B57` |
| Pequeno | < 10 ton | ouro `#B8860B` |

A faixa do município é a do **maior cliente** dele — não a soma. Mudar isso muda a leitura do mapa inteiro.

## Endpoints

| Rota | Auth | O que faz |
|---|---|---|
| `GET /health` | — | status + `coords.stats()` |
| `GET /painel` | `?senha=` | painel Leaflet |
| `GET /api/mapa` | senha | GeoJSON agregado — aceita `safras=X,Y,Z` (multi) ou `safra_id=` (compat), `uf`, `cultivar`, `status`, `vendedor` |
| `GET /api/mapa-comparativo` | senha | compara 2 safras classificando cada cliente em **6 comportamentos** |
| `GET /api/opcoes`, `/api/safras` | senha | valores para os dropdowns / safras disponíveis |
| `GET /admin/coords`, `/api/pendentes` | senha | municípios sem coordenada |
| `POST /api/coord` | `ADMIN_TOKEN` | coordenada manual |
| `GET/POST /api/refresh` | `ADMIN_TOKEN` | força refresh do cache SA (aceita `safra_id` seletivo) |
| `GET /api/debug-sa` | senha | schema do 1º order + flatten + agregação (diagnóstico) |

## Variáveis de ambiente

Obrigatórias (fail-fast): `SA_BASE_URL`, `SA_USERNAME`, `SA_PASSWORD`, `SA_SAFRA_ID`, `SA_GRUPO_ID`, `PAINEL_SENHA`.
Opcionais: `BANCO_MANA_URL` (lake), `ADMIN_TOKEN`, `CACHE_TTL` (1800), `NOMINATIM_URL`, `NOMINATIM_USER_AGENT`.
IDs: safra 25/26 `679135f95feb17003584dc27` · 26/27 `69a5d85cae03f50036ee2531` · grupo Soja `610a8b743829fd00385c48c9`.

## LGPD

Painel com senha · CPF/CNPJ mascarado em log e na API (`cliente_cnpj_masked`) · `cliente_hash` = MD5 não-reversível dos 6 primeiros · cache só em memória · razão social visível porque o painel é interno.

## Drift conhecido (corrigir ao mexer)

- O **README diz "Sem PostgreSQL"** — falso desde que o lake entrou (`agro.lake_pedidos_raw`, `psycopg2` no requirements). `BANCO_MANA_URL` não está documentada nem no README nem no `.env.example`.
- O README **não lista** `/api/mapa-comparativo`, `/api/safras` e `/api/debug-sa`.
- V2 (CAR) depende de popular `car_imoveis.cpf_cnpj`, que hoje é nulo — ver `ManaVault/00-Inbox/drift-car-cpf-cnpj-null.md`.

## Deploy

`git push` → Railway (NIXPACKS, healthcheck `/health`, gunicorn 1 worker/timeout 120). Nunca `railway up`. Cuidado com **Nominatim 429** ao resolver muitas coordenadas de uma vez — o limite é 1 req/s.
