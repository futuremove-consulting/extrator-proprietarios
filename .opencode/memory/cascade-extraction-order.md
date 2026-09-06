---
name: cascade-extraction-order
description: EEmovel → Fisgar → Captei order by cost; Stage 1 costs 1 crédito/listagem
metadata:
  type: architecture
---

## Cascade Extraction Order (Optimized)

### Cost per Consulta (Corrected)
| Sistema | Plano | Custo/ano | Limite/mês | Custo/consulta |
|---------|-------|-----------|------------|----------------|
| **EEmovel** | Pro | R$ 4.846 | 500 | **R$ 0,81** |
| **Fisgar** | Plus | R$ 3.084 | 250 | **R$ 1,03** |
| **Captei** | Light | R$ 3.772 + capcoins | ~200 | **R$ 1,57+** |

### Stage 1: Inventário
- **Custo**: 1 crédito por listagem por sistema
- **Ação**: Buscar endereço, retornar lista completa (proprietários + moradores)
- **Salva**: manifest local — retomada NÃO repaga a listagem
- **Decisão**: se total únicos = 0 → ABORTAR (economiza tudo)

### Stage 2: Extração em Cascata
**Ordem**: EEmovel → Fisgar → Captei (menor custo/maior riqueza primeiro)

Lógica: extrair do sistema com MAIOR cobertura primeiro
1. **EEmovel** (R$ 0,81) — Dados ricos: CPF, múltiplos endereços, telefones, emails, dados imóvel — SEM MODAL
2. **Fisgar** (R$ 1,03) — APENAS gaps residuais; valor: CPF/RG oficiais
3. **Captei** (R$ 1,57+) — APENAS restantes; valor: validação WhatsApp (diferencial único)

### Stage 3: Merge & Enriquecimento
Pipeline 8 stages → Golden Records

### Stage 2.5: Validação WhatsApp (Opcional)
Após consolidação, valida telefones únicos via donodozap.com.br
- Policy: max R$ 0,60/telefone, cache 7 dias, prefere PAID