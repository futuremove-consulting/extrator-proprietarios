---
name: whatsapp-validation-stage
description: Stage 2.5 no pipeline: após consolidação, valida telefones únicos via donodozap.com.br; policy: max R$0,60/telefone, cache 7 dias, prefere PAID
metadata:
  type: architecture
---

## Stage 2.5 — Validação WhatsApp (Dono do Zap)

### Quando Executa
Após Stage 3 (Merge & Enriquecimento), automaticamente no orquestrador

### Fluxo
1. Carrega Golden Records consolidados
2. Extrai telefones únicos (dedup por dígitos)
3. Filtra: só valida se não validado recentemente (cache 7 dias)
4. Chama `WhatsAppValidationService.validate_batch(phones)`
4. Atualiza Golden Records com campo `whatsapp_validation`
5. Recalcula score de confiança

### WhatsAppValidationService
```python
service = create_validation_service(
    max_cost_per_phone=0.60,
    prefer_free_tier=False,
    require_photo_profile=False,
    skip_if_recent_hours=168
)
result = await service.validate_batch(phones)
```

### ValidationPolicy
| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| `max_cost_per_phone` | 0.60 | Cobre PIX ~R$ 0,50 + margem |
| `prefer_free_tier` | False | Queremos CPF/nome completo |
| `require_photo_profile` | False | Nome + CPF já validam |
| `skip_if_recent_hours` | 168 | Cache 7 dias evita re-gasto |
| `validators_order` | ["donodozap_br"] | Só o que funciona |

### WhatsAppValidationResult (salvo no Golden Record)
```json
{
  "phone_digits": "11999999999",
  "phone_formatted": "(11) 99999-9999",
  "source": "donodozap_br",
  "tier": "paid",
  "nome_exibicao": "JOAO SILVA",
  "foto_perfil_url": "https://...",
  "status_whatsapp": "ativo",
  "cpf": "123.456.789-00",
  "custo_estimado": 0.50,
  "validado_em": "2026-09-04T...",
  "raw_response": {...}
}
```

### Integração no Orquestrador
```python
# extrair_orquestrado.py — após stage3_merge_enriquecimento
whatsapp_result = asyncio.run(stage25_validacao_whatsapp(
    logger,
    resultado_merge["golden_records_path"],
    max_cost_per_phone=1.00
))
```

### Logs de Aprendizado
ProcessLearningLogger registra:
- `extraction_result` com stats do serviço
- `cost_snapshot` por validação
- Decisões: pular cache, tier atingido, erros