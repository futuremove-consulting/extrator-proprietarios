---
name: donodozap-com-blocked
description: donodozap.com bloqueia headless browser ("Não foi possível validar sua conexão segura"); não usar como fallback automatizado
metadata:
  type: reference
---

## donodozap.com — Bloqueado

### Testado com agent-browser (Vercel MCP)
- **Número**: 11999783379
- **Status**: ❌ Falha — bloqueio de conexão segura

### Mensagem de Erro
> "Não foi possível validar sua conexão segura. Se você usa um bloqueador de anúncios ou VPN, tente desativá-los temporariamente para esta página e tente novamente."

### Causa Provável
Detecção de headless/automated browser (fingerprinting, TLS, behavioral analysis)

### Recomendação
**NÃO usar como fallback automatizado**. Apenas:
- Browser real (headed, perfil de usuário real)
- Ou não usar

### Validator Implementado (para referência)
`donodozap_com_validator.py` existe mas não deve ser ativado no `WhatsAppValidationService` a menos que tenha browser real disponível.

### Order no Serviço
```python
VALIDATORS = [
    DonoDoZapBRValidator(),   # Primário — funciona
    # DonoDoZapComValidator(),  # Comentado — só com browser real
]
```