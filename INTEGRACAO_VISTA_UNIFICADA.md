# Integração VISTA — Modelo de Dados Universal

**Versão:** 1.0
**Data:** 04/09/2026
**Status:** Implementação

---

## 1. Visão Geral

Este documento define o **modelo de dados universal** para integração com o CRM VISTA (Loft CRM),
incluindo camada de tradução, mapeamento de campos e estratégia de integração.

### 1.1 Fontes Analisadas

| Fonte | URL | Documentação |
|-------|-----|-------------|
| API Oficial | https://vs-public-api-documentation.loft.com.br/ | Swagger UI |
| Documentação | https://www.vistasoft.com.br/api/ | Guia de Integração |
| Spec OpenAPI | https://novovista-rest.vistahost.com.br/doc/ | 117 endpoints |
| Sandbox | https://sandbox-rest.vistahost.com.br/ | Testes |

### 1.2 Domínios da API

| Domínio | Endpoint Base | Descrição |
|---------|---------------|-----------|
| Imóveis |  | Acervo de imóveis |
| Clientes |  | Base de clientes/leads |
| Leads |  | Captção de leads |
| Proprietários |  | Donos de imóveis |
| Negócios |  | Pipeline de vendas |
| Agenda |  | Visitas e agendamentos |
| Corretores |  | Equipe de vendas |
| Agências |  | Filiais |

---

## 2. Autenticação e Padrões da API

### 2.1 Autenticação



- **Nunca** enviar credenciais no body
- **Server-side apenas** (nunca no cliente/frontend)
- Chave de teste: 

### 2.2 Padrão de Requisição (pesquisa)



### 2.3 Padrão de Resposta



---

## 3. Modelo de Dados VISTA → Modelo Canônico

### 3.1 Mapeamento: Imóveis

| Campo VISTA | Campo Canônico | Tipo | Observação |
|-------------|---------------|------|------------|
|  |  | string | ID externo |
|  |  | string | Apartamento, Casa... |
|  |  | string | sale/rent/seasonal |
|  |  | string | |
|  |  | string | |
|  |  | string | |
|  |  | string | |
|  +  |  | string | |
|  |  | number | |
|  |  | number | |
|  |  | number | |
|  |  | number | |
|  |  | integer | |
|  |  | integer | |
|  |  | integer | |
|  |  | number | |
|  |  | number | |
|  |  | string | Novo/Usado... |
|  |  | array | Lista de amenities |
|  |  | string | URL da foto |

### 3.2 Mapeamento: Clientes (Leads)

| Campo VISTA | Campo Canônico | Tipo | Observação |
|-------------|---------------|------|------------|
|  |  | string | ID externo |
|  |  | string | |
|  |  | string | Telefone principal |
|  |  | string | |
|  |  | string | |
|  |  | string | |
|  |  | string | Origem do lead |

### 3.3 Mapeamento: Proprietários

| Campo VISTA | Campo Canônico | Tipo | Observação |
|-------------|---------------|------|------------|
|  |  | string | ID externo |
|  |  | string | |
|  |  | string | |
|  |  | string | |
|  |  | string | |

### 3.4 Mapeamento: Negócios (Deals)

| Campo VISTA | Campo Canônico | Tipo | Observação |
|-------------|---------------|------|------------|
|  |  | string | ID externo |
|  |  | number | Valor do negócio |
|  |  | string | status do deal |

---

## 4. Camada de Tradução (Anti-Corruption Layer)

### 4.1 Arquitetura Hub-and-Spoke



---

## 5. Estratégia de Integração

### 5.1 Direções de Fluxo

| Direção | Descrição | Endpoints |
|---------|-----------|-----------|
| VISTA → Extrator | Importar imóveis/proprietários | ,  |
| Extrator → VISTA | Exportar leads qualificados |  |
| PilotCRM → VISTA | Sincronizar contatos |  |

### 5.2 Sequência de Implementação

1. **Adapter VISTA**: criar  com  e 
2. **Importação**: buscar imóveis/proprietários do VISTA e converter para modelo canônico
3. **Exportação**: enviar leads qualificados do extrator para o VISTA
4. **Sincronização**: manter PilotCRM e VISTA sincronizados via camada de tradução

---

## 6. Endpoints Prioritários para Integração

### 6.1 Leitura (Importação)

| Prioridade | Endpoint | Descrição |
|------------|----------|-----------|
| **P0** |  | Listar imóveis |
| **P0** |  | Detalhes do imóvel |
| **P0** |  | Listar proprietários |
| **P1** |  | Listar clientes |
| **P1** |  | Detalhes do cliente |
| **P2** |  | Listar negócios |

### 6.2 Escrita (Exportação)

| Prioridade | Endpoint | Descrição |
|------------|----------|-----------|
| **P0** |  | Criar lead |
| **P1** |  | Criar cliente |
| **P2** |  | Atualizar cliente |

---

## 7. Modelo de Dados Universal (Canonical Model)

### 7.1 Contato (Proprietário/Lead)



---

## 8. Configuração e Secrets

### 8.1 Variáveis de Ambiente



### 8.2 Segurança

- **Nunca** expor  no frontend
- **Sempre** usar em server-side (API routes ou backend)
- Rotacionar chaves periodicamente

---

## 9. Referências

| Documento | Link |
|-----------|------|
| API Oficial | https://vs-public-api-documentation.loft.com.br/ |
| Guia Integração | https://www.vistasoft.com.br/api/ |
| Spec OpenAPI | https://novovista-rest.vistahost.com.br/doc/ |
| Sandbox | https://sandbox-rest.vistahost.com.br/ |

---

## 10. Próximos Passos

1. **Criar ** com mapeamento completo
2. **Criar ** com autenticação e paginação
3. **Testar importação** de imóveis do sandbox
4. **Testar exportação** de leads para o sandbox
5. **Integrar ao consolidador** multi-origem
