---
name: agente-precificacao
description: >
  Agente de precificação e orçamento de sementes — Sementes Maná LTDA. Flask+Railway+PostgreSQL
  (schema precificacao). Catálogo de cultivares por safra com preços mensais por tier
  (ALTO/MEDIO/BAIXO), desmontagem Royalties+Germoplasma, frete OSRM, TSI, orçamentos com
  aprovação, painel JWT. Use SEMPRE que precisar trabalhar com agente-precificacao — painel HTML,
  endpoints, preços, desmontagem, frete, royalties, catálogo, orçamentos, admin cultivares, upload
  Excel, usuários. Também quando mencionar: precificação, Maná Price, tier de preço, germoplasma,
  royalties, tabela de frete, OSRM, TSI, planilha de preços, cotação de sementes.
---

# Agente Precificação — Sementes Maná

Serviço Flask no Railway para precificação e orçamento de sementes de soja. Gerencia catálogo de
cultivares com preços mensais escalonados por tier (Ouro/Prata/Bronze), desmontagem de preço
(Royalties + Germoplasma editável), cálculo logístico via OSRM, e painel web responsivo com
autenticação JWT e perfis de acesso.

## Infraestrutura

| Item | Valor |
|---|---|
| URL produção | `https://agente-precificacao-sm.up.railway.app` |
| Projeto Railway | `Agente-Precificacao-SM` |
| Repositório | `github.com/Sementesmana/agente-precificacao` (isolado) |
| Branch | `main` |
| Banco | `banco-mana` PostgreSQL — schema `precificacao` + `comum` |
| Painel | `/painel` — autenticação JWT |

## Arquivos Principais

| Arquivo | Descrição |
|---|---|
| `app.py` | Flask backend — ~1200 linhas, todas as rotas API |
| `auth.py` | JWT (PyJWT 2.x), hash SHA256+salt, decorators login_required/perfil_required |
| `db.py` | Pool PostgreSQL (psycopg2), search_path: `precificacao,comum,public` |
| `templates/painel.html` | Frontend completo — Tailwind, Leaflet, jsPDF, ~1200 linhas |
| `requirements.txt` | flask, flask-cors, gunicorn, psycopg2-binary, PyJWT |
| `Procfile` | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120` |
| `railway.toml` | NIXPACKS builder, healthcheck `/health` |
| `banco/criar_admin.py` | Script para criar usuário admin (admin@mana.com / mana2026) |

## Variáveis de Ambiente (Railway)

| Variável | Descrição |
|---|---|
| `BANCO_MANA_URL` | URL pública PostgreSQL banco-mana |
| `JWT_SECRET` | Secret para tokens JWT (padrão: `mana-precificacao-secret-trocar-em-prod`) |
| `TOKEN_EXPIRY_HOURS` | Expiração do token em horas (padrão: 24) |
| `PAINEL_SENHA` | Senha simples do painel (padrão: `mana2026`) |
| `ORIGIN_COORDS` | Coordenadas de origem padrão (Goiânia: `-16.6799,-49.2533`) |

## Autenticação

- **JWT com PyJWT 2.x** — IMPORTANTE: `sub` deve ser `str(id)`, nunca int (PyJWT 2.x é strict)
- **Hash de senha**: `SHA256(f"mana-salt-2026:{senha}")` — definido em `auth.py`
- **Perfis**: `admin` (tudo), `gerente` (catálogo + orçamentos de todos), `vendedor` (só seus orçamentos)
- **Decorators**: `@login_required` (popula `g.usuario`), `@perfil_required("admin", "gerente")`
- **Login**: `POST /api/auth/login` → `{email, senha}` → `{token, usuario}`

## Endpoints da API

Veja o arquivo `references/endpoints.md` para documentação detalhada de cada endpoint.

### Resumo por módulo:

**Auth**: login, me, registrar
**Safra**: safra ativa (tabela `comum.safras`)
**Catálogo**: listar cultivares com filtros (estado, tecnologia, tier, busca, mes_ref), detalhe com preços, filtros disponíveis
**Frete**: listar faixas, calcular por KM
**Logística**: cálculo de rota OSRM com fallback Haversine + frete automático
**TSI**: tratamentos de sementes industriais com preços por mês
**Royalties**: por tecnologia, multiplicadores, por cultivar+estado
**Config**: config_geral + tier_descontos por safra
**Orçamentos**: CRUD completo com itens, duplicação, workflow de status (RASCUNHO→ENVIADO→APROVADO→PEDIDO)
**Admin**: CRUD cultivares com paginação, importação Excel, frete, usuários

## Schema do Banco (precificacao)

### Tabelas principais

```
precificacao.usuarios        — id, nome, email, senha_hash, perfil, ativo, ultimo_login
precificacao.cultivares      — id, safra_id, tecnologia, obtentora, nome, estado, tier,
                               condicao, pme, germoplasma_base, ativo
precificacao.precos          — cultivar_id, mes_ref, ordem, valor
                               UNIQUE(cultivar_id, mes_ref)
precificacao.frete           — km_min, km_max, sem_icms, com_icms
                               UNIQUE(km_min, km_max)
precificacao.royalties       — safra_id, tecnologia, tipo, mes_ref, ordem,
                               valor_por_ha, taxa_acrescimo_mensal
precificacao.royalties_multiplicadores — safra_id, tecnologia, mes_ref, ordem, valor
precificacao.royalties_por_cultivar    — safra_id, estado, cultivar, mes_ref, ordem, valor
precificacao.tsi_tratamentos           — id, codigo, nome, receita, ofertante, ativo, ordem
precificacao.tsi_precos                — tratamento_id, safra_id, mes_ref, ordem, valor_total_bag
precificacao.config_geral              — chave, valor, valor_texto, descricao
precificacao.config_tier_descontos     — safra_id, condicao, tier, percentual_desconto
precificacao.orcamentos      — id, numero, usuario_id, safra_id, cliente_nome, cliente_cnpj,
                               destino_nome, destino_coords, origem_coords, km_estimado,
                               frete_tipo, total_sementes, total_tsi, total_frete,
                               total_geral, status, notas, criado_em, atualizado_em
precificacao.orcamento_itens — id, orcamento_id, cultivar_id, cultivar_nome, tecnologia,
                               obtentora, estado, tier, tsi_tipo, tsi_preco,
                               mes_referencia, preco_unitario, preco_com_tsi,
                               frete_bag, quantidade, subtotal
```

### Tabelas compartilhadas (schema comum)

```
comum.safras      — id, nome, descricao, inicio_em, fim_em, ativa
comum.estados_icms — nome, sigla, percentual_icms, multiplicador
```

## Desmontagem de Preço — Lógica de Mapeamento

A desmontagem separa o preço final em Royalties (fixos) + Germoplasma (editável). Existe um
mapeamento entre o mês de royalties e o mês de preço (pagamento):

| Mês Royalties | Mês de Preço (pagamento) |
|---|---|
| MAIO | A VISTA |
| JUNHO | A VISTA 2 |
| JULHO | MAIO |
| AGOSTO | JUNHO |
| SETEMBRO | JULHO |
| OUTUBRO | AGOSTO |
| NOVEMBRO | SETEMBRO |
| DEZEMBRO | OUTUBRO |
| JANEIRO | NOVEMBRO |
| FEVEREIRO | DEZEMBRO |
| MARÇO | JANEIRO |
| ABRIL | FEVEREIRO |
| MAI/27 | MARÇO/27 |
| JUN/27 | ABRIL/27 |
| JUL/27 | MAIO/27 |

**Fórmula**: `Preço Final = Royalties + Germoplasma`
- Royalties: valor fixo por cultivar+estado+mês (não editável pelo usuário)
- Germoplasma sugerido: `Preço Original (tabela) - Royalties`
- Germoplasma pode ser editado pelo usuário para gerar preço personalizado
- O preço personalizado vai pro carrinho/lote

## Painel Web (templates/painel.html)

### Estrutura de Abas

1. **Catálogo** — Grid de cards com cultivares, filtros (busca, estado, tecnologia, mês), botão incluir no lote
2. **Desmontagem** — Estado pré-selecionado GO, seleção visual de cultivares, tabela Royalties+Germoplasma editável
3. **Admin** (só admin/gerente) — 4 sub-abas:
   - Cultivares & Preços (tabela paginada, toggle ativo, editar preços por mês)
   - Upload Excel (importação de planilha de preços)
   - Tabela de Frete (edição inline de faixas KM)
   - Usuários (CRUD, toggle ativo/inativo)

### Stack Frontend

- Tailwind CSS via CDN, Plus Jakarta Sans font
- Leaflet para mapas (seleção de origem/destino, mini mapa da rota)
- jsPDF + autoTable para exportar PDF de orçamento
- OSRM para cálculo de rota rodoviária real
- Design: `emerald-950` header, cards com medals (Ouro/Prata/Bronze), drawer lateral pro carrinho

### Variáveis de Estado (JavaScript)

```javascript
TOKEN    // JWT string
USER     // {id, nome, email, perfil}
FILTROS  // {estados[], tecnologias[], meses[], tiers[]}
CATALOGO // array de cultivares carregadas
TSI_LIST // tratamentos de semente industrial
CART     // itens do lote/carrinho
FRETE_TYPE  // 'SEM_ICMS' ou 'COM_ICMS'
ROTA     // {km, frete_bag, faixa, metodo}
DESM_CULTIVARES    // cultivares filtradas na desmontagem
DESM_SELECIONADAS  // {cultivar_id: {cultivar, precoMap, royMap, germoCustom}}
```

### Fluxo de Login

1. `POST /api/auth/login` → recebe `{token, usuario}`
2. TOKEN e USER são salvos em variáveis JS (não localStorage)
3. `apiFetch()` envia `Authorization: Bearer {TOKEN}` em todas as chamadas
4. Se `USER.perfil === 'admin'` ou `'gerente'`, mostra aba Admin

## Logística — OSRM + Haversine

1. Usuário define origem (padrão: Goiânia) e destino via inputs ou clicando no mapa Leaflet
2. `POST /api/logistica/rota` tenta OSRM primeiro (`router.project-osrm.org`)
3. Se OSRM falhar, usa fórmula de Haversine com fator ×1.3 para rota rodoviária estimada
4. Com a distância em KM, busca a faixa de frete na tabela `precificacao.frete`
5. O frete/bag é aplicado a todos os itens do carrinho automaticamente

## Workflow de Orçamentos

Status com transições controladas:
```
RASCUNHO → ENVIADO → APROVADO → PEDIDO
     ↓         ↓          ↓
  CANCELADO  CANCELADO  CANCELADO
              ↓
           RASCUNHO (voltar para editar)
```
- Vendedor: cria/edita rascunhos próprios, envia
- Gerente/Admin: aprova, vê todos os orçamentos

## Problemas Conhecidos e Armadilhas

1. **PyJWT 2.x**: `sub` DEVE ser string. Se for int (do PostgreSQL SERIAL), dá `InvalidSubjectError`
2. **Hash de senha**: usa salt fixo `"mana-salt-2026"`. O script `criar_admin.py` DEVE usar o mesmo salt
3. **CORS**: configurado para aceitar origens SE e localhost. Se testar de outro domínio, vai dar erro
4. **Deploy**: `git push origin main` no repo isolado → Railway auto-deploya em ~2 min
5. **DB search_path**: `precificacao,comum,public` — queries podem usar tabelas sem prefixo de schema
6. **Catálogo filtra**: `condicao = 'AGRICULTOR'` e `ativo = true` — cultivares com outra condição não aparecem
7. **Admin frete PUT**: espera array JSON direto `[{km_min, km_max, sem_icms, com_icms}]`, não wrapper

## Deploy

```bash
cd /tmp/agente-precificacao-deploy
git clone https://TOKEN@github.com/Sementesmana/agente-precificacao.git .
# Copiar arquivos atualizados do workspace
cp /path/to/app.py .
cp /path/to/templates/painel.html templates/
git add . && git commit -m "feat: descrição" && git push origin main
# Railway detecta push e deploya em ~2 min
```

## Para mais detalhes

- `references/endpoints.md` — Documentação completa de todos os endpoints com exemplos de request/response
