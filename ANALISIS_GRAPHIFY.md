# Análisis Graphify - PilotCRM & Extrator Proprietarios

> Fecha: 2026-09-08 | Graphify v0.8.1 | Modo: AST local determinístico (sin LLM)

## 1. Resumen ejecutivo

Graphify fue **instalado, configurado, activado y ejecutado** sobre ambos repositorios.
El grafo de conocimiento de **código** está operando (AST local, costo cero, determinístico).
La capa **semántica** (docs/PDFs vía LLM) queda **pendiente de credencial real**:
la OPENAI_API_KEY presente en el CRM es **demo** (no usable) y no hay
ANTHROPIC_API_KEY configurada.

| Métrica | Extrator Proprietarios | PilotCRM |
|---|---|---|
| Nodos | 1.117 | 1.464 |
| Edges | 2.237 | 3.332 |
| Comunidades | 76 | 91 |
| Confianza EXTRACTED | 82% | 99% |
| Confianza INFERRED | 18% (avg 0.68) | 1% (avg 0.80) |
| Reducción tokens/consulta | **hasta 14.2x** | - |
| Artefactos | callflow.html (17 secciones, 16 Mermaid) | igual |

## 2. Instalación y activación

### Instalado
- Binario: ~/.local/bin/graphify (paquete PyPI graphifyy==0.8.1)
- Instalado vía pip install --user graphifyy

### Configurado
- .graphifyignore en **ambos repos** (excluye: node_modules, .venv, __pycache__,
  graphify-out, datos operacionales de lotes/orquestración, supabase/, packages/, *.ndjson)
- graphify-out/ añadido al .gitignore de ambos repos (no commitea artefactos)
- Hooks git instalados y verificados (graphify hook status -> installed en ambos):
  - post-commit: reconstruye el grafo **en background** tras cada commit
    (solo código, sin LLM, no bloquea). Log: ~/.cache/graphify-rebuild.log
  - post-checkout: mismo rebuild al cambiar de rama

### Ejecutado
| Comando | Resultado |
|---|---|
| graphify extract . (extrator) | 132 código -> 1.117 nodos, 2.237 edges, 76 comunidades (5.5s) |
| graphify extract src (pilotcrm) | 463 código -> 1.464 nodos, 3.332 edges, 91 comunidades (9s) |
| graphify export callflow-html | ambos: HTML interactivo + diagramas Mermaid |
| graphify tree | ambos: GRAPH_TREE.html (árbol D3 colapsable) |
| graphify cluster-only --no-viz | ambos: GRAPH_REPORT.md por comunidades |
| graphify benchmark | extrator: 3.8x–14.2x menos tokens por consulta |

## 3. Hallazgos por repositorio

### 3.1 Extrator Proprietarios

**God nodes (abstracciones núcleo):** main(), rodar_live(), ConsolidationPipeline,
AgentBrowser, CanonicalContact, timestamp_iso(), record_key.

**Lectura del CPTO:** el grafo confirma que el acoplamiento central es main() y
rodar_live() (49 y 22 edges) y que ConsolidationPipeline + AgentBrowser son las dos
abstracciones más conectadas de la capa de agentes - coherente con la etapa M1-M3
del plan (runner común).

**Conexiones INFERRED relevantes (a verificar):**
- main() con create_app() y consolidar_multi_origem.py (14 edges inferidos)
- AgentBase con EEmovelAgent/FisgarAgent (herencia, verificar casting)

**Señal de deuda:** 478 nodos **débilmente conectados** (posible documentation gap
o fixtures de test sin enlazar) - candidato a limpiar tras cada fase.

### 3.2 PilotCRM

**God nodes:** name, columns, type, GET(), POST(), primaryKey, notNull - más de 50
edges cada uno. Traducción: la app está muy centrada en **tablas/schemas (CRUD
genérico)** y **rutas API REST** - arquitectura esperada de un CRM.

**Conexiones sorprendentes INFERRED (las valiosas del grafo):**
- normalizeExtracted() hacia normalizeEmail() (modules/captacao/extraction.ts hacia lib/import/dedup.ts)
- GET() hacia DashboardSummary (admin/tenants hacia lib/demo-analytics.ts)
- AdminDashboardPage hacia getPlanUsageSummary() (demo-billing)
- PATCH/DELETE hacia getTenantId() (tenancy en admin users) - confirma multi-tenant

**Señal de design:** 403 nodos débilmente conectados y 39 edges INFERRED alrededor de
GET() - candidatos a verificación con tipos reales (tsc) antes de confiar.

## 4. Recomendaciones (orden de impacto)

1. **Mantener el nodo de código operando** y re-ejecutar tras cada fase del plan
   (graphify update . - actual es automático vía hook post-commit).
2. **Activar capa semántica** cuando exista una API key real (Anthropic/OpenAI/Gemini):
   extraerá docs (.md), PDFs y arquitectura en el mismo grafo (multi-modal).
   Costo estimado actual: ~0.40 USD/M input + 1.60 USD/M output (GPT-4.1-mini).
3. **Acceso por CLI a todo el grafo**: graphify path X Y, graphify explain Z,
   graphify query - ideal para onboarding de nuevos devs y auditoría CPTO.
4. **Verificar los edges INFERRED de mayor confianza** (confidence >= 0.8) para
   evitar que el grafo perpetúe suposiciones incorrectas.
5. **No commitear graphify-out/**: ya en .gitignore; consumir GRAPH_REPORT.md
   y callflow.html como artefactos locales.

## 5. Estado final

| Item | Estado |
|---|---|
| Instalación | OK graphify 0.8.1 |
| Configuración | OK .graphifyignore + .gitignore + hooks en ambos repos |
| Activación | OK hooks post-commit/post-checkout instalados y verificados |
| Ejecución | OK AST completo en ambos (5.5s + 9s) |
| Capa semántica | pendiente de API key real (la del CRM es demo) |
| Documentación | OK este informe en cada repo |


## 6. Comandos útiles

    export OPENAI_API_KEY=...   # o ANTHROPIC_API_KEY / GEMINI_API_KEY
    graphify update .          # re-extraer código (sin LLM, vía hook automático)
    graphify extract .         # extracción completa (código + semántica con key)
    graphify path A B          # camino más corto entre dos nodos
    graphify explain C         # explicación de un nodo y sus vecinos
    graphify query "pregunta"  # recorrido del grafo guiado por pregunta

Artefactos generados en graphify-out/: graph.html, GRAPH_REPORT.md, callflow.html,
GRAPH_TREE.html, graph.json (persistente), cache/ (incremental).
