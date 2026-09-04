# Plano de Arquitetura Modular — Extração + PilotCRM

**Versão:** 1.0  
**Data:** 04/09/2026  
**Status:** Proposto

---

## 1. Premissas (dos 5 pontos)

1. **Nem sempre o sistema apresenta unidade** → foco em WhatsApp e e-mail válidos; unidade quando disponível é atributo extra.
2. **Validação Dono do Zap** →  (sim/não) e  (sim/não) são atributos que aumentam score/confiança.
3. **Nome público** → só mais uma validação para consistência/confiabilidade do número; não é prova definitiva.
4. **Arquitetura** → módulo de extração funciona COMO serviço autônomo E COMO módulo do PilotCRM (desacoplado, orientado a serviço).
5. **LGPD** → desconsiderada por enquanto.
6. **Custos** → planejar com cálculo mínimo, médio e máximo.

---

## 2. Arquitetura Proposta



### 2.1 Princípios Arquiteturais

| Princípio | Descrição |
|-----------|-----------|
| **Desacoplamento** | Serviço de extração roda independente (CLI/API) e se integra ao PilotCRM via API REST |
| **Reuso** | Mesmo serviço atende: (a) uso autônomo via CLI, (b) módulo dentro do PilotCRM, (c) API para terceiros |
| **Idempotência** | Mesmo endereço processado 2x não gera duplicata nem gasta crédito 2x |
| **Observabilidade** | Toda operação tem log estruturado (process_logger) com rastreabilidade |
| **Fail-fast** | Se uma fonte falha, continua com as outras; erro não paralisa o fluxo |

---

## 3. Modelo de Dados — Atributos de Validação

### 3.1 Tabela  (existente) — uso

| Campo | Uso no fluxo |
|-------|--------------|
|  | Nome do proprietário (extraído das fontes) |
|  | E-mail válido (extraído + validado) |
|  | Telefone/WhatsApp (extraído + validado) |
|  | CPF quando disponível (chave forte) |
|  | Origem: , , ,  |
|  | JSONB com atributos de verificação (ver abaixo) |

### 3.2  — Atributos de Validação



### 3.3 Score de Confiança

O score é calculado pelos atributos de validação:

| Atributo | Peso | Motivação |
|----------|------|-----------|
|  = true | +30 | Nome público bate com proprietário |
|  = true | +30 | Validação secundária independente |
|  = true | +40 | Validação oficial via WhatsApp |
|  = true | +10 | E-mail confirmado como válido |
|  = true | +20 | CPF disponível (chave forte) |
|  (2+ fontes) | +15 | Mesmo dado em múltiplas fontes |

**Faixas de confiança:**
- **Alta (≥80):** WhatsApp validado por 2+ camadas ou Captei
- **Média (50-79):** Validação por nome público + e-mail
- **Baixa (<50):** Apenas dados brutos sem validação

---

## 4. Cálculo de Custos — Mínimo, Médio, Máximo

### 4.1 Premissas de Cálculo

| Recurso | Custo unitário | Observação |
|---------|---------------|------------|
| Captei (capcoin) | R$ 0,998 | Pacote 50 por R$ 49,90 |
| Fisgar (consulta) | R$ 1,03 | 250/mês por R$ 257,50 (estimado) |
| EEmovel (consulta) | R$ 0,81 | 500/mês por R$ 403,90 (plano Pro) |
| Dono do Zap (.com) | R$ 0,00 | Pesquisa inicial grátis |
| Dono do Zap (.com.br) | R$ 4,90 | Se usar relatório completo (opcional) |

### 4.2 Cenários para Lote de 320 Proprietários (Marc Chagall)

#### CENÁRIO MÍNIMO (melhor caso)

Todas as fontes colaboram, máxima sobreposição, validação gratuita funciona:

| Etapa | Quantidade | Custo unit. | Total |
|-------|-----------|-------------|-------|
| Listagem (3 sistemas) | 3 | 1 capcoin | 3 capcoins |
| EEmovel (fichas) | 200 | R$ 0,81 | R$ 162,00 |
| Fisgar (complemento) | 50 | R$ 1,03 | R$ 51,50 |
| Captei (lacunas) | 20 | R$ 0,998 | R$ 19,96 |
| Dono do Zap (todos) | 320 | R$ 0,00 | R$ 0,00 |
| **TOTAL** | | | **R$ 233,46 + 23 capcoins** |

#### CENÁRIO MÉDIO (realista)

Sobreposição parcial, algumas validações falham, complemento necessário:

| Etapa | Quantidade | Custo unit. | Total |
|-------|-----------|-------------|-------|
| Listagem (3 sistemas) | 3 | 1 capcoin | 3 capcoins |
| EEmovel (fichas) | 320 | R$ 0,81 | R$ 259,20 |
| Fisgar (complemento) | 80 | R$ 1,03 | R$ 82,40 |
| Captei (lacunas + validações) | 40 | R$ 0,998 | R$ 39,92 |
| Dono do Zap (todos) | 320 | R$ 0,00 | R$ 0,00 |
| **TOTAL** | | | **R$ 381,52 + 43 capcoins** |

#### CENÁRIO MÁXIMO (pior caso)

Quase nenhuma sobreposição, validações falham, precisa de tudo:

| Etapa | Quantidade | Custo unit. | Total |
|-------|-----------|-------------|-------|
| Listagem (3 sistemas) | 3 | 1 capcoin | 3 capcoins |
| EEmovel (fichas) | 320 | R$ 0,81 | R$ 259,20 |
| Fisgar (fichas) | 200 | R$ 1,03 | R$ 206,00 |
| Captei (lacunas + validações) | 60 | R$ 0,998 | R$ 59,88 |
| Dono do Zap (relatório completo) | 50 | R$ 4,90 | R$ 245,00 |
| **TOTAL** | | | **R$ 770,08 + 63 capcoins** |

---

## 5. Integração com PilotCRM

### 5.1 Opção de Integração

| Opção | Descrição | Complexidade |
|--------|-----------|--------------|
| **A. API REST** | Serviço de extração expõe endpoints; PilotCRM chama via fetch | Média |
| **B. Webhook** | PilotCRM dispara webhook; serviço processa e retorna | Média |
| **C. Pacote compartilhado** | Módulo Python importado diretamente no PilotCRM (monorepo) | Baixa |
| **D. CLI + agendamento** | PilotCRM chama CLI via subprocess/cron | Baixa |

**Recomendação:** Opção C (pacote compartilhado) para fase inicial + Opção A (API) para desacoplamento futuro.

### 5.2 Endpoints da API do Serviço de Extração



---

## 6. Fluxo Operacional Completo

### 6.1 Modo Autônomo (CLI)



### 6.2 Modo PilotCRM (módulo)



### 6.3 Modo API (terceiros)



---

## 7. Roadmap de Implementação

| Fase | Entrega | Prazo sugerido |
|------|---------|----------------|
| **F1** | Serviço autônomo CLI funcionando (3 agentes + consolidador) | 1 semana |
| **F2** | Módulo de validação Dono do Zap integrado | 1 semana |
| **F3** | API REST do serviço de extração | 1 semana |
| **F4** | Integração PilotCRM (pacote compartilhado) | 2 semanas |
| **F5** | Testes reais completos (Dia 1-4 do plano) | 1 semana |
| **F6** | Modo "consulta direta" (lead urgente) | 1 semana |

---

## 8. Decisões Pendentes

1. **Estrutura do monorepo:** serviço de extração como submódulo do PilotCRM ou repo separado com pacote compartilhado?
2. **Banco de dados:** serviço de extração usa mesmo Supabase do PilotCRM ou banco separado?
3. **Autenticação:** como o PilotCRM autentica nas chamadas à API do serviço de extração?
4. **Priorização:** implementar modo "consulta direta" antes da integração completa?

