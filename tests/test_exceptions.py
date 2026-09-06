"""Testes para exceptions.py."""

from extrator_prop.exceptions import (
    ExtratorError,
    AgentError,
    ValidationError,
    RateLimitError,
    AuthenticationError,
    TimeoutError,
    CircuitBreakerOpenError
)


class TestExceptions:
    """Testes para excecoes customizadas."""
    
    def test_extrator_error(self):
        err = ExtratorError("Test error", {"key": "value"})
        assert str(err) == "Test error"
        assert err.details == {"key": "value"}
    
    def test_agent_error(self):
        err = AgentError("captei", "Connection failed")
        assert "[captei]" in str(err)
        assert "Connection failed" in str(err)
        assert err.agent == "captei"
    
    def test_validation_error(self):
        err = ValidationError("name", "Required field", None)
        assert "name" in str(err)
        assert err.field == "name"
        assert err.value is None
    
    def test_rate_limit_error(self):
        err = RateLimitError("captei", retry_after=30.0)
        assert "captei" in str(err)
        assert "30s" in str(err)
        assert err.retry_after == 30.0
    
    def test_authentication_error(self):
        err = AuthenticationError("fisgar")
        assert "[fisgar]" in str(err)
        assert err.source == "fisgar"
    
    def test_timeout_error(self):
        err = TimeoutError("eemovel", 30.0)
        assert "eemovel" in str(err)
        assert "30s" in str(err)
    
    def test_circuit_breaker_error(self):
        err = CircuitBreakerOpenError("captei", 5)
        assert "captei" in str(err)
        assert "5" in str(err)
