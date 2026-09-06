---
name: process-learning-evaluator
description: Módulo de aprendizado contínuo: avalia se fluxo/ordem atual é ótimo (eficácia, eficiência, custo-benefício) e recomenda ajustes baseados em logs reais
metadata:
  type: architecture
---

## Process Learning Evaluator — Validação Contínua do Pipeline

### Objetivo
A cada execução, analisar logs NDJSON + métricas reais e responder:
> **O fluxo atual (EEmovel → Fisgar → Captei) é o melhor? Onde há desperdício? O que ajustar?**

### Inputs (do ProcessLearningLogger)
| Fonte | Métricas Chave |
|-------|----------------|
| `stage: inventory` | Sistemas com dados, chaves únicas, tempo listagem |
| `stage: extraction_cascade` | Processados/pulados por sistema, custo real vs estimado, erros |
| `stage: merge_enrichment` | Golden records, multi-origem %, requires_review, quality dist |
| `stage: whatsapp_validation` | Validados, custo total, tier atingido, cache hits |
| `cost_snapshots` | Gasto real por sistema por execução |

### Regras de Avaliação (Heurísticas)

| Sinal | Ação Recomendada |
|-------|------------------|
| **Sistema pulado > 50% das vezes** | Remover da ordem ou mover para fallback condicional |
| **Custo real > 2x estimado** | Recalibrar `custo_estimado` ou rever volume real |
| **Erros > 10% em sistema** | Investigar seletores/browser; considerar pular |
| **Multi-origem < 20%** | Chaves de identidade fracas; revisar record_key |
| **Requires_review > 80%** | Merge policies ou validação fraca; ajustar scoring |
| **Cache hit rate > 80% (WhatsApp)** | Aumentar `skip_if_recent_hours` |
| **Stage 1 inventário = 0 chaves** | Abortar cedo (já implementado) |
| **Tempo total > threshold** | Paralelizar Stage 1 (listagens independentes) |

### Output: Learning Report (Markdown)
```markdown
# Learning Report — YYYY-MM-DD HH:MM

## Execução Atual
- Endereço: ...
- Ordem usada: EEmovel → Fisgar → Captei
- Custo total: R$ X,XX
- Tempo total: Ys

## Análise por Sistema
| Sistema | Listagem | Extração | Custo Real | Pulados | Erros | Eficiência |
|---------|----------|----------|------------|---------|-------|------------|
| EEmovel | ✓ | 23 | R$ 18,63 | 0 | 0 | ★★★★★ |
| Fisgar  | ✓ | 3  | R$ 3,09  | 20 | 0 | ★★★☆☆ |
| Captei  | ✓ | 2  | R$ 3,14  | 18 | 0 | ★★☆☆☆ |

## Recomendações
1. **Fisgar**: 87% pulados → mover para fallback condicional (só se EEmovel < 80% cobertura)
2. **Captei**: 90% pulados + mais caro → remover da cascata padrão; só sob demanda
3. **WhatsApp**: Cache hit 0% → ativar cache 7 dias na próxima execução
4. **Ordem otimizada**: EEmovel → (condicional Fisgar) → (sob demanda Captei)

## Próxima Execução Sugerida
```python
ORDEM_DINAMICA = [
    {"sistema": "eemovel", "sempre": True},
    {"sistema": "fisgar", "condicao": "cobertura_eemovel < 0.8"},
    {"sistema": "captei", "condicao": "whatsapp_validation_needed and not captei_done"},
]
```
```

### Integração no Orquestrador
```python
# extrair_orquestrado.py — após logger.finalize()
from comum.learning_evaluator import evaluate_and_recommend

recommendations = evaluate_and_recommend(logger.log_path)
logger.log_decision(
    stage="learning",
    decision="evaluate_pipeline",
    rationale=recommendations["summary"],
    data=recommendations
)

# Salvar recomendação para próxima execução
with open(".opencode/memory/last_recommendation.json", "w") as f:
    json.dump(recommendations, f, ensure_ascii=False, indent=2)
```

### Arquivo de Estado: `.opencode/memory/last_recommendation.json`
```json
{
  "timestamp": "2026-09-04T...",
  "ordem_atual": ["eemovel", "fisgar", "captei"],
  "ordem_sugerida": ["eemovel"],
  "fallback_condicional": {"fisgar": "cobertura_eemovel < 0.8"},
  "sob_demanda": {"captei": "whatsapp_gap"},
  "ajustes_custo": {"fisgar": 1.03, "captei": 1.57},
  "cache_whatsapp_horas": 168
}
```

### Princípio: "O fluxo se auto-otimiza"
- Não hardcodear ordem fixa
- Usar recomendação da execução anterior como default da próxima
- Permitir override manual via CLI `--ordem`
- Logar decisão: "usou recomendação automática" vs "override manual"