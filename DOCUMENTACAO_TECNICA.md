# Documentação Técnica — Extrator de Proprietários Multi-Origem

**Versão**: 1.0  
**Data**: 2026-09-03  
**Status**: Produção — Base para desenvolvimento contínuo  
**Projeto**: extrator-proprietarios  
**Integração Futura**: PilotCRM (módulo Captação)

---

## 1. Resumo Executivo

Este projeto implementa um sistema de extração de dados de proprietários imobiliários a partir de três sistemas de origem:
- **Captei** — Consulta de proprietários com validação WhatsApp
- **Fisgar** — Consulta de proprietários com CPF/RG e referência DOM
- **EEmovel** — Consulta de proprietários + moradores com múltiplos endereços e CPF

A arquitetura segue padrão **Agent-Based** com:
- Manifesto append-only (NDJSON) para auditoria completa
- Checkpoint-based resumable processing
- Classificação automática PF vs Empresa
- Deduplicação cross-origem via `record_key` (SHA-256)
- Quality scoring por origem
- Relatórios de reconciliação em Markdown

---

## 2. Arquitetura Atual

### 2.1 Estrutura de Diretórios

```
extrator-proprietarios/
├── agentes/                    # Código Python dos agentes
│   ├── comum/                  # Utilitários compartilhados
│   │   └── __init__.py         # canonicalizar_texto, gerar_record_key, classificar_entidade,
│   │                            # criar_estrutura_lote, NDJSON, validações
│   ├── captei/                 # Agente Captei
│   │   ├── __init__.py         # AgenteCaptei: manifest, checkpoint, state tracking
│   │   ├── extrator.py         # processar_modal_captei, validar_dados_modal, quality, WhatsApp
│   │   └── persister.py        # persistir_proprietario (JSON/MD/RAW), consolidar_lote
│   ├── fisgar/                 # Agente Fisgar (paralelo a Captei)
│   │   ├── __init__.py         # AgenteFisgar: + scroll_position, dom_reference
│   │   ├── extrator.py         # processar_modal_fisgar, CTA selectors, tel:/mailto:
│   │   └── persister.py        # + sistema_origem='fisgar', CPF/RG no MD
│   ├── eemovel/                # NOVO: Agente EEmovel (a implementar)
│   │   ├── __init__.py         # AgenteEEmovel: + multi_enderecos, moradores
│   │   ├── extrator.py         # processar_modal_eemovel, CPF, multi-endereços
│   │   └── persister.py        # + sistema_origem='eemovel', moradores no MD
│   ├── extrair_captei.py       # CLI: inventariar_tabela, processar_pendentes, relatório
│   ├── extrair_fisgar.py       # CLI paralelo com scroll checkpoint
│   ├── extrair_eemovel.py      # NOVO: CLI para EEmovel
│   ├── exemplo_dados_tabela.json
│   └── exemplo_dados_modal.json
├── extracted/                  # Dados brutos extraídos (Excel, JSON, CSV, MD)
└── DOCUMENTACAO_TECNICA.md     # Este arquivo
```

### 2.2 Fluxo de Dados

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Dados Tabela   │────▶│  Agente (Captei/ │────▶│  Manifest NDJSON│
│  (JSON/Excel)   │     │   Fisgar/EEmovel)│     │  (append-only)  │
└─────────────────┘     └────────┬─────────┘     └────────┬────────┘
                                 │                        │
                                 ▼                        ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │ Processar Modal  │     │  Checkpoint     │
                        │ (Web/Simulado)   │     │  (JSON state)   │
                        └────────┬─────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Persistir       │
                        │  (JSON + MD +    │
                        │   RAW)           │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ Consolidar Lote  │
                        │ Relatório Recon. │
                        └──────────────────┘
```

### 2.3 Componentes Principais

| Componente | Responsabilidade | Arquivo |
|------------|------------------|---------|
| `canonicalizar_texto` | Normalização para matching (lower, sem acentos, sem pontuação) | `comum/__init__.py` |
| `gerar_record_key` | Chave única SHA-256: `name|unit|address` (20 chars) | `comum/__init__.py` |
| `classificar_entidade` | PF vs Empresa via tokens (LTDA, S.A., INCORPORADORA, etc.) | `comum/__init__.py` |
| `AgenteCaptei/AgenteFisgar` | Orquestração: manifest, checkpoint, state machine | `captei/__init__.py`, `fisgar/__init__.py` |
| `processar_modal_*` | Extração, validação, quality scoring, WhatsApp status | `captei/extrator.py`, `fisgar/extrator.py` |
| `persistir_proprietario` | JSON curado + Markdown legível + RAW para auditoria | `captei/persister.py`, `fisgar/persister.py` |
| `extrair_*.py` | CLI de orquestração end-to-end | `extrair_captei.py`, `extrair_fisgar.py` |

---

## 3. Análise de Integração PilotCRM

### 3.1 Stack PilotCRM
- **Monorepo**: pnpm workspaces
- **Linguagem**: TypeScript
- **ORM**: Drizzle (PostgreSQL)
- **Auth/DB**: Supabase
- **Frontend**: Next.js (App Router)
- **Domain Types**: `packages/domain` (puros, sem dependências)
- **Repositories**: `packages/pilotcrm-infra` (pattern repository com SupabaseClient)

### 3.2 Modelo de Dados Relevante (DATAMODEL.md — Frozen)

| Tabela | Propósito | Status |
|--------|-----------|--------|
| `crm_contacts` | Pessoa (centro do grafo) | Existe |
| `crm_properties` | Imóvel | Existe |
| `crm_property_addresses` | Endereço do imóvel | Existe |
| `crm_property_sources` | **Origem + source_record_id + raw_payload JSONB** | **Existe** ✅ |
| `person_role_property` | **Relação enriquecida Pessoa→Imóvel (role, purpose, price_range, source)** | **Existe** ✅ |
| `crm_captacoes` | Captação (broker, property, origin, commission) | Delta C (P1c) |
| `crm_developments` | Empreendimento | Delta C |
| `crm_units` | Unidade | Delta C |
| `crm_events` | Camada de eventos AI-native (enum EventType + JSONB) | Delta B |
| `crm_deals` | Negócio (expande com property/unit/development/broker) | Delta C |

### 3.3 Pontos de Integração Identificados

```typescript
// 1. crm_property_sources — Já suporta as 3 origens
enum PropertySource { "fisgar" | "captei" | "eemovel" | "manual" }

// 2. person_role_property — Vincula proprietário extraído ao imóvel
interface PersonRoleProperty {
  person_id: uuid;        // crm_contacts
  property_id: uuid;      // crm_properties
  role: "proprietario";
  source: PropertySource;
  last_interaction_at: timestamp;
}

// 3. crm_captacoes — Registro de captação por corretor
interface Captacao {
  property_id: uuid;
  broker_id: uuid;
  origin: "fisgar" | "captei" | "eemovel" | "manual";
  capture_date: date;
  exclusivity: boolean;
  commission_pct: numeric;
}

// 4. crm_events — Auditoria para IA
enum EventType {
  OwnerExtracted = "owner_extracted",
  PropertyEntered = "property_entered",
  // ...
}

// 5. LeadSource (domain) — Precisa expandir para incluir origens
type LeadSource = "captacao" | "manual" | "referral" | ... // Adicionar fisgar/captei/eemovel
```

---

## 4. Roadmap & Sprints

### 4.1 Visão Geral de Fases

| Fase | Foco | Entregável | Duração |
|------|------|------------|---------|
| **Fase 0** | Fundação | Agentes Python completos (Captei, Fisgar, EEmovel) + Testes | Sprint 1-2 |
| **Fase 1** | **Consolidação Multi-Origem** | **Pipeline unificado: normalização, sanitização, dedup, validação, merge** | **Sprint 3-4** |
| **Fase 2** | Integração Core | Domain types + Repository + Service layer no PilotCRM | Sprint 5-6 |
| **Fase 3** | UI/UX | Wizard Captação no PilotCRM (Sidebar IMOBILIÁRIO) | Sprint 7-8 |
| **Fase 4** | Automação | Browser automation (Playwright) para extração real | Sprint 9-10 |
| **Fase 5** | IA & Observabilidade | Command Bar, crm_events, reconciliação avançada | Sprint 11-12 |

---

## 4.2 Fase 1 — Consolidação Multi-Origem: Pipeline Unificado (Sprint 3-4)

> **CRÍTICO**: Os mesmos proprietários aparecem em Captei, Fisgar e EEmovel com informações diferentes (CPF só no Fisgar/EEmovel, WhatsApp só no Captei, endereços adicionais só no EEmovel, moradores só no EEmovel). Esta fase produz **uma única base completa e consistente** — a "Golden Record" por proprietário.

### Metodologia: Benchmark → Brainstorm → Define → Spec → Plan → Execute

#### 4.2.1 Benchmark (Semana 3 - Dias 1-2)

| Atividade | Entregável | Critério |
|-----------|------------|----------|
| Coletar amostras reais das 3 origens (mesmo endereço) | Dataset de benchmark: 50+ proprietários cross-origem | Cobertura: PF, Empresa, Morador |
| Medir overlap real: % mesmos nomes, % CPF match, % telefone match | Relatório de overlap com matriz de concordância | Quantitativo |
| Testar `record_key` atual: taxa colisão falsa, taxa miss | Análise de falsos positivos/negativos | <2% FP, <5% FN |
| Avaliar qualidade por campo por origem | Scorecard: completude, precisão, frescor por campo | Tabela comparativa |

**Ferramentas**: Python notebooks, `difflib`, `fuzzywuzzy`, pandas profiling

#### 4.2.2 Brainstorm (Semana 3 - Dias 3-4)

**Perguntas-chave a resolver:**

1. **Identidade**: `record_key` (name|unit|address) é suficiente? CPF deve ser fator primário quando disponível?
2. **Merge strategy**: "Last write wins" vs "Most complete wins" vs "Source priority" vs "Field-level merge"?
3. **Conflitos**: Telefones diferentes — concatenar? Priorizar validado (Captei)? Priorizar principal (Fisgar/EEmovel)?
4. **Moradores EEmovel**: Manter como entidade separada? Vincular ao imóvel como `tipo_pessoa: morador`?
5. **Empresas**: Mesclar ou manter separadas por origem? CNPJ como chave forte?
6. **Histórico**: Preservar proveniência de cada campo (source + timestamp) para auditoria?
7. **Validação**: Regras automáticas vs revisão manual threshold?

**Output**: Documento de decisões preliminares (ADR rascunho)

#### 4.2.3 Define (Semana 3 - Dia 5)

**Definições formais:**

| Conceito | Definição |
|----------|-----------|
| **Golden Record** | Registro único por proprietário (pessoa física), combinando melhores campos de todas origens |
| **Source Record** | Registro bruto de uma origem específica (imutável, auditável) |
| **Merge Policy** | Regras determinísticas por campo para resolver conflitos |
| **Confidence Score** | 0-100 por campo e por record, baseado em concordância cross-origem + validadores |
| **Provenance** | Metadados: `source`, `source_record_id`, `extracted_at`, `field_level_origin` |

**Chaves de identidade (hierarquia):**
1. CPF (quando disponível em ≥2 origens) — **forte**
2. `record_key` canônico (name|unit|address) — **médio**
3. Nome + telefone normalizado — **fraco**
4. Fuzzy match (nome similar + mesmo endereço) — **revisão manual**

#### 4.2.4 Spec (Semana 4 - Dias 1-2)

**Especificação do Pipeline de Consolidação:**

```python
# Entrada: 3 listas de SourceRecord (Captei, Fisgar, EEmovel)
# Saída: Lista de GoldenRecord + Relatório de Merge

class ConsolidationPipeline:
    stages = [
        "normalize",      # Padronizar campos (nomes, telefones, endereços, CPF)
        "sanitize",       # Remover PII de logs, mascarar CPF/telefone em outputs não seguros
        "deduplicate",    # Agrupar por identidade (CPF > record_key > fuzzy)
        "merge",          # Aplicar merge_policy por campo
        "validate",       # Regras de consistência + quality gates
        "enrich",         # Completar campos faltantes via lookup cruzado
        "score",          # Confidence por campo e record
        "output"          # GoldenRecord + SourceRecord links + MergeReport
    ]

# Merge Policy por campo (exemplo)
MERGE_POLICY = {
    "nome_completo": "most_complete",      # Maior string não-vazia
    "cpf": "non_null_priority",            # Primeiro não-nulo (validado)
    "telefones": "union_dedup",            # União deduplicada por dígitos
    "emails": "union_dedup",               # União deduplicada por lower
    "enderecos": "union_all",              # Todos (principal + adicionais)
    "data_nascimento": "non_null_priority",
    "idade": "most_recent",                # Mais recente (calculada da nascimento)
    "imovel_detalhes": "most_complete",    # EEmovel tem mais detalhes
    "whatsapp_status": "captei_priority",  # Só Captei tem
    "tipo_pessoa": "source_priority",      # Proprietário > Morador
    "quality": "recalculate"               # Recalcular no Golden
}
```

#### 4.2.5 Plan (Semana 4 - Dias 3-4)

| Task | Arquivo | Estimativa | Dependência |
|------|---------|------------|-------------|
| `comum/consolidation.py` — Core pipeline | Novo | 16h | Benchmark |
| `comum/merge_policies.py` — Políticas por campo | Novo | 8h | Spec |
| `comum/identity_resolution.py` — CPF + record_key + fuzzy | Novo | 16h | Define |
| `comum/validators.py` — Regras de validação cross-origem | Novo | 8h | Spec |
| `comum/scoring.py` — Confidence scoring | Novo | 8h | Spec |
| `consolidar_multi_origem.py` — CLI orquestrador | Novo | 8h | Pipeline |
| Testes: golden records esperados vs reais | Test | 16h | Plan |
| Benchmark regressivo automatizado | Test | 8h | Benchmark |

#### 4.2.6 Execute (Sprint 4)

| Sprint 4 Backlog | Status |
|------------------|--------|
| Implementar `normalize` stage | ☐ |
| Implementar `sanitize` stage (LGPD) | ☐ |
| Implementar `deduplicate` com identity resolution | ☐ |
| Implementar `merge` com políticas configuráveis | ☐ |
| Implementar `validate` (regras + quality gates) | ☐ |
| Implementar `enrich` (lookup cruzado) | ☐ |
| Implementar `score` (confidence 0-100) | ☐ |
| Implementar `output` (GoldenRecord NDJSON + MergeReport MD) | ☐ |
| CLI `consolidar_multi_origem.py` | ☐ |
| Testes integrados com dados reais | ☐ |
| Documentar MergeReport format | ☐ |

**Definition of Done Fase 1:**
- [ ] Pipeline roda end-to-end com 3 origens
- [ ] Golden Records produzidos para 100% dos proprietários únicos
- [ ] MergeReport documenta cada decisão de merge
- [ ] Zero perda de dados (SourceRecords preservados)
- [ ] Confidence score médio > 85
- [ ] Taxa revisão manual < 10%

---

### 4.3 Sprint 1 — Fundação: Agentes Completos (Semana 1-2)

#### Sprint Goal
Entregar 3 agentes Python funcionais, testados e documentados, prontos para consumo via CLI ou subprocess.

#### Backlog do Sprint

| ID | Task | Tipo | Estimativa | Critério de Aceite |
|----|------|------|------------|---------------------|
| T1.1 | Implementar `agentes/eemovel/__init__.py` (AgenteEEmovel) | Dev | 8h | Classe com manifest, checkpoint, scroll, multi-endereços |
| T1.2 | Implementar `agentes/eemovel/extrator.py` | Dev | 8h | processar_modal_eemovel, CPF, multi-endereços, quality |
| T1.3 | Implementar `agentes/eemovel/persister.py` | Dev | 4h | JSON/MD/RAW + moradores, sistema_origem='eemovel' |
| T1.4 | Implementar `extrair_eemovel.py` (CLI) | Dev | 4h | Paralelo a extrair_captei/fisgar.py |
| T1.5 | Criar `exemplo_dados_tabela_eemovel.json` | Data | 2h | 10+ registros representativos (PF, Empresa, Moradores) |
| T1.6 | Criar `exemplo_dados_modal_eemovel.json` | Data | 2h | Modal completo com CPF, multi-endereços, moradores |
| T1.7 | Testes integrados: 3 agentes rodam sem erro | QA | 4h | `python3 extrair_*.py --lote teste --limite 3` passa |
| T1.8 | Documentar CLI unificado (`make extract`) | Doc | 2h | Makefile ou script wrapper |

#### Definition of Done
- [ ] 3 agentes passam em `pnpm test:unit` (ou pytest equivalente)
- [ ] Manifest NDJSON válido e legível
- [ ] Checkpoint permite resume exato
- [ ] Relatório de reconciliação gera Markdown correto
- [ ] Zero warnings de tipo (mypy/pyright se aplicável)

---

### 4.4 Sprint 4 — Qualidade & Resilência (Semana 5-6)

#### Sprint Goal
Hardening dos agentes: retry, rate limit, validação cruzada, logging estruturado.

| ID | Task | Tipo | Estimativa |
|----|------|------|------------|
| T2.1 | Retry exponencial + circuit breaker nas chamadas web | Dev | 8h |
| T2.2 | Rate limiting por origem (Captei: capcoins, Fisgar: req/min, EEmovel: créditos) | Dev | 8h |
| T2.3 | Validação cross-origem: dedup por record_key no consolidado | Dev | 8h |
| T2.4 | Logging estruturado (JSONL) para observabilidade | Dev | 4h |
| T2.5 | Testes de falha: modal incompleto, rede instável, crédito zero | QA | 8h |
| T2.6 | Métricas de qualidade por origem (dashboard simples) | Dev | 4h |

---

### 4.5 Sprint 5 — PilotCRM Domain & Repository (Semana 7-8)

#### Sprint Goal
Types TypeScript + Repository pattern para persistir extrações no PilotCRM.

| ID | Task | Arquivo | Estimativa |
|----|------|---------|------------|
| T3.1 | `packages/domain/src/crm/extractor.ts` — Types: ExtractionJob, ExtractedOwner, ExtractorSource | Domain | 4h |
| T3.2 | `packages/domain/src/crm/captacao.ts` — Types: Captacao, CaptacaoOrigin | Domain | 4h |
| T3.3 | `packages/pilotcrm-infra/src/extractor-repository.ts` — CRUD ExtractionJob | Infra | 8h |
| T3.4 | `packages/pilotcrm-infra/src/captacao-repository.ts` — CRUD Captacao | Infra | 8h |
| T3.5 | `packages/pilotcrm-infra/src/property-source-repository.ts` — crm_property_sources | Infra | 4h |
| T3.6 | `packages/pilotcrm-infra/src/role-property-repository.ts` — person_role_property | Infra | 4h |
| T3.7 | `packages/pilotcrm-infra/src/event-repository.ts` — crm_events (Delta B) | Infra | 8h |
| T3.8 | Testes de repositório (vitest) | Test | 8h |

---

### 4.6 Sprint 6 — Service Layer & Adapters (Semana 9-10)

#### Sprint Goal
Orquestração: chamar agentes Python, reconciliar, persistir no PilotCRM.

| ID | Task | Arquivo | Estimativa |
|----|------|---------|------------|
| T4.1 | `packages/pilotcrm-application/src/extractor/extractor.service.ts` — Orquestra job | App | 8h |
| T4.2 | `packages/pilotcrm-application/src/extractor/captei-adapter.ts` | App | 4h |
| T4.3 | `packages/pilotcrm-application/src/extractor/fisgar-adapter.ts` | App | 4h |
| T4.4 | `packages/pilotcrm-application/src/extractor/eemovel-adapter.ts` | App | 4h |
| T4.5 | `packages/pilotcrm-application/src/extractor/reconciliation.service.ts` — Dedup + Sync | App | 16h |
| T4.6 | Server Action: `apps/pilotcrm/src/actions/extractor.actions.ts` | Next.js | 8h |
| T4.7 | Testes de integração (mock agents) | Test | 8h |

---

### 4.7 Sprint 7 — UI: Wizard Captação (Semana 11-12)

#### Sprint Goal
Interface completa no PilotCRM (Sidebar IMOBILIÁRIO → Captação → Nova Captação).

| ID | Task | Componente | Estimativa |
|----|------|------------|------------|
| T5.1 | Page: `/captacao` — List com tabs [Visão geral][Origens][Log] | Next.js | 8h |
| T5.2 | Page: `/captacao/nova` — Wizard 4 steps (Endereço→Origens→Confirmação→Processando) | Next.js | 16h |
| T5.3 | Component: AddressAutocomplete (CEP + Google Places) | React | 8h |
| T5.4 | Component: SourceSelector (cards com créditos/disponibilidade) | React | 8h |
| T5.5 | Component: LiveProgress (WebSocket/SSE para progresso real-time) | React | 16h |
| T5.6 | Page: `/captacao/[id]` — Resultado + Reconciliação + Ações | Next.js | 8h |
| T5.7 | Integração Command Bar (⌘K): "Nova captação Rua X" | Next.js | 4h |

---

### 4.8 Sprint 8 — Browser Automation (Semana 13-15)

#### Sprint Goal
Substituir simulação por extração real via Playwright.

| ID | Task | Detalhe | Estimativa |
|----|------|---------|------------|
| T6.1 | Setup Playwright + Docker/Chromium no monorepo | Infra | 8h |
| T6.2 | `CapteiBrowserExtractor` — Login, busca, paginação, modal, "Ver mais" telefones | Dev | 24h |
| T6.3 | `FisgarBrowserExtractor` — Login, busca, CTA por DOM reference, scroll | Dev | 24h |
| T6.4 | `EEmovelBrowserExtractor` — Login, busca range, paginação, detalhes moradores | Dev | 24h |
| T6.5 | Pool de browsers + queue de jobs (BullMQ ou similar) | Dev | 16h |
| T6.6 | Screenshots de erro + retry automático | Dev | 8h |
| T6.7 | Testes E2E contra staging de cada origem | QA | 16h |

---

### 4.9 Sprint 9 — IA & Observabilidade (Semana 16-18)

| ID | Task | Detalhe |
|----|------|---------|
| T7.1 | Backfill crm_events histórico (messages, activities, consent) | Delta B |
| T7.2 | Command Bar AI: "Quais proprietários extraídos semana passada sem telefone?" | Next.js |
| T7.3 | Dashboard qualidade por origem + tendência | Next.js |
| T7.4 | Alertas: crédito baixo, falha extração, dedup alta | Infra |
| T7.5 | Exportação CSV/Excel unificada (todas origens) | Dev |

---

## 5. Riscos & Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Mudança de DOM/seletores nos sites origem | Alta | Alto | Seletores configuráveis + testes visuais semanais |
| Rate limiting / bloqueio de IP | Média | Alto | Proxy rotation, respect robots.txt, delays humanos |
| Créditos insuficientes (Captei/Fisgar/EEmovel) | Média | Médio | Monitoramento prévio + alerta no UI |
| Dados sensíveis (CPF, telefone) em logs | Baixa | Crítico | Sanitização automática, LGPD compliance |
| Conflito de schema PilotCRM (Delta A/B/C) | Baixa | Alto | Branches por delta, gates 381 testes |
| Duplicação de proprietários cross-origem | Média | Médio | record_key canônico + revisão manual flag |

---

## 6. Métricas de Sucesso (KPIs)

| Métrica | Target Sprint 1-2 | Target Sprint 4 | Target Sprint 6 | Target Sprint 9 |
|---------|-------------------|-----------------|-----------------|-----------------|
| Taxa sucesso extração | >95% | >98% | >99% | >99.5% |
| Tempo extração/endereço (3 origens) | <5 min (simulado) | <3 min | <2 min (real) | <90s (real) |
| Taxa dedup cross-origem | N/A | >90% | >95% | >98% |
| Cobertura testes (Python + TS) | >80% | >85% | >90% | >95% |
| Zero vazamento PII em logs | 100% | 100% | 100% | 100% |
| Disponibilidade API extractor | N/A | 99.5% | 99.9% | 99.99% |

---

## 7. Próximos Passos Imediatos

### Prioridade 1 — Esta Semana
1. ✅ **Implementar Agente EEmovel** (paralelo a Captei/Fisgar)
2. ✅ Criar dados de exemplo EEmovel
3. ✅ Testar 3 agentes em sequência
4. ✅ Documentar CLI unificado

### Prioridade 2 — Próxima Semana
5. Iniciar Fase 1: Benchmark de consolidação cross-origem
6. Brainstorm/Define/Spec do pipeline de merge
7. Setup CI/CD para agentes Python (GitHub Actions)

### Prioridade 3 — Curto Prazo
8. Browser automation (Playwright) para uma origem (piloto Captei)
9. Wizard UI no PilotCRM
10. Integração Command Bar

---

## 8. Apêndices

### 8.1 Estrutura de Dados EEmovel (Baseado na Amostra Fornecida)

```json
{
  "nome_completo": "ANA LAURA ALCANTARA ALVES",
  "tipo": "Proprietário",                    // ou "Possível morador"
  "endereco_principal": "Marc Chagall, 397 - Ap 101 E 2 Vg Bl C Recanto Jacaranda",
  "enderecos_adicionais": [
    "Ulisses Cruz, 668 - Ap 37 E 2 Vg Torre A Sky The Gardens Sea",
    "Saturnino Pereira, 12 - A 12"
  ],
  "cpf": "***.236.678-**",
  "idade": 44,
  "obito": false,
  "telefones": [
    "(11) 96751-6505",
    "(11) 96103-9278",
    "(16) 3633-2114"
  ],
  "emails": [
    "alcantara.analauraalves@gmail.com",
    "analaura151521@yahoo.com.br"
  ],
  "imovel": {
    "ano_construcao": 2015,
    "edificio": "CONDOMINIO RECANTO JACARANDA",
    "padrao": "Residencial Vertical Padrão D",
    "uso": "Apartamento Em Condomínio",
    "area_terreno": 8254,
    "area_construida": 174
  }
}
```

### 8.2 Diferenças-chave EEmovel vs Captei/Fisgar

| Aspecto | Captei | Fisgar | EEmovel |
|---------|--------|--------|---------|
| **Tipos de pessoa** | Proprietário | Proprietário | Proprietário + Morador |
| **Endereços** | 1 principal | 1 principal | 1 principal + múltiplos adicionais |
| **CPF** | Não | Sim | Sim (mascarado) |
| **RG** | Não | Sim | Não |
| **WhatsApp** | Status validado | Não | Não |
| **Moradores** | Não | Não | Sim (tipo "Possível morador") |
| **Dados imóvel** | Básicos | Básicos | Detalhados (área, padrão, ano) |
| **Créditos** | Capcoins | Requisições | Créditos |

### 8.3 Comandos de Referência

```bash
# Testar agentes individuais
cd agentes
python3 extrair_captei.py --lote teste_captei --endereco "Rua Marc Chagall, 397" --dados exemplo_dados_tabela.json --limite 3
python3 extrair_fisgar.py --lote teste_fisgar --endereco "Rua Marc Chagall, 397" --dados exemplo_dados_tabela.json --limite 3
python3 extrair_eemovel.py --lote teste_eemovel --endereco "Rua Marc Chagall, 397" --dados exemplo_dados_tabela_eemovel.json --limite 3

# Ver manifest
cat teste_captei/manifest/manifest_teste_captei.ndjson

# Ver relatório
cat teste_captei/curated/reconciliacao_teste_captei.md

# Ver dados persistidos
ls teste_captei/curated/*.json
ls teste_captei/curated/*.md
```

---

## 9. Decisões de Arquitetura (ADRs)

| ADR | Decisão | Justificativa |
|-----|---------|---------------|
| ADR-001 | NDJSON append-only para manifest | Auditoria imutável, replay, streaming |
| ADR-002 | record_key = SHA256(name|unit|address)[:20] | Determinístico, cross-origem, colisão desprezível |
| ADR-003 | Classificação PF/Empresa por tokens | Simples, extensível, zero ML |
| ADR-004 | Adapter pattern para integração PilotCRM | Desacoplamento, testabilidade, substituição |
| ADR-005 | Reconciliação no PilotCRM (não no Python) | Fonte da verdade única, transacional, tenant-scoped |
| ADR-006 | Browser automation separado dos agentes core | Separação de responsabilidades, pool isolado |

---

*Documento vivo — atualizar a cada sprint concluído.*