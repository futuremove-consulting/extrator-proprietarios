# Jornadas de Usuário, Inventário de UIs e Planejamento Frontend

**Versão:** 1.0
**Data:** 04/09/2026
**Status:** Proposto

---

## 1. Personas

### 1.1 Corretor de Imóveis

| Atributo | Descrição |
|----------|-------------------|
| **Nome** | Carlos, 35 anos |
| **Objetivo** | Encontrar proprietários para captar imóveis |
| **Dores** | Perda de tempo ligando para não-proprietários, dados desatualizados |
| **Nível Tech** | Intermediário (usa WhatsApp, apps) |

### 1.2 Gerente de Imobiliária

| Atributo | Descrição |
|----------|-------------------|
| **Nome** | Ana, 42 anos |
| **Objetivo** | Acompanhar métricas de capção da equipe |
| **Dores** | Falta de visão sobre o pipeline de captação |
| **Nível Tech** | Avanáado (planilhas, CRMs) |

### 1.3 Administrador do Sistema

| Atributo | Descrição |
|----------|-------------------|
| **Nome** | Pedro, 28 anos |
| **Objetivo** | Configurar integrações e monitorar sistema |
| **Dores** | Configurações complexas, falta de logs |
| **Nível Tech** | Avaná0ado (CLI, APIs) |

---

## 2. Jornadas de Usuário

### 2.1 Jornada 1: Extrair Proprietários de um Endereço

**Persona:** Corretor
**Objetivo:** Obter lista de proprietários válidos



**Etapas:**
1. Usuário insere endereço
2. Sistema valida endereço
3. Executa extração em cascata
4. Exibe resultados com score
5. Usuário exporta dados

### 2.2 Jornada 2: Validar WhatsApp

**Persona:** Corretor
**Objetivo:** Confirmar se telefone pertence ao proprietário



### 2.3 Jornada 3: Acompanhar Extração

**Persona:** Gerente
**Objetivo:** Monitorar execuções



### 2.4 Jornada 4: Configurar Integrações

**Persona:** Administrador
**Objetivo:** Conectar sistemas externos



### 2.5 Jornada 5: Revisar Matching Manual

**Persona:** Corretor
**Objetivo:** Validar casos ambíguos



---

## 3. Inventário de Telas

### 3.1 Telas Principais

| # | Tela | Rota | Descrição | Prioridade |
|---|------|------|-------------------|------------|
| 1 | Home |  | Dashboard com ações rápidas | P0 |
| 2 | Extrair |  | Formulário de extração | P0 |
| 3 | Execucao |  | Acompanhar execução | P0 |
| 4 | Resultados |  | Lista de proprietários | P0 |
| 5 | Lotess |  | Listagem de lotes | P1 |
| 6 | Validacao |  | Validar WhatsApp | P1 |
| 7 | Revisao |  | Fila de revisão manual | P1 |
| 8 | Configuracoes |  | Configurações gerais | P1 |
| 9 | Integracoes |  | Marketplace | P2 |
| 10 | Logs |  | Visualizar logs | P2 |

### 3.2 Componentes de Interface

| Componente | Onde Usar | Descrição |
|------------|-----------|-------------------|
|  | Home, Extrair | Campo de endereço com autocomplete |
|  | Execucao | Barra de progresso por sistema |
|  | Vários | Badge de status (sucesso, erro, pendente) |
|  | Resultados | Card de proprietário com score |
|  | Validacao | Resultado da validação |
|  | Extrair | Estimativa de custo |
|  | Resultados | Medidor de confiança |
|  | Integracoes | Card de integração |
|  | Logs | Visualizador de logs |
|  | Revisao | Par para revisão manual |

---

## 4. Fluxos Detalhados

### 4.1 Fluxo de Extração



### 4.2 Fluxo de Validação



### 4.3 Fluxo de Integração



---

## 5. Arquitetura Frontend Proposta

### 5.1 Stack Tecnológica

| Camada | Tecnologia | Justificativa |
|--------|------------|---------------|
| Framework | Next.js 15 | PilotCRM já usa |
| UI | shadcn/ui | Componentes acessíveis |
| State | Zustand | Leve, simples |
| Forms | React Hook Form + Zod | Validação |
| Tables | TanStack Table | Performance |
| Charts | Recharts | Dashboard |
| HTTP | fetch + SWR | Cache e revalidação |

### 5.2 Estrutura de Páginas



### 5.3 Componentes Compartilhados



---

## 6. Especificação de Telas

### 6.1 Dashboard (Home)

| Elemento | Tipo | Ação |
|----------|------|-----------|
| Header | Layout | Logo, navegação |
| Quick Action | Button | Iniciar extração |
| Stats Cards | Cards | Total extrações, sucesso, custo |
| Recent Lots | Table | Últimos 5 lotes |
| System Status | Indicador | Status dos 3 sistemas |

### 6.2 Extrair

| Elemento | Tipo | Validação |
|----------|------|---------------|
| Endereço | TextInput | Obrigatório, mínimo 5 chars |
| Sistemas | Checkboxes | Pelo menos 1 |
| Modo | Radio | API, Browser, Ambos |
| Cost Estimate | Display | Calculado em tempo real |
| Submit | Button | Desabilitado se inválido |

### 6.3 Execução

| Elemento | Tipo | Atualização |
|----------|------|------------------|
| Progress Bar | Progress | A cada 2s |
| System Status | Badges | WebSocket |
| Log Viewer | Terminal | Stream |
| Cost Counter | Display | Tempo real |
| Cancel Button | Button | Confirmação |

### 6.4 Resultados

| Elemento | Tipo | Funcionalidade |
|----------|------|----------------|
| Filters | Search/Filter | Nome, score, sistema |
| Table | DataTable | Ordenável, paginada |
| Export Button | Dropdown | CSV, JSON, Excel |
| Validate Button | Action | Inicia validação |
| Owner Card | Detail | Expandir detalhes |

### 6.5 Configurações

| Elemento | Tipo | Opções |
|----------|------|-----------|
| Feature Flags | Toggles | Liga/desliga features |
| Rate Limits | Sliders | Ajuste por sistema |
| Timeouts | Number | Segundos |
| Logging | Select | Nível, formato |
| Save Button | Button | Persiste alterações |

---

## 7. Planejamento de Implementação

### 7.1 Fase 1 - MVP (2 semanas)

| Prioridade | Tela | Componentes |
|------------|------|-------------|
| P0 | Dashboard | Header, Stats, Recent Lots |
| P0 | Extrair | AddressInput, CostEstimator |
| P0 | Execucao | ProgressBar, LogViewer |
| P0 | Resultados | OwnerTable, ExportButton |

### 7.2 Fase 2 - Funcionalidades (2 semanas)

| Prioridade | Tela | Componentes |
|------------|------|-------------|
| P1 | Validacao | ValidationResult |
| P1 | Revisao | ReviewPair |
| P1 | Lotes | LotTable, Filters |
| P1 | Configurações | FeatureToggles |

### 7.3 Fase 3 - Integrações (1 semana)

| Prioridade | Tela | Componentes |
|------------|------|-------------|
| P2 | Integrações | IntegrationCard, CredentialsForm |
| P2 | Logs | LogViewer avaná0ado |

---

## 8. Estados e Feedback

### 8.1 Estados de Tela

| Estado | Visual | Quando |
|--------|--------|--------|
| Loading | Skeleton/Spinner | Carregando dados |
| Empty | Illustration + CTA | Sem dados |
| Error | Alert + Retry | Erro na API |
| Success | Content | Dados carregados |
| Partial | Content + Warning | Dados parciais |

### 8.2 Feedback ao Usuário

| Ação | Feedback | Duração |
|-----------|----------|------------|
| Iniciar extração | Toast + Redirect | 3s |
| Extração concluída | Toast + Sound | 5s |
| Erro | Toast + Detalhes | Até fechar |
| Validação válida | Badge verde | Permanente |
| Rate limit | Progress + ETA | Até liberar |

---

## 9. Resumo

### Jornadas Mapeadas: 5
- Extrair Proprietários
- Validar WhatsApp
- Acompanhar Extração
- Configurar Integrações
- Revisar Matching

### Telas: 10
- 4 P0 (críticas)
- 4 P1 (importantes)
- 2 P2 (melhorias)

### Componentes: 15+
- Forms: 2
- Cards: 3
- Feedback: 3
- Data: 2
- Layout: 3

### Próximos Passos
1. Aprovar este documento
2. Criar protótipo no Figma
3. Implementar Fase 1 (MVP)
4. Testar com usuários reais
