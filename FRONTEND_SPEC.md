# Especificacao de Frontend - Extrator de Proprietarios

**Versao:** 1.0
**Data:** 04/09/2026
**Status:** Aprovado para implementacao

---

## 1. Principios de Design

### 1.1 Minimalismo Funcional

| Principio | Aplicacao |
|-----------|----------|
| **Menos e mais** | Cada elemento deve ter funcao clara |
| **Espaco em branco** | Respiracao visual, foco no conteudo |
| **Tipografia como hierarquia** | Sem cores excessivas, peso e tamanho bastam |
| **Uma acao primaria** | Cada tela tem 1 CTA principal claro |

### 1.2 Anticipatory Design

| Principio | Aplicacao |
|-----------|----------|
| **Sugestao inteligente** | Preenche endereco, estima custo automaticamente |
| **Proxima acao clara** | Sempre mostra o que fazer a seguir |
| **Dados pre-carregados** | Cache de consultas recentes |
| **Empty states uteis** | Nunca tela vazia, sempre com direcao |

### 1.3 Opinionado

| Decisao | Justificativa |
|---------|---------------|
| **Sidebar fixa** | Padrao CRMs modernos (Attio, Linear) |
| **Tabela como view principal** | Dados tabulares sao o coracao do CRM |
| **Acao em massa** | Sempre disponivel em listas |
| **Filtros persistentes** | Salva ultima busca |

### 1.4 Deterministico

| Decisao | Justificativa |
|---------|---------------|
| **Mesma acao = mesmo resultado** | Previsibilidade |
| **Estados claros** | Loading, success, error, empty |
| **Feedback imediato** | Toda acao tem resposta visual |
| **Zero surpresas** | Confirmacao para acoes destrutivas |

---

## 2. Design System

### 2.1 Tokens de Cor



### 2.2 Tipografia



### 2.3 Espacamento



### 2.4 Bordas e Sombras



---

## 3. Layout

### 3.1 Estrutura Base



### 3.2 Sidebar

| Propriedade | Valor |
|-------------|-------|
| Largura | 240px (expansivel para 280px) |
| Background |  |
| Border right | 1px  |
| Padding |  |
| Item height | 36px |
| Item padding |   |
| Item radius |  |
| Active bg |  |
| Active color |  |
| Hover bg |  |

### 3.3 Header

| Propriedade | Valor |
|-------------|-------|
| Altura | 64px |
| Background |  |
| Border bottom | 1px  |
| Padding |   |
| Busca | Largura 320px, altura 36px |

### 4. Componentes

### 4.1 Button

| Variante | Uso | Estilo |
|----------|-----|--------|
| **Primary** | Acao principal | bg primary, white text, hover darker |
| **Secondary** | Acao secundaria | bg white, border, gray text |
| **Ghost** | Acao terciaria | sem bg, gray text, hover gray bg |
| **Danger** | Acao destrutiva | bg error, white text |

| Tamanho | Height | Padding | Font |
|---------|--------|---------|------|
| sm | 32px | 8px 12px | 12px |
| md | 36px | 8px 16px | 14px |
| lg | 40px | 12px 20px | 14px |

### 4.2 Input

| Propriedade | Valor |
|-------------|-------|
| Height | 36px |
| Padding | 8px 12px |
| Border | 1px gray-300 |
| Radius | 6px |
| Focus | 2px primary ring |
| Placeholder | gray-400 |
| Error | border error, message abaixo |

### 4.3 Select/Dropdown

| Propriedade | Valor |
|-------------|-------|
| Height | 36px |
| Trigger | Same as input |
| Menu | white, shadow-lg, radius-md |
| Item | 36px height, hover gray-50 |
| Selected | primary-light bg |

### 4.4 Table

| Propriedade | Valor |
|-------------|-------|
| Header | gray-50 bg, 40px height, semibold |
| Row | 48px height, border-bottom gray-100 |
| Row hover | gray-50 |
| Row selected | primary-light |
| Cell padding | 12px 16px |
| Checkbox | 16px, radius-sm |

### 4.5 Badge

| Variante | Uso | Cores |
|----------|-----|-------|
| **success** | Validado | emerald |
| **warning** | Pendente | amber |
| **error** | Erro | red |
| **info** | Info | blue |
| **neutral** | Neutro | gray |

| Propriedade | Valor |
|-------------|-------|
| Height | 20px |
| Padding | 2px 8px |
| Radius | 9999px (pill) |
| Font | 12px, medium |

### 4.6 Card

| Propriedade | Valor |
|-------------|-------|
| Background | white |
| Border | 1px gray-200 |
| Radius | 8px |
| Padding | 16px |
| Shadow | shadow-sm |

### 4.7 Modal

| Propriedade | Valor |
|-------------|-------|
| Overlay | black 50% opacity |
| Background | white |
| Radius | 12px |
| Shadow | shadow-xl |
| Max width | 480px (sm), 640px (md), 768px (lg) |
| Padding | 24px |

### 4.8 Toast

| Propriedade | Valor |
|-------------|-------|
| Position | top-right, 16px from edge |
| Background | gray-900 (dark mode) |
| Color | white |
| Radius | 8px |
| Padding | 12px 16px |
| Duration | 3s (success), 5s (error) |

---

## 5. Especificacao de Telas

### 5.1 Dashboard (Home)



**Componentes:**
- Stats Cards (3 cards com metrica, valor, tendencia)
- Tabela de ultimas extracoes
- Status badges por sistema
- Botao "Nova Extracao" (primary, canto superior direito)

### 5.2 Extrair



**Componentes:**
- AddressInput com autocomplete
- Checkboxes para sistemas
- Radio group para metodo
- CostEstimator (calculo em tempo real)
- Botoes de acao

### 5.3 Execucao



**Componentes:**
- ProgressBar (por sistema)
- Timeline de estagios
- LogViewer (terminal style)
- Metricas em tempo real

### 5.4 Resultados



**Componentes:**
- Search input
- Filtros (dropdowns)
- DataTable (sortable, selectable)
- Pagination
- Bulk actions

### 5.5 Validacao



### 5.6 Configuracoes



---

## 6. Interacoes e Estados

### 6.1 Estados de Componente

| Estado | Visual | Quando |
|--------|--------|--------|
| Default | Estilo padrao | Parado |
| Hover | Leve destaque | Mouse sobre |
| Active/Focus | Ring de foco | Selecionado |
| Loading | Spinner/Skeleton | Carregando |
| Disabled | Opacidade 50% | Indisponivel |
| Error | Borda vermelha | Erro de validacao |
| Success | Borda verde | Valido |

### 6.2 Feedback Imediato

| Acao | Feedback | Duracao |
|------|----------|---------|
| Click | Ripple/Scale 0.98 | 100ms |
| Submit | Loading state | Ate resposta |
| Success | Toast verde | 3s |
| Error | Toast vermelho + detalhes | Ate fechar |
| Delete | Confirm dialog | Ate confirmar |
| Copy | Toast "Copiado!" | 2s |

### 6.3 Transicoes

| Transicao | Duracao | Easing |
|-----------|---------|--------|
| Page change | 150ms | ease-out |
| Modal open | 200ms | ease-out |
| Modal close | 150ms | ease-in |
| Toast in | 200ms | ease-out |
| Toast out | 150ms | ease-in |
| Sidebar expand | 200ms | ease-out |

---

## 7. Implementacao Tecnica

### 7.1 Stack

| Camada | Tecnologia | Versao |
|--------|------------|--------|
| Framework | Next.js | 15+ |
| React | React | 19+ |
| Styling | Tailwind CSS | 4+ |
| UI Components | shadcn/ui | latest |
| State | Zustand | 5+ |
| Forms | React Hook Form | 7+ |
| Validation | Zod | 3+ |
| Tables | TanStack Table | 8+ |
| Charts | Recharts | 2+ |
| HTTP | SWR | 2+ |
| Icons | Lucide React | latest |

### 7.2 Estrutura de Arquivos



### 7.3 Padroes de API



### 7.4 Padroes de Estado (Zustand)



---

## 8. Checklist de Implementacao

### Fase 1 (MVP - 2 semanas)

- [ ] Setup Next.js + Tailwind + shadcn/ui
- [ ] Layout base (Sidebar + Header)
- [ ] Dashboard com stats cards
- [ ] Formulario de extracao
- [ ] Tabela de resultados
- [ ] API routes basicas

### Fase 2 (Funcionalidades - 2 semanas)

- [ ] Tela de execucao com progresso
- [ ] Validacao de WhatsApp
- [ ] Fila de revisao manual
- [ ] Configuracoes (feature flags)
- [ ] Exportacao CSV/JSON

### Fase 3 (Polimento - 1 semana)

- [ ] Marketplace de integraoes
- [ ] Logs viewer avancado
- [ ] Empty states e loading states
- [ ] Animacoes e transicoes
- [ ] Testes E2E

---

## 9. Referencias de Design

| CRM | Licoes Aplicadas |
|-----|------------------|
| **Attio** | Sidebar minimalista, data density, AI-native |
| **Pipedrive** | Pipeline visual, foco em acao |
| **Linear** | Keyboard-first, velocidade, minimalismo |
| **Notion** | Empty states uteis, templates |
| **HubSpot** | Onboarding gradual, tooltips contextuais |
| **Salesforce** | Customizacao, feature flags |

---

**Fim da especificacao.**
