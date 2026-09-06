"""Testes para rate_limiter.py."""

import time

import pytest

from extrator_prop.core.rate_limiter import (
    RateLimitConfig,
    RateLimiterManager,
    TokenBucketRateLimiter,
)


class TestRateLimitConfig:
    """Testes para RateLimitConfig."""
    
    def test_default_values(self):
        config = RateLimitConfig(requests_per_minute=60)
        assert config.requests_per_minute == 60
        assert config.burst_size == 10
    
    def test_custom_burst(self):
        config = RateLimitConfig(requests_per_minute=100, burst_size=20)
        assert config.burst_size == 20


class TestTokenBucketRateLimiter:
    """Testes para TokenBucketRateLimiter."""
    
    def test_initial_tokens(self):
        config = RateLimitConfig(requests_per_minute=60, burst_size=5)
        limiter = TokenBucketRateLimiter(config)
        
        assert limiter.tokens == 5
        assert limiter.available_tokens == 5
    
    def test_acquire_success(self):
        config = RateLimitConfig(requests_per_minute=60, burst_size=5)
        limiter = TokenBucketRateLimiter(config)
        
        assert limiter.acquire() is True
        assert limiter.available_tokens == pytest.approx(4, abs=1e-3)
    
    def test_acquire_exhaustion(self):
        config = RateLimitConfig(requests_per_minute=60, burst_size=2)
        limiter = TokenBucketRateLimiter(config)
        
        assert limiter.acquire() is True
        assert limiter.acquire() is True
        # Sem tokens, deve retornar False rapidamente
        assert limiter.acquire(timeout=0.1) is False
    
    def test_refill(self):
        config = RateLimitConfig(requests_per_minute=600, burst_size=1)  # 10 tokens/sec
        limiter = TokenBucketRateLimiter(config)
        
        limiter.acquire()  # Gasta 1 token
        assert limiter.available_tokens < 1
        
        time.sleep(0.2)  # Espera refill
        assert limiter.available_tokens > 0


class TestRateLimiterManager:
    """Testes para RateLimiterManager."""
    
    def test_register_and_acquire(self):
        manager = RateLimiterManager()
        config = RateLimitConfig(requests_per_minute=60, burst_size=5)
        
        manager.register("test_source", config)
        assert manager.acquire("test_source") is True
    
    def test_unregistered_source(self):
        manager = RateLimiterManager()
        # Fonte nao registrada nao tem limitacao
        assert manager.acquire("unknown") is True
    
    def test_get_status(self):
        manager = RateLimiterManager()
        config = RateLimitConfig(requests_per_minute=60, burst_size=5)
        manager.register("test", config)
        
        status = manager.get_status("test")
        assert status is not None
        assert status["source"] == "test"
        assert status["requests_per_minute"] == 60
