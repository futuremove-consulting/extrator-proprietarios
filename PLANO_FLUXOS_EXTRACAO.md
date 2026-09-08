# Plano de Fluxos de Extração — Extrator Proprietários + PilotCRM

**Versão:** 1.0
**Data:** 2026-09-08
**Responsável:** CPTO
**Princípio ordenador:** um fluxo por vez — o próximo só inicia quando o anterior estiver **operando** (Done), não apenas codificado.

---

## 0. Definições de Ready e Done (contrato de qualidade)

> **Regra:** Ready e Done são definidos por **operação com dados reais**, nunca por "código escrito". Código sem execução validada fim a fim não conta como progresso.

### 0.1 Ready — "posso executar o fluxo agora"

Checklist obrigatório antes de iniciar qualquer fluxo:

| # | Item | Evidência |
|---|------|-----------|
| R1 | agent-browser CLI instalada, sessão nomeada persistente funcionando | `agent-browser open` + snapshot OK |
| R2 | Credenciais da fonte válidas (login manual confirmado na semana) | print/log do login |
| R3 | Cota/saldo da fonte disponível para o teste | saldo antes/depois registrado |
| R4 | API do extrator rodando (`extrator-api`) e CRM com `EXTRATOR_API_URL` apontando | `curl /healthz` OK |
| R5 | Seletores da fonte calibrados e salvos em `selectors.json` da fonte | snapshot de calibração arquivado |
| R6 | Endereços-piloto definidos: 1 rico (centenas de registros), 1 médio, 1 sem dados | lista no plano de teste |
| R7 | Guard-rail de crédito ativo: `--max-consultas` por execução + aprovação humana para lote pago | `aprovacao.json` (padrão sondar_cotas) |
| R8 | Custo por ação confirmado (listagem/detalhe) — sondado, não estimado | `custos_verificados.json` |

### 0.2 Done — "o fluxo está operando fim a fim"

Checklist obrigatório para encerrar qualquer fluxo:

| # | Item | Evidência |
|---|------|-----------|
| D1 | Execução fim a fim com dados reais, **≥2 vezes, em dias diferentes** | manifest NDJSON + logs de 2 execuções |
| D2 | Persistência correta no Supabase: contato + imóvel + `crm_property_sources` + vínculo de papel | registros consultáveis |
| D3 | Idempotência provada: re-executar o mesmo endereço **não duplica nada** | contagem antes/depois idêntica |
| D4 | Dados visíveis no frontend: `/crm/properties/captados` (e `/crm/captacao` quando aplicável) | screenshot |
| D5 | Créditos gastos registrados e ≤ orçado; divergência explicada | relatório de créditos da execução |
| D6 | Interrupção no meio (browser morto/timeout) retoma por checkpoint **sem retrabalho pago** | teste de kill + retomada |
| D7 | Runbook validado: operador não-desenvolvedor executa sozinho seguindo o documento | execução assistida → não assistida |
| D8 | Suíte de testes do pipeline verde (pytest/vitest) | CI/local |
| D9 | Falha com sessão expirada → relogin automático ou erro claro e acionável | teste forçado |

**Saída de um fluxo Done:** comando único documentado que qualquer operador roda; dados reais no CRM; evidências arquivadas.

---

## 1. Visão geral e ordem de execução

| Ordem | Fluxo | Fonte | Entrega | Esforço est. |
|-------|-------|-------|---------|--------------|
| 1 | **Fluxo 1 — Simples EEmóvel** | EEmóvel | extração 1 fonte → CRM | 2–3 dias |
| 2 | **Fluxo 2 — Simples Fisgar** | Fisgar | extração 1 fonte → CRM | 3–4 dias |
| 3 | **Fluxo 3 — Simples Captei** | Captei | extração 1 fonte → CRM | 3–4 dias |
| 4 | **Fluxo 4 — Completo sequencial** | 3 fontes | cascata + enriquecimento incremental + base única | 6–8 dias (incl. telas 6.9) |

---

## 2. F0 — Fundação compartilhada (pré-requisito dos 4 fluxos)

**Objetivo:** eliminar dependências repetidas — tudo que os 4 fluxos usam em comum, validado uma vez.

**Etapas:**

| # | Etapa | Resultado |
|---|-------|-----------|
| F0.1 | Inventario CLI: `agent-browser --help`, sessão nomeada, cookies persistidos | R1 satisfeito |
| F0.2 | Cofre de credenciais: env ou credential store (CRM) para as 3 fontes; login manual testado | R2 |
| F0.3 | Executar **Sondador de Cotas** (P1–P5) por fonte → `custos_verificados.json` | R8 |
| F0.4 | Subir stack: `extrator-api` (:8000) + CRM (dev) + `EXTRATOR_API_URL` | R4 |
| F0.5 | Definir endereços-piloto (Marc Chagall 397 + 2 variações, 1 sem dados) | R6 |
| F0.6 | Template de runbook por fonte + relatório de créditos padronizado | base de D5/D7 |

**Done do F0:** R1–R8 todos verdes com evidência arquivada. Não entrega feature — entrega **capacidade de operar**.

---

## 3. Fluxo 1 — Simples EEmóvel (extração de uma fonte → CRM)

### 3.1 Objetivo

Operador digita um endereço no PilotCRM, escolhe EEmóvel e recebe a lista de proprietários/moradores com contato; aprova; dados ficam no Supabase e visíveis na lista de imóveis captados.

### 3.2 Arquitetura do fluxo (implementada em M0–M3, falta operar)

```
/crm/captacao (input endereço, fonte EEmóvel, busca ao vivo)
  → POST /api/crm/captacao/search {forceLive}
  → POST extrator:8000/api/v1/extract {address, fontes:["eemovel"]}
  → ExtractorService → EEmovelAgent → runner.py batch-json (agent-browser)
  → ResultsTabs (revisão humana) → persist
  → Supabase: crm_contacts + crm_properties + crm_property_sources + crm_person_property_roles
  → /crm/properties/captados
```

### 3.3 Etapas restantes

| # | Etapa | Tipo |
|---|-------|------|
| 1.1 | Calibração live: `runner.py live --calibrate` → ajustar `selectors.json` (login, busca, listagem, detalhe) | operação |
| 1.2 | Execução piloto CLI: `live --endereco "Rua Marc Chagall, 397" --max-consultas 3` | operação |
| 1.3 | Corrigir o que a calibração revelar (parse de linhas, navegação detalhe, back) | código sob demanda |
| 1.4 | E2E pelo CRM: busca ao vivo → revisão → persist → conferir Supabase e frontend | operação |
| 1.5 | Teste de idempotência: re-executar mesmo endereço; contagens antes/depois | operação |
| 1.6 | Teste de resiliência: matar o browser no meio; retomada por checkpoint | operação |
| 1.7 | Runbook EEmóvel (comando único + solução de problemas) validado por operador | operação |

### 3.4 Ready específico

R1–R8 + credenciais EEmóvel (email/senha) no ambiente + saldo ≥ 10 consultas.

### 3.5 Done específico (além de D1–D9)

- ≥ 2 endereços-piloto extraídos com contatos reais persistidos;
- classificação correta: com contato → `proprietario` (confidence 0.9); sem contato → `possivel_morador`;
- `/crm/properties/captados` exibe o imóvel com badge EEmóvel e proprietários;
- orçamento de crédito respeitado (listagem 1 + N detalhes ≤ N+1);
- **frontend 11.2 operando**: erros acionáveis + aviso de custo estimado, usados na execução real.

### 3.6 Riscos específicos

| Risco | Mitigação |
|-------|-----------|
| Seletores da listagem diferentes do previsto | modo `calibrate` + `selectors.json` sem tocar no código |
| Sessão expira entre execuções | perfil/cookies persistidos + relogin automático no `garantir_login` |
| Anti-bot em uso intenso | ritmo humanizado, cota diária baixa, sessão persistida |

---

## 4. Fluxo 2 — Simples Fisgar (extração de uma fonte → CRM)

**Só inicia após Fluxo 1 Done.**

### 4.1 Objetivo

Mesmo contrato do Fluxo 1 com a fonte Fisgar: endereço → listagem de proprietários → modal por registro (CPF/RG, referência DOM, tel:/mailto:) → CRM. Fisgar é a fonte de **identidade forte** (CPF) — o contato phone/email costuma ser mais raro; o valor é enriquecer a base com documento.

### 4.2 Arquitetura do fluxo

```
/crm/captacao (fonte Fisgar, busca ao vivo)
  → POST /api/crm/captacao/search {forceLive}
  → POST extrator:8000/api/v1/extract {address, fontes:["fisgar"]}
  → ExtractorService → FisgarAgent → fisgar/runner.py batch-json (agent-browser)  [NOVO]
  → revisão → persist → Supabase → /crm/properties/captados
```

Auth no webhook S2-1: `query_key` (credencial tipo `?key=`) — já suportado.

### 4.3 Etapas

| # | Etapa | Tipo |
|---|-------|------|
| 2.1 | Criar `agentes/fisgar/runner.py` clonando o padrão do runner EEmóvel (calibrate/live/batch-json/mock-input), reaproveitando `AgentBrowser` genérico — extrair a classe para `agentes/comum/browser_cli.py` | código |
| 2.2 | Calibração Fisgar: login, busca, listagem, **abertura do modal por registro** e extração (CPF/RG via regex, tel via `tel:`, email via `mailto:`, `dom_reference`) | operação + código |
| 2.3 | Contador de modais consumidos por execução (1 crédito/modal) integrado ao relatório de créditos; guard-rail `--max-consultas` default 10 | código |
| 2.4 | `FisgarAgent.extract_listing` delega ao runner (padrão `FISGAR_BROWSER_ENABLED=1`) + `map_to_canonical` com Address/cpf/confidence (espelhar EEmóvel) | código |
| 2.5 | E2E pelo CRM + idempotência + resiliência + runbook Fisgar | operação |

### 4.4 Ready específico

R1–R8 + credenciais Fisgar + **saldo ≥ 15 modais** (250/mês) + custo por modal sondado (P4).

### 4.5 Done específico

- ≥ 2 endereços-piloto com registros Fisgar persistidos;
- CPF (quando presente no modal) armazenado e visível no contato;
- idempotência via `source_record_id` (record_key) provada;
- orçamento: 1 listagem + N modais ≤ N+1 créditos;
- **frontend 11.2 operando**: CPF forte x mascarado visível na revisão, usado na execução real.

### 4.6 Riscos específicos

| Risco | Mitigação |
|-------|-----------|
| Modal custa 1/250 por registro — esgotar cota rápido | guard-rail + ordem: modal só para registros priorizados; listing-only por padrão no fluxo completo |
| Modal com interação complexa (scroll/abas) | calibrate + checkpoints por registro |
| CPF mascarado no modal | registrar como veio; CPF forte só quando completo (validador dígito) |

---

## 5. Fluxo 3 — Simples Captei (extração de uma fonte → CRM)

**Só inicia após Fluxo 2 Done.**

### 5.1 Objetivo

Mesmo contrato com a fonte Captei — a fonte de **qualidade de WhatsApp** (validação nativa) e dados de contato de melhor qualidade. Saldo escasso (capcoins pré-pago): a operação é **cirúrgica**, com guard-rail de aprovação humana obrigatório por lote.

### 5.2 Arquitetura do fluxo

```
/crm/captacao (fonte Captei, busca ao vivo)
  → POST /api/crm/captacao/search {forceLive}
  → POST extrator:8000/api/v1/extract {address, fontes:["captei"]}
  → ExtractorService → CapteiAgent → captei/runner.py batch-json (agent-browser)  [NOVO]
  → revisão → persist → Supabase → /crm/properties/captados
```

Auth no webhook S2-1: `headers` (Token + User-Key) — já suportado.

### 5.3 Etapas

| # | Etapa | Tipo |
|---|-------|------|
| 3.1 | `agentes/captei/runner.py` no padrão comum (AgentBrowser compartilhado) | código |
| 3.2 | Calibração Captei: login, saldo de capcoins visível, busca, listagem, modal com **"Validar WhatsApp"** | operação + código |
| 3.3 | Leitura do saldo de capcoins antes/depois embutida no relatório de créditos (auditoria por execução) | código |
| 3.4 | Aprovação humana obrigatória: execução `live` exige `--aprovacao aprovacao.json` (padrão sondar_cotas; sem aprovação → exit 2 e log de auditoria) | código |
| 3.5 | `CapteiAgent.extract_listing` delega ao runner (`CAPTEI_BROWSER_ENABLED=1`) + map_to_canonical com confidence/status WhatsApp nativo | código |
| 3.6 | E2E pelo CRM + idempotência + resiliência + runbook Captei | operação |

### 5.4 Ready específico

R1–R8 + credenciais Captei (Token/User-Key) + **saldo capcoins ≥ 20** + política de gasto aprovada (quantos capcoins por execução).

### 5.5 Done específico

- ≥ 2 endereços-piloto com registros Captei persistidos;
- WhatsApp validado nativo refletido em `whatsappValidation` do ExtractedOwner e no CRM;
- toda execução `live` com aprovação registrada (auditoria sem exceção);
- orçamento de capcoins por execução respeitado e registrado;
- **frontend 11.2 operando**: diálogo de aprovação com orçamento, usado na execução real (quem aprovou fica no relatório).

### 5.6 Riscos específicos

| Risco | Mitigação |
|-------|-----------|
| Capcoins escassos (reposição cara) | uso cirúrgico: no fluxo completo, Captei só entra no delta final |
| Gasto acidental | aprovação humana obrigatória + leitura de saldo antes/depois |
| Capcoins x cota mensal (modelo ambíguo) | resolver com P2 do Sondador de Cotas antes de operar |

---

## 6. Fluxo 4 — Completo sequencial (3 fontes + enriquecimento incremental + base única)

**Só inicia após Fluxos 1, 2 e 3 Done.**

### 6.1 Objetivo

Uma única operação: dado um endereço, extrair dos 3 sistemas **em sequência otimizada por valor-por-crédito**, enriquecer incrementalmente (cada fonte preenche o que a anterior não trouxe), consolidar em **base única** (golden record) e disponibilizar no CRM — com custo de crédito mínimo e auditoria total.

Princípio (ESTRATEGIA_EXTRACAO_CASCATA.md): **consolidar-antes-de-comprar** — listagem é barata e revela centenas de nomes; crédito de detalhe só é gasto em quem falta dado.

### 6.2 Arquitetura do fluxo

```
                  ┌─ Estágio A: INVENTÁRIO (3 listagens = 3 créditos) ─┐
                  │  runner eemovel --listing-only                     │
                  │  runner fisgar  --listing-only                     │
                  │  runner captei  --listing-only                     │
                  └────────────────┬───────────────────────────────────┘
                                   ▼
        Estágio B: CONSOLIDAÇÃO DE INVENTÁRIO (grátis, local)
        identity_resolution + record_key v2 (nome+unidade+vaga+endereço)
        → base preliminar SEM contato + matriz de presença por fonte
                                   ▼
        Estágio C: CASCATA DE DETALHES (crédito sob guard-rail)
        C1. EEmóvel: detalhes de todos sem contato           (cota 500)
        C2. Fisgar:  detalhes SÓ do delta (sem contato/CPF)   (cota 250)
        C3. Captei:  detalhes SÓ das lacunas estratégicas + validação WhatsApp (capcoins)
        → cada estágio recalcula o delta antes do próximo
                                   ▼
        Estágio D: ENRIQUECIMENTO (grátis/local)
        donodozap (nome público) para todo telefone; scoring de qualidade
                                   ▼
        Estágio E: GOLDEN RECORD (base única)
        merge_policies + consolidation → golden_records.json
        (1 pessoa = 1 registro; linhagem por fonte; PF ≠ morador separados)
                                   ▼
        Estágio F: PUSH PARA O CRM
        webhook/[source] por fonte (credencial própria, dedupe do CRM)
        → base única no CRM: contatos dedupados + imóvel + papéis
                                   ▼
        Estágio G: VERIFICAÇÃO
        relatório de reconciliação + conferência no frontend
```

### 6.3 Componentes

| Componente | Origem | Papel |
|-----------|--------|-------|
| runners por fonte (`live --listing-only` e `live`) | Fluxos 1–3 | coleta |
| `extrair_orquestrado.py` (estágios 1–3) | existente | esqueleto da orquestração — adaptar para chamar os runners reais |
| `comum/identity_resolution.py`, `merge_policies.py`, `consolidation.py`, `scoring.py` | existente | consolidação e golden record |
| `comum/whatsapp_validation_service.py` (donodozap) | existente | enriquecimento gratuito |
| `agentes/orquestrador_completo.py` | **NOVO** | CLI única: endereço → base única → CRM, com relatório de créditos e checkpoint por estágio |
| webhook/[source] + persist | existente (S2-1/S2-4) | persistência e visualização |

### 6.4 Etapas

| # | Etapa | Tipo |
|---|-------|------|
| 4.1 | Modo `--listing-only` nos 3 runners (só inventário, 1 crédito cada) | código |
| 4.2 | Estágio B: consolidador de inventário incremental — grava `inventario.json` com matriz de presença por fonte e delta por estágio | código |
| 4.3 | Estágio C: cascatas C1→C2→C3 com recálculo de delta entre estágios; resumo de orçamento antes de cada cascata e **aprovação humana** para C2/C3 (padrão aprovacao.json) | código |
| 4.4 | Estágio D: donodozap + scoring sobre a base enriquecida | código (plugar existente) |
| 4.5 | Estágio E: golden record — 1 pessoa = 1 registro, lista proprietários separada de moradores, linhagem de fontes por campo | código (adaptar consolidation.py) |
| 4.6 | Estágio F: push ao CRM via webhook por fonte; regra de unicidade: o CRM nunca recebe a mesma pessoa 2x (dedupe por CPF > telefone > nome+unidade) | código |
| 4.7 | `orquestrador_completo.py`: CLI única com checkpoint **por estágio** (retomada sem repetir cascata paga) e relatório final de créditos | código |
| 4.8 | E2E completo com os 3 endereços-piloto + re-execução (idempotência dupla: no extrator e no CRM) | operação |
| 4.9 | Runbook do fluxo completo validado por operador + revisão do relatório de reconciliação | operação |

### 6.5 Regras de negócio da consolidação (base única)

1. **Identidade:** `record_key v2` = canonical(nome) + unidade_imóvel + unidade_vaga + canonical(endereço). CPF completo (dígito verificador OK) sobrepõe a chave quando presente (chave forte).
2. **Merge de campos:** por fonte priorizada por qualidade — contato: EEmóvel < Fisgar < Captei (Captei tem WhatsApp validado); documento: Fisgar prevalece; endereço: o mais estruturado vence; conflitos ficam registrados em `raw` (nunca descartados).
3. **Proprietário ≠ morador:** listas separadas em todos os estágios; o papel (`crm_person_property_roles`) só recebe `proprietario` para a lista de proprietários.
4. **Delta mínimo:** um registro só recebe consulta paga de detalhe na fonte seguinte se estiver **sem contato** (ou sem documento, para Fisgar) após o estágio anterior.
5. **Auditoria:** todo gasto de crédito fica no manifest da execução com quem aprovou.

### 6.6 Ready específico

R1–R8 dos **3 fluxos simples Done** + saldos combinados suficientes para 1 piloto (3 listagens + detalhes do delta) + aprovações C2/C3 pré-acordadas.

### 6.7 Done específico

- 1 endereço-piloto completo: inventário nas 3 fontes → cascata → golden record → CRM;
- sobreposição medida: % de registros casados entre fontes ≥ 80% no lote de teste (esperado ~85%);
- economia provada: consultas de detalhe totais < U (universo consolidado) — alvo ~40% de economia vs. sem cascata;
- re-execução do mesmo endereço: **zero crédito extra de listagem** (inventário salvo no manifest) e zero duplicata no CRM;
- golden record visível no CRM com linhagem multi-fonte (badge de múltiplas fontes no S2-4);
- **telas da seção 6.9 operando com dados reais** (orquestração, aprovação, revisão de pares, linhagem);
- relatório de reconciliação e créditos arquivados por execução.

### 6.8 Riscos específicos

| Risco | Mitigação |
|-------|-----------|
| Falso negativo no matching → consulta duplicada | limiar conservador (banda 0.92/0.75 do matching_revisao) + revisão humana dos pares duvidosos (revisar_pares.py) |
| Falso positivo → perde quem tinha dado melhor | matching por nome+unidade+endereço, nunca só por nome |
| Cotas esgotadas no meio da cascata | checkpoint por estágio; cascata retoma de onde parou no mês seguinte |
| CRM recebe pessoas repetidas entre fontes | dedupe do webhook + dedupe prévio no golden record (2 camadas) |

### 6.9 Frontend do Fluxo 4 — telas novas (obrigatórias para o Done)

O Fluxo 4 **não opera só por CLI**: a orquestração, as aprovações pagas e a revisão de consolidção são decisões de negócio e precisam de tela. Done do Fluxo 4 inclui estas telas testadas com dados reais:

| Tela | Função | Done da tela (mesma régua R/D) |
|------|--------|-------------------------------|
| **Captação Completa** (`/crm/captacao/completa`) — NOVA | input do endereço → iniciar orquestração → progresso pelos estágios A–G (inventário, cascatas C1/C2/C3, enriquecimento, golden record, push) com status por fonte | 1 execução real acompanhada ponta a ponta nesta tela |
| **Ponto de aprovação C2/C3** — na tela acima | antes de cada cascata paga: orçamento (N consultas, custo verificado, saldo), botão aprovar → grava `aprovacao.json` com aprovador | aprovação real registrada e visível no relatório de créditos |
| **Revisão de pares duvidosos** (`/crm/captacao/revisao`) — NOVA | casamentos de identidade abaixo do limiar: aprovar/rejeitar par; alimenta o golden record | ≥1 lote de pares revisado com dados reais; decisão persistida |
| **Golden record / contato consolidado** — visão na tela de captação ou no contato do CRM | 1 pessoa = 1 registro com **linhagem por campo** (qual fonte forneceu o quê) | golden record real exibido com linhagem de ≥2 fontes |
| **Detalhe do imóvel (S2-5)** (`/crm/properties/captados/[id]`) — NOVA | imóvel com proprietários/moradores, papéis, badge multi-fonte ("2 fontes confirmaram") e histórico de captação | imóvel real do piloto aberto com linhagem multi-fonte |

Esforço adicional do Fluxo 4 por causa do frontend: **+2–3 dias** (total passa de 4–5 para **6–8 dias**).


---

## 7. Cronograma e dependências

```
Semana 1        F0 → Fluxo 1 (EEmóvel) ──────────────── Done
Semana 2        Fluxo 2 (Fisgar) ────────────────────── Done
Semana 3        Fluxo 3 (Captei) ────────────────────── Done
Semana 3–5      Fluxo 4 (Completo, incl. frontend 6.9) ─ Done
```

Regra inegociável: **um fluxo por vez**. Se um fluxo estourar a estimativa, o seguinte desloca — nunca paralelizamos fluxos de fonte diferentes (mesmo browser, mesmas credenciais, mesma conta de crédito).

---

## 8. Governança de créditos (todos os fluxos)

- Toda execução `live` produz `relatorio_creditos.json`: saldo antes/depois, ações pagas, custo verificado, aprovador.
- Guard-rail duplo: `--max-consultas` (técnico) + `aprovacao.json` (humano, para lotes pagos — obrigatório em Captei e nas cascatas C2/C3).
- Custo de cada ação vem de `custos_verificados.json` (sondado), nunca de estimativa.
- Orçamento por endereço-piloto definido **antes** da execução; estouro = parada automática.

---

## 9. Evidências e auditoria (o que fica arquivado por fluxo Done)

1. manifest NDJSON das execuções (append-only);
2. curated JSON/MD dos registros;
3. relatorio_creditos.json de cada execução;
4. screenshots do frontend (captacao + properties/captados);
5. log de contagem antes/depois do teste de idempotência;
6. runbook assinado pelo operador que executou sem ajuda de dev;
7. link dos commits/PRs referenciados (código é só o rastro; a evidência é a operação).

---

## 10. Resumo executivo

| Fluxo | Pronto quando | Valor |
|-------|---------------|-------|
| 1. EEmóvel | operador extrai de um endereço e vê contatos no CRM, 2x, sem duplicar | prova o caminho fim a fim |
| 2. Fisgar | idem + CPF enriquecendo a base | identidade forte |
| 3. Captei | idem + WhatsApp validado nativo, gasto auditado | qualidade de contato |
| 4. Completo | 1 comando → 3 fontes em cascata → golden record → CRM, com economia medida | o produto: base única de proprietários a custo mínimo |

---

## 11. Frontend — inventário de telas por fluxo

Princípio: cada fluxo é operado **pelo usuário no navegador**, não por CLI. CLI é o motor; a tela é o produto. O Done de cada fluxo inclui as telas abaixo testadas com dados reais.

### 11.1 Telas existentes (reaproveitadas — já operando)

| Tela | Usada em | Status |
|------|----------|--------|
| `/crm/captacao` — CaptacaoForm (busca por fonte única, rua/número/cidade, busca ao vivo x demo) | Fluxos 1–3 | ✅ existe |
| `ResultsTabs` + `RevisionTable` — resultados, seleção e revisão (exibe cpf · tel · email) | Fluxos 1–3 | ✅ existe |
| `ValidationWhatsApp` — validação de WhatsApp | Fluxos 1–3 | ✅ existe |
| `LotesView` — lotes salvos + export CSV | Fluxos 1–3 | ✅ existe |
| `/crm/properties/captados` — lista de imóveis captados (badge por fonte, busca, filtro) | Todos | ✅ existe (S2-4) |
| `/api/crm/captacao/credentials` — gestão de credenciais por fonte | Fluxos 1–3 | ⚠️ API existe; **verificar se há tela de configuração** — se não houver, criar tela simples em Settings |

### 11.2 Ajustes nas telas existentes (por fluxo simples)

| Fluxo | Ajuste | Critério de Done do ajuste |
|-------|--------|---------------------------|
| 1. EEmóvel | estados de erro amigáveis na busca ao vivo (timeout do runner, sessão expirada, endereço sem dados) — mensagem acionável, não stack trace | operador lê a mensagem e sabe o que fazer |
| 1. EEmóvel | aviso de custo estimado antes de disparar busca ao vivo ("≈ 1 + N créditos") | exibido antes de cada busca ao vivo |
| 2. Fisgar | coluna CPF/RG destacada na revisão + indicador de CPF forte x mascarado | visível com dados reais do Fisgar |
| 3. Captei | diálogo de aprovação com **orçamento de capcoins** antes da busca ao vivo (quem aprovou fica no relatório) | aprovação registrada e auditável |

Esforço: **1–2 dias** somados.

### 11.3 Telas novas (Fluxo 4)

Detalhadas na seção 6.9: Captação Completa (orquestração A–G), aprovação C2/C3, revisão de pares duvidosos, golden record com linhagem por campo, detalhe do imóvel S2-5. Esforço: **2–3 dias**.

### 11.4 Regra

Nenhuma tela entra no Done "pronta" sem ter sido **usada numa execução com dados reais** — mock não conta. Tela sem dado real é código, não entrega.




