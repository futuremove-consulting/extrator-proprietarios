# Plano de Preparação para Produção

**Versão:** 1.0
**Data:** 04/09/2026
**Status:** Proposto

---

## 1. Diagnóstico do Estado Atual

### 1.1 Inventário de Código

| Módulo | Arquivos | Linhas (est.) | Papel |
|--------|----------|---------------|-------|
|  | 3 | ~27k | Agente Captei |
|  | 3 | ~31k | Agente Fisgar |
|  | 3 | ~37k | Agente EEmovel |
|  | 13 | ~130k | Utilitários compartilhados |
| CLIs | 9 | ~80k | Interface de linha de comando |
| Testes | 3 | ~13k | Testes unitários |
| **Total** | **34** | **~318k** | |

### 1.2 Problemas Identificados

#### 🔴 Críticos

| Problema | Impacto | Local |
|----------|---------|------|
| Duplicação de código entre agentes | Manutenção, bugs | , ,  |
| Falta de feature flags | Não pode ativar/desativar funcionalidades | Todos os módulos |
| Configuração hardcoded | Difícil deploy em produção | , CLIs |
| Tratamento de erros inconsistente | Falhas silenciosas | Todos os módulos |
| Sem rate limiting | Pode ser bloqueado pelos fornecedores | , ,  |
| Sem retry com backoff | Falhas temporárias = perda de dados | Todos os agentes |
| Logging não estruturado | Difícil monitoramento |  |
| Sem timeout de requisição | Pode travar indefinidamente | Todos os agentes |
#### 🟡 Médios

| Problema | Impacto | Local |
|----------|---------|------|
| Type hints incompletos | Difícil refatoração | Todos os módulos |
| Validação de entrada fraca | Dados corrompidos | CLIs, agentes |
| Sem documentação inline | Difícil onboarding | Todos os módulos |
| Testes insuficientes | Regressões |  |
| Sem health check | Não sabe se está funcionando | Nenhum |
| Sem métricas | Não sabe performance | Nenhum |
#### 🟢 Melhorias

| Problema | Impacto | Local |
|----------|---------|------|
| Sem type aliases | Código verboso |  |
| Sem dataclasses | Estruturas frágeis |  |
| Sem constants file | Mágicos no código | Todos |
| Sem __version__ | Difícil versionamento | Raiz |
---

## 2. Arquitetura Proposta

### 2.1 Princípios

| Princípio | Descrição |
|-----------|-----------|
| **DRY** | Don't Repeat Yourself - eliminar duplicação |
| **Feature Flags** | Ativar/desativar funcionalidades sem deploy |
| **Fail Fast** | Falhar rápido com mensagens claras |
| **Graceful Degradation** | Continuar funcionando com menos recursos |
| **Observabilidade** | Logs, métricas, health checks |
| **Segurança por Padrão** | Credenciais nunca em código |
### 2.2 Nova Estrutura de Diretórios



---

## 3. Feature Flags

### 3.1 Implementação



### 3.2 Uso



---

## 4. Plano de Ação

### 4.1 Fase 1 — Fundação (Semana 1)

| Task | Descrição | Entrega |
|------|-----------|---------|
| T001 | Criar  | Feature flags funcionando |
| T002 | Criar  | Configuração centralizada |
| T003 | Criar  | Exceções customizadas |
| T004 | Criar  | Type aliases |
| T005 | Criar  | Constantes centralizadas |
| T006 | Criar  | Logging estruturado |
| T007 | Criar  | Cliente HTTP com retry |
### 4.2 Fase 2 — Refatoração (Semana 2)

| Task | Descrição | Entrega |
|------|-----------|---------|
| T008 | Criar  | Classe base dos agentes |
| T009 | Refatorar  | Agente usando base |
| T010 | Refatorar  | Agente usando base |
| T011 | Refatorar  | Agente usando base |
| T012 | Consolidar  | Eliminar duplicação |
### 4.3 Fase 3 — Produção (Semana 3)

| Task | Descrição | Entrega |
|------|-----------|---------|
| T013 | Adicionar rate limiting | Respeitar limites |
| T014 | Adicionar retry com backoff | Resiliência |
| T015 | Adicionar health check | Monitoramento |
| T016 | Adicionar métricas | Observabilidade |
| T017 | Criar  | Empacotamento |
| T018 | Criar  | Configuração |
| T019 | Criar  | Container |
### 4.4 Fase 4 — Testes (Semana 4)

| Task | Descrição | Entrega |
|------|-----------|---------|
| T020 | Testes unitários (80%+) | Cobertura |
| T021 | Testes de integração | Fluxo completo |
| T022 | Testes E2E | Produção-like |
| T023 | CI/CD pipeline | GitHub Actions |
---

## 5. Configuração de Produção

### 5.1 Variáveis de Ambiente



---

## 6. Checklist de Produção

- [ ] Feature flags implementadas
- [ ] Configuração via .env
- [ ] Logging estruturado (JSON)
- [ ] Rate limiting configurado
- [ ] Retry com backoff exponencial
- [ ] Timeout em todas as requisições
- [ ] Health check endpoint
- [ ] Métricas de execução
- [ ] Tratamento de erros consistente
- [ ] Type hints completos
- [ ] Testes unitários (80%+)
- [ ] Testes de integração
- [ ] Documentação inline
- [ ] Dockerfile
- [ ] CI/CD pipeline
- [ ] Feature flags documentadas
- [ ] Runbook de operação
---

## 7. Resumo

### Objetivo
Transformar o módulo extrator de um protótipo funcional em um produto pronto para produção,
com feature flags, observabilidade, resiliência e manutenibilidade.

### Princípios
1. **DRY**: Eliminar duplicação entre agentes
2. **Feature Flags**: Ativar/desativar sem deploy
3. **Fail Fast**: Mensagens de erro claras
4. **Graceful Degradation**: Continuar com menos recursos
5. **Observabilidade**: Logs, métricas, health checks
6. **Segurança**: Credenciais nunca em código

### Próximos Passos
1. Aprovar este plano
2. Iniciar Fase 1 (Fundação)
3. Implementar feature flags
4. Refatorar agentes para usar classe base
5. Adicionar testes
6. Preparar ambiente de produção
