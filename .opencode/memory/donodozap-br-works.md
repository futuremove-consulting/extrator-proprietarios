---
name: donodozap-br-works
description: donodozap.com.br funciona com agent-browser: FREE retorna nome mascarado + nascimento/CPF parciais; PAID (PIX ~R$0,50) desbloqueia dados completos
metadata:
  type: reference
---

## donodozap.com.br — Validador Funcional

### Testado com agent-browser (Vercel MCP)
- **Número**: 11999783379
- **Status**: ✅ Funciona
- **Anti-bot**: Não detectado

### Tier FREE (Sem custo)
- Nome parcialmente mascarado: `****G*** ***I*** ***H***`
- Data de nascimento mascarada
- CPF mascarado
- **Uso**: Confirma que número existe no WhatsApp + dá pista do nome

### Tier PAID (PIX ~R$ 0,50)
Desbloqueia dados completos:
- Nome completo
- CPF completo
- RG
- Endereços (atual + histórico)
- Emails
- Telefones (todos)
- Parentes/associados
- Empresas vinculadas
- Cidade/Estado
- Operadora
- Redes sociais

### Integração no Pipeline
```python
# WhatsAppValidationService policy
policy = ValidationPolicy(
    max_cost_per_phone=0.60,      # Cobre PIX
    prefer_free_tier=False,       # Queremos dados completos
    require_photo_profile=False,  # Nome + CPF já valem
    skip_if_recent_hours=168,     # Cache 7 dias
    validators_order=["donodozap_br"]
)
```

### Seletores agent-browser (do validator)
- Input: `input[type="tel"], input[placeholder*="WhatsApp"], input[placeholder*="número"]`
- Botão: `button:has-text("Consultar"), button:has-text("Descobrir")`
- Nome FREE: `.resultado-nome, [data-testid="nome"], h2:has-text("Nome"), .nome-exibicao`
- Foto PAID: `img[alt*="foto"], img[alt*="perfil"], .foto-perfil img`