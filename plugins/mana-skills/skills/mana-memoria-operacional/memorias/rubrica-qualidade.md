---
data: 2026-11-01
origem: máquina-hub (Xayer) — condensado das correções que o Xayer fez ao Claude entre jun e nov/2026
verificado: sim
---

# Rubrica de qualidade: o que conferir antes de abrir o PR

Cada linha é uma correção que já custou retrabalho em produção. Use como
checklist antes do PR e como régua do juiz na revisão adversarial.
Resposta por linha: **ok**, **não se aplica** ou **falhou (e por quê)**.
Linha que falha não segue para PR sem dizer isso na descrição.

## 1. Antes de escrever

- [ ] **Li a nota do agente** (ManaVault `06-Agentes-e-Skills/`) e os ADRs do tema
      (`08-Decisoes/_index.md`). Não reinventei uma decisão já tomada.
- [ ] **Li o contrato, não um exemplo.** Formato de campo, API e ERP vêm da doc
      (há PDFs em `WEBSERVICE WF/`, `DICIONARIO DE DADOS SOFTEXPERT/`). O que for
      inferido está dito como inferência. *Custou 2 deploys no CRE-003.*
- [ ] **Medi a escala do sintoma.** Sumiu um registro: olhar chave e dado. Sumiu o
      bloco inteiro: olhar a fonte compartilhada, não regra de negócio.
- [ ] **Agente novo:** li `novo-agente-mana` E `mana-arquitetura-padrao`; repo privado;
      `.gitignore` antes do 1º commit; pool de conexão no banco-mana desde o dia 1.

## 2. Dados

- [ ] **Falha não vira dado.** Erro da fonte não volta como lista vazia, nem é
      cacheado como sucesso ([falha-nao-vira-dado.md](falha-nao-vira-dado.md)).
- [ ] **Fonte externa é dinâmica.** A cada leitura de DIXI/SA/SE/Protheus, todo campo
      que a fonte traz é reconciliado (cadastro incluso), não só na primeira
      importação. Sem flag "manual vence a fonte". Vazio da fonte não apaga valor conhecido.
- [ ] **Conferi por conjunto, não por contagem** ([verificar-por-conjunto.md](verificar-por-conjunto.md)).
- [ ] **SA:** paginado, sem confiar em `limit=-1`/`total`; sem vínculo por posição
      ([sa-api-mente-listagem-e-limit.md](sa-api-mente-listagem-e-limit.md)).

## 3. Produto (painel, report, alerta)

- [ ] **Report = um produto, duas telas.** Mudou no desktop, mudou no mana-reports
      na mesma tarefa. Regra de negócio no servidor (contrato `/api/report/<id>`),
      nunca `if` no cliente.
- [ ] **Alerta = o recorte que o painel mostra**, na mesma ordem, num relatório só.
- [ ] **Filtro, chip e KPI abrem a quantidade que prometem** (teste contrato × linha).
- [ ] **Vazio honesto.** Tela vazia diz por quê ("nada em aberto — N já tratados"),
      e não parece erro nem "tudo certo".
- [ ] **Coluna que acusa, acusa o certo** (ex.: "sem pedido" não vale para quem não lança pedido).
- [ ] **Embed no SE:** conferido em 1400/900/560 px; sessão por token, não cookie de terceiro.

## 4. Segurança e LGPD

- [ ] **Nenhuma credencial no código** nem no histórico; tudo em env do Railway.
- [ ] **Rota que mexe em dado tem auth no servidor** (senha só no JS não é auth).
- [ ] **Super-sensível nunca vai ao LLM** (PDF Tarken, scred completo com CPF +
      restrição, documento de cliente do comitê).
- [ ] **Pseudonimização proporcional** ao que de fato vai ao LLM: nome de arquivo pede
      CPF/CNPJ/cliente; conteúdo de documento pede todos os nomes vinculados.

## 5. Arquitetura

- [ ] **LLM pelo `mana-llm-gateway`** (alias, chave virtual); nada direto na Anthropic.
- [ ] **WhatsApp pela porta única** do `agente-whatsapp`, com `classe`, `idempotency_key` e `agente`.
- [ ] **IA só no ambíguo.** O que tem resposta certa é código; a IA consulta fonte
      viva como ferramenta, não uma base estática copiada.

## 6. Prova

- [ ] **Existe um teste que FALHA na versão antiga** e passa na nova.
- [ ] **Mudança que vai para produção passou por revisão adversarial**
      (críticos em sessões separadas + juiz); o veredito está na descrição do PR.
- [ ] **Sem diff fantasma de CRLF** ([git-crlf-fantasma-e-checkout.md](git-crlf-fantasma-e-checkout.md)).

## 7. Fechamento

- [ ] **Nota do vault e SKILL.md atualizados no mesmo movimento**; espelho do
      marketplace pelo `_tools/sincronizar_espelhos.py`, nunca à mão
      ([documentacao-a-frente-do-codigo.md](documentacao-a-frente-do-codigo.md)).
- [ ] **Mexeu em skill, habilidade ou SDK?** Os 3 pontos do cockpit foram reportados:
      manifest, card em `plataforma_agentica.py`, SKILL.md no plugin.
- [ ] **Depois do merge, deploy conferido**: commit em produção = commit do `main`
      (`/api/railway/deploys` do monitor) e `/health` 200. Commit não é deploy.
- [ ] **Decisão arquitetural virou ADR**; ideia que ninguém decidiu NÃO entra no vault
      como "pendente" (vai como sugestão na conversa).
