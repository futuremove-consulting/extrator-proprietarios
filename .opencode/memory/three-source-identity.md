---
name: three-source-identity
description: Identity resolution cascata: 1) CPF (forte), 2) nome|unidade, 3) +email, 4) +telefone; intra-source dedup ANTES do cross-source merge; moradores ≠ proprietários
metadata:
  type: architecture
---

## Identity Resolution — 3 Fontes (Captei, Fisgar, EEmovel)

### Chaves em Cascata (Prioridade)

| Prioridade | Chave | Força | Quando Usar |
|------------|-------|-------|-------------|
| **1** | **CPF** | Forte | Disponível em ≥2 origens (EEmovel + Fisgar) |
| **2** | **nome\|unidade** | Forte | record_key exato (SHA256 20 chars) |
| **3** | **nome\|unidade\|email** | Média | Email disponível em ambas |
| **4** | **nome\|unidade\|telefone** | Média | Telefone disponível em ambas |
| **5** | **Fuzzy** (nome + endereço) | Baixa | Variações de digitação/abreviação |

### Pipeline de Deduplicação (Ordem Crítica)

```
1. INTRA-SOURCE DEDUP (cada origem separadamente)
   → Captei: 12 → 4 registros (benchmark mostrou repetição na listagem)
   → Fisgar: 12 → 4 registros
   → EEmovel: 23 → 23 (já únicos)

2. CROSS-SOURCE MERGE
   → Agrupa por chaves cascata
   → Grupos multi-origem: merge policies por campo
   → Singles: mantêm origem única

3. MORADORES ≠ PROPRIETÁRIOS
   → Listas FISICAMENTE SEPARADAS desde Stage 1
   → NUNCA dedupar morador com proprietário
   → tipo_pessoa: "Proprietário" vs "Possível morador"
```

### Merge Policies por Campo
| Campo | Política |
|-------|----------|
| `nome_completo` | Mais completo (maior length) |
| `cpf` | Qualquer não-vazio (validar formato) |
| `telefones` | União dedup por dígitos; WhatsApp validado vence |
| `emails` | União dedup por lowercase; válido vence |
| `enderecos` | União; principal = do EEmovel (mais rico) |
| `whatsapp_status` | PAID > FREE > not_found > failed |
| `quality` | Recalculado pós-merge |

### Benchmark (Dados Reais)
- Overlaps por record_key exato: 4 grupos (Captei↔Fisgar)
- Overlaps por CPF: 0 (dados simulados sem CPF)
- Overlaps por telefone: 1 (telefone simulado igual)
- Fuzzy matches (>0.85 nome): 42 (muitos falsos positivos intra-origem)