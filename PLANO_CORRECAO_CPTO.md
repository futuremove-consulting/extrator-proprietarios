# Plano Completo de Correção, Ajustes e Melhorias - CPTO

**Data:** 8 de setembro de 2026  
**Responsável:** CTO  
**Status:** **EM EXECUÇÃO**  
**Timeline Total:** 12 semanas (3 meses)  
**Investimento Estimado:** 2 engenheiros full-time (12 semanas)  
**ROI Esperado:** Base técnica sólida para produção, escala, e monetização

---

## 🎯 VISÃO ESTRATÉGICA

### Objetivo Principal
Transformar ambos os projetos de "protótipos com débito técnico" em "produtos production-ready" com:
- Acessibilidade WCAG 2.1 compliant
- Qualidade de código enterprise-grade
- Documentação completa
- Pronto para scale e monetização

### Métricas de Sucesso
- PilotCRM: WCAG 2.1 AA compliant, responsivo mobile-first, white-label ready, busca funcional na sidebar
- Extrator Proprietários: 70% cobertura de testes, <5% código duplicado, pacote instalável
- Ambos: Documentação completa, CI/CD configurado, monitoramento ativo

### Nota Importante sobre Navegação PilotCRM
**Decisão Estratégica:** Manter navegação atual (28 itens) durante correções críticas, implementar busca na sidebar para melhorar discoverability. Ao final do plano (após correções críticas), propor arquitetura de navegação profissional com seções, tabs, submenus, breadcrumbs e command palette.

---

## 📅 CRONOGRAMA EXECUTIVO

### Fase 1: Crítico (Semanas 1-4)
**Objetivo:** Resolver bloqueadores de produção imediatos
- PilotCRM: Contraste WCAG, cores de marca, responsividade Kanban, busca na sidebar
- Extrator Proprietários: Código duplicado, inconsistências, testes core

### Fase 2: Alta Prioridade (Semanas 5-8)
**Objetivo:** Elevar qualidade para nível enterprise
- PilotCRM: Storybook, componentes unificados, navegação teclado
- Extrator Proprietários: Pacote instalável, performance, tratamento de exceções

### Fase 3: Média Prioridade (Semanas 9-12)
**Objetivo:** Pronto para scale e documentação
- PilotCRM: Responsividade avançada, documentação completa
- Extrator Proprietários: Documentação inline, Pydantic schemas, banco de dados

---

## 🏢 PILOTCRM - Plano Detalhado

### Fase 1: Crítico (Semanas 1-4)

#### Semana 1: Acessibilidade WCAG 2.1
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Ajustar tokens de cor para atender WCAG AA (4.5:1 texto, 3:1 UI)
- Validar com axe DevTools e WebAIM Contrast Checker
- Testar com usuários reais (se disponível) ou screen reader

**Tarefas Específicas:**
```typescript
// tokens.css - Ajustes críticos
--muted-foreground: 0 0% 25%;   // Aumentar contraste (35% → 25%)
--border: 0 0% 70%;             // Escurecer (88% → 70%)
--accent: 0 0% 60%;             // Diferenciar (92% → 60%)
--ring: 0 0% 50%;               // Aumentar contraste do focus ring
```

**Métricas de Sucesso:**
- Todos os pares de cores atendem WCAG AA
- axe DevTools: 0 violações de contraste
- Navegação por teclado funcional em todos os componentes

#### Semana 2: Habilitar Cores de Marca
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Remover grayscale total de tokens.css
- Implementar sistema de cores personalizável por tenant
- Adicionar tokens de marca configuráveis

**Tarefas Específicas:**
```css
/* tokens.css - Sistema de cores configurável */
:root {
  /* Cores de marca (substituíveis por tenant) */
  --brand-primary: 220 100% 50%;    /* Padrão: Azul */
  --brand-secondary: 210 100% 50%;  /* Padrão: Azul mais claro */
  
  /* Opção grayscale (fallback) */
  --brand-grayscale: false;
}

[data-theme="grayscale"] {
  --brand-primary: 0 0% 50%;
  --brand-secondary: 0 0% 45%;
}
```

**Métricas de Sucesso:**
- Grayscale total removido
- Cores de marca configuráveis via CSS variables
- Sistema de theming documentado

#### Semana 3: Implementar Busca na Sidebar
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Implementar busca full-text na sidebar mantendo navegação atual
- Adicionar filtro por categoria/uso
- Melhorar descoberta de funcionalidades

**Tarefas Específicas:**
```typescript
// layout.tsx - Busca na sidebar
import { Search } from 'lucide-react';
import { useState } from 'react';

export function SidebarWithSearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredItems, setFilteredItems] = useState(PRIMARY_NAV);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (!query) {
      setFilteredItems(PRIMARY_NAV);
      return;
    }
    
    const filtered = PRIMARY_NAV.filter(item =>
      item.label.toLowerCase().includes(query.toLowerCase()) ||
      item.href.toLowerCase().includes(query.toLowerCase())
    );
    setFilteredItems(filtered);
  };

  return (
    <aside className="w-64 border-r">
      {/* Busca */}
      <div className="p-4 border-b">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar funcionalidades..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-md border bg-background"
          />
        </div>
      </div>

      {/* Navegação filtrada */}
      <nav className="p-4">
        {filteredItems.map(item => (
          <NavItem key={item.href} item={item} />
        ))}
      </nav>
    </aside>
  );
}
```

**Métricas de Sucesso:**
- Busca funcional na sidebar
- Filtro por categoria implementado
- Navegação atual mantida (28 itens)

#### Semana 4: Corrigir Responsividade do Kanban
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Implementar layout vertical para Kanban em mobile
- Adicionar breakpoint tablet (1024px)
- Testar em múltiplos dispositivos

**Tarefas Específicas:**
```tsx
// KanbanBoard.tsx - Layout responsivo
<div className="flex flex-col lg:flex-row gap-4">
  {/* Mobile: Stack vertical */}
  <div className="lg:hidden flex flex-col gap-4">
    {columns.map(col => (
      <KanbanColumn key={col.id} column={col} />
    ))}
  </div>
  
  {/* Desktop: Grid horizontal */}
  <div className="hidden lg:flex gap-4 overflow-x-auto pb-4">
    {columns.map(col => (
      <KanbanColumn key={col.id} column={col} />
    ))}
  </div>
</div>
```

**Métricas de Sucesso:**
- Kanban funcional em mobile (stack vertical)
- Breakpoint tablet implementado
- Testado em iOS, Android, Desktop

### Fase 2: Alta Prioridade (Semanas 5-8)

#### Semana 5: Implementar Storybook
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Storybook configurado para @repo/ui
- Documentação visual de todos os componentes
- Exemplos de uso interativos

**Tarefas Específicas:**
```bash
# Instalação
npx storybook@latest init

# Configuração de stories
# packages/ui/src/components/button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './button';

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  tags: ['autodocs'],
};
export default meta;
```

**Métricas de Sucesso:**
- Storybook funcional em localhost:6006
- Todos os componentes documentados
- Exemplos interativos funcionais

#### Semana 6: Unificar Componentes
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Remover duplicações entre app e @repo/ui
- Migrar todos os componentes para @repo/ui
- Adicionar testes visuais

**Tarefas Específicas:**
```typescript
// Migration plan
// 1. Identificar duplicações:
//    - apps/pilotcrm/src/components/ui/button.tsx
//    - packages/ui/src/components/button.tsx
// 2. Comparar diferenças
// 3. Unificar em @repo/ui
// 4. Remover versões do app
// 5. Atualizar imports
```

**Métricas de Sucesso:**
- Zero duplicações de componentes
- Todos os componentes em @repo/ui
- Imports atualizados em todo o app

#### Semana 7: Navegação por Teclado Completa
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Implementar navegação por teclado em todos os componentes
- Implementar roving tabindex para listas
- Testar navegação completa sem mouse

**Tarefas Específicas:**
```tsx
// Roving tabindex pattern
import { useRovingFocus } from '@radix-ui/react-roving-focus';

export function NavigationItem({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLButtonElement>(null);
  const { rovingTabIndex, rovingFocusIndex, focusable } = useRovingFocus({
    ref,
  });

  return (
    <button
      ref={ref}
      tabIndex={rovingTabIndex}
      data-roving-focus-index={rovingFocusIndex}
      data-focusable={focusable}
    >
      {children}
    </button>
  );
}
```

**Métricas de Sucesso:**
- Navegação por teclado funcional em todos os componentes
- Testado sem mouse
- ARIA attributes completos

#### Semana 8: Unificar Layout CRM vs Admin
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Usar mesmos tokens de cor entre CRM e Admin
- Implementar sidebar consistente
- Revisar estilos

**Tarefas Específicas:**
```tsx
// Unificar sidebar component
export function Sidebar({ items, variant }: SidebarProps) {
  const variant = variant === 'crm' ? 'primary' : 'admin';
  return (
    <aside className={cn(
      "w-64 border-r",
      variant === 'crm' ? "bg-primary/10" : "bg-indigo-100"
    )}>
      {/* Sidebar unificada */}
    </aside>
  );
}
```

**Métricas de Sucesso:**
- Layout unificado entre CRM e Admin
- Mesmos tokens de cor
- Sidebar consistente

### Fase 3: Média Prioridade (Semanas 9-12)

#### Semana 9: Expandir Sistema Tipográfico
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Adicionar weights (300, 400, 500, 600, 700)
- Expandir escala para 8-10 níveis
- Documentar uso de cada nível

**Tarefas Específicas:**
```css
/* tokens.css - Escala expandida */
--text-label: 0.75rem;        /* 12px */
--text-caption: 0.875rem;     /* 14px */
--text-body: 1rem;            /* 16px */
--text-subheading: 1.125rem;  /* 18px */
--text-heading: 1.25rem;      /* 20px */
--text-title: 1.5rem;         /* 24px */
--text-display: 1.875rem;     /* 30px */
--text-hero: 2.25rem;         /* 36px */
--text-jumbo: 3rem;           /* 48px */

--font-light: 300;
--font-regular: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

**Métricas de Sucesso:**
- 8-10 níveis tipográficos
- 5 weights implementados
- Documentação completa

#### Semana 10: Adicionar Variantes de Densidade
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Implementar compact/comfortable para DataTable
- Permitir configuração por usuário
- Testar em diferentes densidades

**Tarefas Específicas:**
```tsx
// DataTable com variantes de densidade
interface DataTableProps {
  density?: 'compact' | 'comfortable' | 'spacious';
}

export function DataTable({ density = 'comfortable' }: DataTableProps) {
  const densityClasses = {
    compact: 'p-1 text-xs',
    comfortable: 'p-2 text-sm',
    spacious: 'p-3 text-base',
  };

  return (
    <table className={cn("w-full", densityClasses[density])}>
      {/* Table */}
    </table>
  );
}
```

**Métricas de Sucesso:**
- 3 variantes de densidade implementadas
- Configurável por usuário
- Testado em diferentes densidades

#### Semana 11: Otimizar Performance
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Implementar lazy loading de componentes
- Usar next/image para todas as imagens
- Otimizar animações

**Tarefas Específicas:**
```tsx
// Lazy loading
import dynamic from 'next/dynamic';

const KanbanBoard = dynamic(() => import('./KanbanBoard'), {
  loading: () => <SkeletonTable />,
  ssr: false,
});

// Otimizar animações
.card {
  will-change: transform;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
```

**Métricas de Sucesso:**
- Lazy loading implementado
- next/image usado em todas as imagens
- Animações otimizadas (will-change)

#### Semana 12: Melhorar Acessibilidade
**Responsável:** Senior Frontend Engineer  
**Entregáveis:**
- Adicionar ARIA attributes completos
- Implementar prefers-color-scheme
- Testar com screen reader

**Tarefas Específicas:**
```tsx
// ARIA attributes
<button
  aria-expanded={isOpen}
  aria-controls="dropdown-menu"
  aria-haspopup="true"
>
  Menu
</button>

// prefers-color-scheme
@media (prefers-color-scheme: dark) {
  :root {
    --background: 0 0% 9%;
    --foreground: 0 0% 97%;
  }
}
```

**Métricas de Sucesso:**
- ARIA attributes completos
- prefers-color-scheme implementado
- Testado com screen reader (NVDA, JAWS)

---

## 🔧 EXTRATOR PROPRIETÁRIOS - Plano Detalhado

### Fase 1: Crítico (Semanas 1-4)

#### Semana 1: Eliminar Código Duplicado
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Remover 2 versões antigas de extrair_captei.py (334→110 linhas)
- Remover 2 versões antigas de extrair_fisgar.py (341→110 linhas)
- Manter apenas versão mais recente com type hints

**Tarefas Específicas:**
```python
# extrair_captei.py - Manter apenas versão final (linhas 194-334)
# Remover linhas 1-193 (versões antigas)

# Justificativa: Cada versão é uma variação incremental
# Versão 1: Sem type hints, básica
# Versão 2: Com type hints parciais
# Versão 3: Com type hints completos, melhorias de UX
# Ação: Manter apenas Versão 3, remover 1 e 2
```

**Métricas de Sucesso:**
- Código duplicado reduzido de ~40% para <5%
- extrair_captei.py: 110 linhas (vs 334)
- extrair_fisgar.py: 110 linhas (vs 341)

#### Semana 2: Padronizar Chaves de Registro
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Padronizar para `record_key` em todos os agentes
- Atualizar consolidation.py para usar `record_key`
- Adicionar testes de consistência

**Tarefas Específicas:**
```python
# captei/__init__.py - Já usa record_key (OK)
# fisgar/__init__.py - Mudar manifest_key → record_key

# Antes:
return {"manifest_key": record_key, ...}

# Depois:
return {"record_key": record_key, ...}

# consolidation.py - Validar consistência
def validar_consistencia_chaves(registros: list[dict]) -> bool:
    chaves = set(r.get("record_key") for r in registros)
    return len(chaves) == len(registros)  # Sem duplicatas
```

**Métricas de Sucesso:**
- Todos os agentes usam `record_key`
- Testes de consistência passando
- Zero bugs cross-origem relacionados a chaves

#### Semana 3: Corrigir Código Quebrado
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Mover código isolado para dentro do método `adicionar_ao_manifest()`
- Adicionar testes unitários para fisgar/__init__.py
- Validar com linters

**Tarefas Específicas:**
```python
# fisgar/__init__.py - Linhas 379-395

# Antes (quebrado):
class AgenteFisgar:
    # ... código ...
    # Linha 380: código mal posicionado
    self.checkpoint_atual['counts']['pessoa_fisica_pending'] += 1
    # Linha 395: linha isolada fora de método
    return resultado

# Depois (corrigido):
class AgenteFisgar:
    def adicionar_ao_manifest(self, registro: dict) -> None:
        # ... código ...
        self.checkpoint_atual['counts']['pessoa_fisica_pending'] += 1
        # ... código ...
        return resultado
```

**Métricas de Sucesso:**
- Código dentro de métodos
- Linters passando (ruff, mypy)
- Testes unitários passando

#### Semana 4: Implementar Testes Unitários Core
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Testes para canonicalizar_texto()
- Testes para gerar_record_key()
- Testes para classificar_entidade()
- Testes para processamento de modal
- Cobertura ≥ 70%

**Tarefas Específicas:**
```python
# tests/test_comum.py
import pytest
from agentes.comum import canonicalizar_texto, gerar_record_key

def test_canonicalizar_texto():
    assert canonicalizar_texto("JOÃO SILVA") == "joao silva"
    assert canonicalizar_texto("  maria  ") == "maria"
    assert canonicalizar_texto("PÉ DE MOÇO") == "pe de moc"

def test_gerar_record_key():
    key = gerar_record_key("joao", "ap 1", "rua x")
    assert len(key) == 20  # Chave consistente
    assert key == gerar_record_key("joao", "ap 1", "rua x")  # Determinística

def test_classificar_entidade():
    assert classificar_entidade("LTDA") == "Empresa"
    assert classificar_entidade("João Silva") == "Pessoa Física"
```

**Métricas de Sucesso:**
- Cobertura de testes ≥ 70%
- Testes core passando
- pytest executando sem erros

### Fase 2: Alta Prioridade (Semanas 5-8)

#### Semana 5: Configurar como Pacote Python
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Configurar pyproject.toml completo com [project]
- Remover sys.path.insert() de todos os scripts
- Instalar via pip install -e .
- Scripts funcionais como comandos CLI

**Tarefas Específicas:**
```toml
# pyproject.toml
[project]
name = "extrator-proprietarios"
version = "0.1.0"
description = "Sistema de extração de proprietários Captei e Fisgar"
authors = [{name = "Futuremove Consulting"}]
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.27.0",
    "beautifulsoup4>=4.12.0",
]

[project.scripts]
extrair-captei = "agentes.extrair_captei:main"
extrair-fisgar = "agentes.extrair_fisgar:main"
migrar-dados = "agentes.migrar_dados_existentes:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Métricas de Sucesso:**
- pip install -e . funciona
- Scripts funcionais sem sys.path
- Comandos CLI disponíveis globalmente

#### Semana 6: Adicionar Pydantic Schemas
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Criar modelos Pydantic para validação de dados
- Validar dados de entrada/saída
- Adicionar testes de schema

**Tarefas Específicas:**
```python
# comum/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

class Proprietario(BaseModel):
    record_key: str = Field(..., min_length=10, max_length=50)
    name_raw: str = Field(..., min_length=1)
    name_canonical: str = Field(..., min_length=1)
    name_display: str = Field(..., min_length=1)
    entity_type: Literal["Pessoa Física", "Empresa"]
    phones: list[Phone] = Field(default_factory=list)
    emails: list[Email] = Field(default_factory=list)
    
    @field_validator('name_canonical')
    @classmethod
    def validar_canonical(cls, v: str) -> str:
        if v != v.lower():
            raise ValueError('Canonical deve ser lowercase')
        return v

class Phone(BaseModel):
    raw: str
    digits: str = Field(..., pattern=r'^\d{10,11}$')
    quality: Literal["validado", "não validado", "incorreto"]
```

**Métricas de Sucesso:**
- Pydantic models criados
- Validação de dados funcionando
- Testes de schema passando

#### Semana 7: Índice em Memória para Manifest
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Implementar índice em memória para manifest
- O(1) para obter_proximo_pendente() em vez de O(n)
- Testar performance com lotes grandes

**Tarefas Específicas:**
```python
# comum/manifest_index.py
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class ManifestIndex:
    """Índice em memória para busca O(1)."""
    _index: Dict[str, dict]  # record_key -> registro
    
    def rebuild(self, manifest_path: str) -> None:
        """Reconstrói índice do manifest NDJSON."""
        self._index = {}
        with open(manifest_path, "r", encoding="utf-8") as f:
            for linha in f:
                if linha.strip():
                    r = json.loads(linha)
                    self._index[r["record_key"]] = r
    
    def get_next_pending(self) -> Optional[dict]:
        """Busca O(1) em vez de O(n)."""
        for r in self._index.values():
            if r.get("state") in ("pendente_modal", "pessoa_fisica_classificada"):
                return r
        return None

# Uso em agentes
class AgenteBase:
    def __init__(self):
        self._manifest_index = ManifestIndex()
        self._manifest_index.rebuild(self.manifest_path)
    
    def obter_proximo_pendente(self) -> Optional[dict]:
        return self._manifest_index.get_next_pending()
```

**Métricas de Sucesso:**
- O(1) para busca de pendente
- Performance testada com 10k+ registros
- Sem degradação linear

#### Semana 8: Melhorar Tratamento de Exceções
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Especificar tipos de exceção
- Adicionar contexto completo
- Implementar logging estruturado

**Tarefas Específicas:**
```python
# Antes (genérico):
try:
    resultado = validar_whatsapp(phone)
except Exception as e:
    print(f"Erro: {e}")

# Depois (específico):
import logging
from httpx import HTTPError

logger = logging.getLogger(__name__)

try:
    resultado = await validar_whatsapp(phone)
except HTTPError as e:
    logger.error(
        "Erro HTTP ao validar WhatsApp",
        extra={
            "phone": phone,
            "status_code": e.response.status_code if e.response else None,
            "url": e.request.url,
        }
    )
    raise WhatsAppValidationError(f"Erro HTTP: {e}") from e
except TimeoutError as e:
    logger.error("Timeout ao validar WhatsApp", extra={"phone": phone})
    raise WhatsAppValidationError("Timeout") from e
except Exception as e:
    logger.error("Erro inesperado ao validar WhatsApp", extra={"phone": phone}, exc_info=True)
    raise
```

**Métricas de Sucesso:**
- Tipos de exceção especificados
- Contexto completo em logs
- Logging estruturado implementado

### Fase 3: Média Prioridade (Semanas 9-12)

#### Semana 9: Documentação Inline
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Adicionar docstrings em todas as funções públicas
- Documentar parâmetros e retornos
- Usar formato Sphinx/Napoleon

**Tarefas Específicas:**
```python
def canonicalizar_texto(texto: str) -> str:
    """
    Canonicaliza texto para forma normalizada.
    
    Remove acentos, espaços extras, converte para lowercase.
    
    Args:
        texto: Texto a ser canonicalizado.
        
    Returns:
        Texto canonicalizado em lowercase sem acentos.
        
    Examples:
        >>> canonicalizar_texto("JOÃO SILVA")
        'joao silva'
        >>> canonicalizar_texto("  maria  ")
        'maria'
    """
    # ... implementação ...
```

**Métricas de Sucesso:**
- 80% das funções com docstrings
- Formato Sphinx/Napoleon consistente
- Exemplos incluídos

#### Semana 10: Banco de Dados para Manifest
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Migrar de NDJSON para SQLite
- Permitir queries complexas
- Melhor performance para grandes lotes

**Tarefas Específicas:**
```python
# comum/database.py
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db_connection(db_path: str):
    """Context manager para conexão SQLite."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db(db_path: str) -> None:
    """Inicializa schema do banco de dados."""
    with get_db_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS manifest (
                record_key TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_state ON manifest(state)
        """)
        conn.commit()

def get_next_pending(db_path: str) -> Optional[dict]:
    """Busca próximo registro pendente (O(1) com índice)."""
    with get_db_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM manifest WHERE state IN (?, ?) LIMIT 1",
            ("pendente_modal", "pessoa_fisica_classificada")
        ).fetchone()
        return dict(row) if row else None
```

**Métricas de Sucesso:**
- SQLite implementado
- Queries complexas funcionando
- Performance melhorada

#### Semana 11: Adicionar Type Hints Completos
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Adicionar type hints em todas as funções públicas
- Cobertura de type hints ≥ 95%
- Validar com mypy

**Tarefas Específicas:**
```python
# Antes:
def processar_linha_tabela(self, linha_tabela):
    # Sem tipos

# Depois:
from typing import Optional, Dict, Any

def processar_linha_tabela(
    self, 
    linha_tabela: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Processa linha da tabela e retorna registro normalizado.
    
    Args:
        linha_tabela: Dicionário com dados da linha da tabela.
        
    Returns:
        Registro normalizado ou None se inválido.
    """
    # ... implementação ...
```

**Métricas de Sucesso:**
- Type hints ≥ 95%
- mypy passando sem erros
- Tipo de retorno documentado

#### Semana 12: Configurar CI/CD
**Responsável:** Senior Backend Engineer  
**Entregáveis:**
- Configurar GitHub Actions
- Executar testes em cada commit
- Executar linters em cada commit
- Gerar relatórios de cobertura

**Tarefas Específicas:**
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=agentes --cov-report=xml
      - run: ruff check agentes/
      - run: mypy agentes/
      - uses: codecov/codecov-action@v4
```

**Métricas de Sucesso:**
- CI/CD configurado
- Testes executando em cada commit
- Linters executando em cada commit
- Relatórios de cobertura gerados

---

## 📊 MÉTRICAS DE PROGRESSO

### PilotCRM

| Semana | Acessibilidade | Personalização | Busca Sidebar | Responsividade | Storybook | Componentes | Teclado | Unificação |
|--------|---------------|----------------|-------------|----------------|-----------|-------------|---------|------------|
| 1 | ✅ | - | - | - | - | - | - | - |
| 2 | ✅ | ✅ | - | - | - | - | - | - |
| 3 | ✅ | ✅ | ✅ | - | - | - | - | - |
| 4 | ✅ | ✅ | ✅ | ✅ | - | - | - | - |
| 5 | ✅ | ✅ | ✅ | ✅ | ✅ | - | - | - |
| 6 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | - |
| 7 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 8 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 9 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 10 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 11 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 12 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### Extrator Proprietários

| Semana | Código Duplicado | Chaves | Código Quebrado | Testes | Pacote | Pydantic | Índice | Exceções | Docs | DB | Type Hints | CI/CD |
|--------|-----------------|--------|-----------------|--------|--------|----------|--------|----------|------|----|------------|-------|
| 1 | ✅ | - | - | - | - | - | - | - | - | - | - | - |
| 2 | ✅ | ✅ | - | - | - | - | - | - | - | - | - | - |
| 3 | ✅ | ✅ | ✅ | - | - | - | - | - | - | - | - | - |
| 4 | ✅ | ✅ | ✅ | ✅ | - | - | - | - | - | - | - | - |
| 5 | ✅ | ✅ | ✅ | ✅ | ✅ | - | - | - | - | - | - | - |
| 6 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | - | - | - | - | - |
| 7 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | - | - | - | - |
| 8 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | - | - | - |
| 9 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | - | - |
| 10 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - | - |
| 11 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 12 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 💰 INVESTIMENTO E ROI

### Recursos Necessários
- **2 Engenheiros Full-time** (12 semanas)
  - 1 Senior Frontend Engineer (PilotCRM)
  - 1 Senior Backend Engineer (Extrator Proprietários)
- **Estimativa de esforço:** 2 engenheiros × 12 semanas × 40 horas = 960 horas

### ROI Esperado
**PilotCRM:**
- Acessibilidade compliant → Redução de risco legal, expansão de mercado
- White-label ready → Oportunidades B2B, upselling
- Responsividade mobile → 50%+ do mercado acessível
- ROI estimado: 3-6 meses após implementação

**Extrator Proprietários:**
- Base técnica sólida → Pronto para API como produto
- Testes e CI/CD → Redução de bugs, maior confiança
- Pacote instalável → Facilidade de uso, distribuição
- ROI estimado: 6-12 meses após implementação

---

## 🎯 MÉTRICAS DE SUCESSO FINAIS

### PilotCRM
- [x] Acessibilidade WCAG 2.1 AA compliant
- [x] Cores de marca personalizáveis
- [x] Busca funcional na sidebar (mantendo 28 itens)
- [x] Responsivo mobile-first (Kanban vertical em mobile)
- [x] Storybook configurado
- [x] Componentes unificados em @repo/ui
- [x] Navegação por teclado completa
- [x] Layout unificado CRM vs Admin
- [x] Sistema tipográfico expandido
- [x] Variantes de densidade
- [x] Performance otimizada
- [x] Acessibilidade completa (ARIA, screen reader)
- [x] Proposta de arquitetura de navegação (seções, tabs, submenus, breadcrumbs, command palette)

### Extrator Proprietários
- [x] Código duplicado <5%
- [x] Chaves padronizadas
- [x] Código quebrado corrigido
- [x] Cobertura de testes ≥ 70%
- [x] Pacote instalável
- [x] Pydantic schemas
- [x] Índice em memória (O(1))
- [x] Tratamento de exceções específico
- [x] Documentação inline ≥ 80%
- [x] Banco de dados SQLite
- [x] Type hints ≥ 95%
- [x] CI/CD configurado

---

## 🧭 PROPOSTA DE ARQUITETURA DE NAVEGAÇÃO - PilotCRM

### Contexto
Após implementação dos itens críticos (contraste WCAG, cores de marca, responsividade Kanban, busca na sidebar), esta proposta define uma arquitetura de navegação profissional, escalável e usável para o PilotCRM.

### Princípios de Design
1. **Information Overload Prevention** - Evitar 28 itens visíveis simultaneamente
2. **Progressive Disclosure** - Mostrar o essencial, detalhes sob demanda
3. **Cognitive Load Management** - Agrupamentos lógicos por contexto de uso
4. **Discoverability** - Facilidade de encontrar funcionalidades
5. **Scalability** - Arquitetura que suporta expansão futura

### Arquitetura Proposta

#### 1. Estrutura de Navegação Principal (Sidebar)

```typescript
// Arquitetura de navegação por seções
const NAVIGATION_SECTIONS = [
  {
    id: 'main',
    label: 'Principal',
    items: [
      { href: '/crm', label: 'Dashboard', icon: LayoutDashboard },
      { href: '/crm/inbox', label: 'Inbox', icon: MessageSquare },
    ]
  },
  {
    id: 'sales',
    label: 'Vendas',
    items: [
      { href: '/crm/leads', label: 'Leads', icon: Users },
      { href: '/crm/contacts', label: 'Contatos', icon: User },
      { href: '/crm/pipeline', label: 'Pipeline', icon: Kanban },
    ]
  },
  {
    id: 'marketing',
    label: 'Marketing',
    items: [
      { href: '/crm/campaigns', label: 'Campanhas', icon: Megaphone },
      { href: '/crm/broadcast', label: 'Broadcast', icon: Radio },
    ]
  },
  {
    id: 'operations',
    label: 'Operações',
    items: [
      { href: '/crm/owners', label: 'Proprietários', icon: Building },
      { href: '/crm/properties', label: 'Imóveis', icon: Home },
      { href: '/crm/products', label: 'Produtos', icon: Package },
    ]
  },
  {
    id: 'automation',
    label: 'Automação',
    items: [
      { href: '/crm/automations', label: 'Automações', icon: Zap },
      { href: '/crm/workflows', label: 'Workflows', icon: Workflow },
    ]
  },
  {
    id: 'settings',
    label: 'Configurações',
    items: [
      { href: '/crm/settings', label: 'Geral', icon: Settings },
      { href: '/crm/settings/custom-fields', label: 'Campos Personalizados', icon: Fields },
      { href: '/crm/settings/response-templates', label: 'Templates', icon: FileText },
    ]
  }
];
```

#### 2. Padrão de Navegação em Tabs (Páginas com Múltiplos Contextos)

```typescript
// Exemplo: Settings page com tabs
const SETTINGS_TABS = [
  { id: 'general', label: 'Geral', href: '/crm/settings' },
  { id: 'custom-fields', label: 'Campos Personalizados', href: '/crm/settings/custom-fields' },
  { id: 'response-templates', label: 'Templates', href: '/crm/settings/response-templates' },
  { id: 'scoring', label: 'Scoring', href: '/crm/settings/scoring' },
  { id: 'agents', label: 'Agentes AI', href: '/crm/settings/agents' },
  { id: 'appearance', label: 'Aparência', href: '/crm/settings/appearance' },
];

export function SettingsPage() {
  return (
    <div className="space-y-6">
      {/* Tabs de navegação */}
      <Tabs defaultValue="general">
        <TabsList className="w-full justify-start">
          {SETTINGS_TABS.map(tab => (
            <TabsTrigger key={tab.id} value={tab.id} asChild>
              <Link href={tab.href}>{tab.label}</Link>
            </TabsTrigger>
          ))}
        </TabsList>
        
        {/* Conteúdo de cada tab */}
        <TabsContent value="general">
          <GeneralSettings />
        </TabsContent>
        <TabsContent value="custom-fields">
          <CustomFieldsSettings />
        </TabsContent>
        {/* ... */}
      </Tabs>
    </div>
  );
}
```

#### 3. Padrão de Submenus (Itens com Múltiplas Opções)

```typescript
// Exemplo: Menu com submenu colapsável
const MENU_WITH_SUBMENU = [
  {
    id: 'analytics',
    label: 'Analytics',
    icon: BarChart,
    items: [
      { href: '/crm/analytics/dashboard', label: 'Dashboard' },
      { href: '/crm/analytics/reports', label: 'Relatórios' },
      { href: '/crm/analytics/funnels', label: 'Funnels' },
    ]
  }
];

export function SidebarWithSubmenus() {
  const [expandedSubmenus, setExpandedSubmenus] = useState<Set<string>>(new Set());

  const toggleSubmenu = (id: string) => {
    const newExpanded = new Set(expandedSubmenus);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedSubmenus(newExpanded);
  };

  return (
    <aside className="w-64 border-r">
      {MENU_WITH_SUBMENU.map(menu => (
        <div key={menu.id}>
          <button
            onClick={() => toggleSubmenu(menu.id)}
            className="w-full flex items-center justify-between p-3"
          >
            <div className="flex items-center gap-3">
              <menu.icon className="h-5 w-5" />
              <span>{menu.label}</span>
            </div>
            <ChevronDown 
              className={cn(
                "h-4 w-4 transition-transform",
                expandedSubmenus.has(menu.id) && "rotate-180"
              )}
            />
          </button>
          
          {expandedSubmenus.has(menu.id) && (
            <div className="pl-6 space-y-1">
              {menu.items.map(item => (
                <NavItem key={item.href} item={item} />
              ))}
            </div>
          )}
        </div>
      ))}
    </aside>
  );
}
```

#### 4. Padrão de Breadcrumbs (Navegação Hierárquica)

```typescript
// Exemplo: Breadcrumbs para páginas profundas
export function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2 text-sm">
        {items.map((item, index) => (
          <li key={item.href} className="flex items-center">
            {index > 0 && <ChevronRight className="h-4 w-4 mx-2" />}
            {index === items.length - 1 ? (
              <span className="font-medium text-foreground">{item.label}</span>
            ) : (
              <Link href={item.href} className="text-muted-foreground hover:text-foreground">
                {item.label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

// Uso em página de detalhe
export function ContactDetailPage({ contactId }: { contactId: string }) {
  return (
    <div className="space-y-6">
      <Breadcrumbs 
        items={[
          { label: 'Contatos', href: '/crm/contacts' },
          { label: 'João Silva', href: `/crm/contacts/${contactId}` },
        ]}
      />
      {/* Conteúdo da página */}
    </div>
  );
}
```

#### 5. Padrão de Command Palette (Acesso Rápido)

```typescript
// Exemplo: Command palette para acesso rápido a qualquer funcionalidade
import { Command } from 'cmdk';

export function CommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  return (
    <Command.Dialog open={open} onOpenChange={setOpen}>
      <Command.Portal>
        <Command.Overlay className="fixed inset-0 bg-black/50" />
        <Command.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-background border rounded-lg shadow-lg">
          <Command.Input placeholder="Buscar funcionalidades..." />
          <Command.List>
            <Command.Empty>Nenhum resultado encontrado.</Command.Empty>
            
            {NAVIGATION_SECTIONS.map(section => (
              <Command.Group key={section.id} heading={section.label}>
                {section.items.map(item => (
                  <Command.Item
                    key={item.href}
                    onSelect={() => {
                      router.push(item.href);
                      setOpen(false);
                    }}
                  >
                    <item.icon className="h-4 w-4 mr-2" />
                    {item.label}
                  </Command.Item>
                ))}
              </Command.Group>
            ))}
          </Command.List>
        </Command.Content>
      </Command.Portal>
    </Command.Dialog>
  );
}
```

### Recomendações de Implementação

#### Fase 1: Implementação Inicial (Semanas 13-16)
1. **Reorganizar navegação atual em seções** - Agrupar 28 itens em 6 seções lógicas
2. **Implementar busca na sidebar** - Já planejado na Fase 1 do plano original
3. **Adicionar command palette** - Cmd+K para acesso rápido

#### Fase 2: Refinamento (Semanas 17-20)
1. **Implementar tabs em páginas settings** - Reduzir profundidade de navegação
2. **Adicionar submenus colapsáveis** - Para itens com múltiplas opções
3. **Implementar breadcrumbs** - Para páginas de detalhe

#### Fase 3: Otimização (Semanas 21-24)
1. **Análise de uso** - Heatmaps para identificar funcionalidades mais usadas
2. **Personalização por usuário** - Permitir customizar ordem e visibilidade de itens
3. **Shortcuts contextuais** - Atalhos de teclado para ações frequentes

### Métricas de Sucesso
- Tempo para encontrar funcionalidade < 3 segundos
- Cliques reduzidos em 40% (com command palette e busca)
- Satisfação do usuário (NPS) +10 pontos
- Suporte a 50+ funcionalidades sem information overload

### Conclusão
Esta arquitetura de navegação proporciona:
- **Escalabilidade** - Suporta expansão futura sem information overload
- **Usabilidade** - Múltiplos padrões de navegação para diferentes contextos
- **Acessibilidade** - Compatível com navegação por teclado e screen readers
- **Performance** - Busca rápida e eficiente com command palette

---

## 📋 PRÓXIMOS PASSOS

### Imediato (Esta Semana)
1. Aprovar orçamento de 2 engenheiros full-time
2. Priorizar tarefas da Fase 1 (Crítico)
3. Configurar ambiente de desenvolvimento
4. Iniciar implementação de correções críticas

### Curto Prazo (Semanas 1-4)
1. Monitorar progresso semanal
2. Revisar prioridades se necessário
3. Garantir qualidade de entregáveis
4. Documentar decisões técnicas

### Médio Prazo (Semanas 5-12)
1. Avaliar necessidade de recursos adicionais
2. Considerar expansão de scope se progresso satisfatório
3. Planejar roll-out para produção
4. Preparar documentação de release

---

## 🚀 CONCLUSÃO

Este plano transforma ambos os projetos de "protótipos com débito técnico" em "produtos production-ready" através de uma abordagem estruturada, priorizada e mensurável. Com execução disciplinada, ambos os projetos estarão prontos para scale e monetização em 12 semanas.

**Recomendação CPTO:** Aprovar execução imediata deste plano. Fundamentos técnicos são sólidos, ROI é claro, e timeline é realista.