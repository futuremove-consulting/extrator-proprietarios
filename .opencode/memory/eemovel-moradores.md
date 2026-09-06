---
name: eemovel-moradores
description: EEmovel retorna "Possível morador" + "Proprietário" na mesma listagem; classificar por tipo_pessoa e salvar em listas distintas; não dedupar morador com proprietário
metadata:
  type: business-rule
---

## EEmovel — Moradores vs Proprietários

### Diferença Crítica
EEmovel retorna **ambos** na mesma listagem:
- `tipo_pessoa: "Proprietário"` — dono da unidade
- `tipo_pessoa: "Possível morador"` — residente (pode ser inquilino, familiar, etc.)

### Classificação no Stage 1
```python
# extrair_orquestrado.py — normalizar_linha_tabela()
if reg["tipo_pessoa"] in ["Possível morador", "Morador"]:
    moradores.append(reg)
else:
    proprietarios.append(reg)
```

### Listas Fisicamente Separadas
| Lista | Conteúdo | Uso |
|-------|----------|-----|
| `proprietarios` | Apenas `tipo_pessoa == "Proprietário"` | Captação, negociação, contato comercial |
| `moradores` | Apenas `tipo_pessoa in ["Possível morador", "Morador"]` | Relacionamento, visita, referência |

### Regra de Ouro: NUNCA Dedupar Cruzado
- Morador "João Silva AP 101" ≠ Proprietário "João Silva AP 101"
- Mesmo nome + mesma unidade = pessoas diferentes
- `record_key` inclui `tipo_pessoa` implicitamente via listas separadas
- Merge policies NÃO cruzam as listas

### Dados de Morador (EEmovel)
- Nome + unidade
- Telefones + emails (quando disponíveis)
- **SEM CPF** (só proprietários têm)
- Tipo: "Possível morador" (não confirmado)

### Outros Sistemas
- **Captei**: Pode ter moradores (verificar `papel` no modal)
- **Fisgar**: Pode ter moradores (verificar `papel` no modal)
- Mesmo tratamento: classificar no Stage 1, listas separadas