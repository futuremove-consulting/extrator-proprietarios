# Teste de Validação WhatsApp — Dono do Zap

**Data**: 2026-09-04  
**Número testado**: 11999783379  
**Ferramenta**: agent-browser (Vercel MCP)

---

## Resultados

### donodozap.com.br ✅ FUNCIONA
| Aspecto | Resultado |
|---------|-----------|
| **Status** | Sucesso |
| **Tier detectado** | PAID (PIX unlock) |
| **Nome (FREE)** | `****G*** ***I*** ***H***` (parcialmente mascarado) |
| **Dados FREE** | Data de nascimento mascarada, CPF mascarado |
| **Dados PAID (após PIX)** | Nome completo, CPF, RG, endereços, emails, telefones, parentes, empresas, cidade, estado, operadora, redes sociais |
| **Custo estimado PAID** | ~R$ 0,50 via PIX |
| **Bloqueio anti-bot** | Não detectado |

### donodozap.com ❌ BLOQUEADO
| Aspecto | Resultado |
|---------|-----------|
| **Status** | Falha — bloqueio de conexão segura |
| **Mensagem** | "Não foi possível validar sua conexão segura. Se você usa um bloqueador de anúncios ou VPN, tente desativá-los temporariamente para esta página e tente novamente." |
| **Causa provável** | Detecção de headless/automated browser |
| **Tier** | N/A (não chegou a consultar) |

---

## Recomendação de Integração

```python
# Ordem de prioridade no WhatsAppValidationService
VALIDATORS = [
    DonoDoZapBRValidator(),   # Primário — funciona com agent-browser
    # DonoDoZapComValidator(),  # Fallback — só com browser real (não headless)
]

# Política sugerida
policy = ValidationPolicy(
    max_cost_per_phone=0.60,      # Cobre PIX do donodozap.com.br
    prefer_free_tier=False,       # Queremos dados completos
    require_photo_profile=False,  # Nome + CPF já valem
    skip_if_recent_hours=168,     # Cache 7 dias
    validators_order=["donodozap_br", "donodozap_com"]
)
```

---

## Integração no Pipeline (Estágio 2.5)

```bash
# Execução via orquestrador
python3 extrair_orquestrado.py \
  --endereco "Rua Marc Chagall, 397" \
  --sistemas eemovel fisgar captei \
  --log-dir logs_orquestrado
```

O Estágio 2.5 roda automaticamente após consolidação:
1. Carrega Golden Records
2. Extrai telefones únicos
3. Valida em lote via Dono do Zap
4. Atualiza Golden Records com `whatsapp_validation`
5. Recalcula score de confiança

---

## Arquivos Gerados

- `logs_orquestrado/process_log_orquestrado_*.ndjson` — Log estruturado NDJSON
- `logs_orquestrado/process_log_orquestrado_*.md` — Relatório de aprendizado
- `orquestrado_consolidado/consolidado/golden_records_*.json` — Golden Records com `whatsapp_validation`

---

## Próximos Passos

1. ✅ Testar validação em lote com múltiplos números
2. ✅ Integrar cache (SQLite/JSON) para evitar re-consultas
3. ⏳ Implementar fallback para donodozap.com com browser real (se necessário)
4. ⏳ Adicionar métricas de custo real vs estimado
5. ⏳ Testar com números reais dos manifests (não simulados)