"""Excecoes customizadas do modulo extrator."""

from typing import Any


class ExtratorError(Exception):
    """Excecao base do modulo."""
    
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}


class AgentError(ExtratorError):
    """Erro em agente de extracao."""
    
    def __init__(self, agent: str, message: str, details: dict | None = None):
        super().__init__(f"[{agent}] {message}", details)
        self.agent = agent


class ValidationError(ExtratorError):
    """Erro de validacao de dados."""
    
    def __init__(self, field: str, message: str, value: Any = None):
        super().__init__(f"Validacao de '{field}': {message}")
        self.field = field
        self.value = value


class RateLimitError(ExtratorError):
    """Erro de rate limiting."""
    
    def __init__(self, source: str, retry_after: float | None = None):
        msg = f"Rate limit atingido para {source}"
        if retry_after:
            msg += f". Tente novamente em {retry_after:g}s"
        super().__init__(msg)
        self.source = source
        self.retry_after = retry_after


class AuthenticationError(ExtratorError):
    """Erro de autenticacao."""
    
    def __init__(self, source: str, message: str = "Falha na autenticacao"):
        super().__init__(f"[{source}] {message}")
        self.source = source


class TimeoutError(ExtratorError):
    """Erro de timeout."""
    
    def __init__(self, source: str, timeout: float):
        super().__init__(f"Timeout ({timeout:g}s) para {source}")
        self.source = source
        self.timeout = timeout


class CircuitBreakerOpenError(ExtratorError):
    """Circuit breaker aberto."""
    
    def __init__(self, source: str, failures: int):
        super().__init__(f"Circuit breaker aberto para {source} ({failures} falhas)")
        self.source = source
        self.failures = failures
