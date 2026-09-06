"""Rate limiting com token bucket algoritm."""

import time
import threading
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger("extrator_prop.rate_limiter")


@dataclass
class RateLimitConfig:
    """Configuracao de rate limit."""
    requests_per_minute: int = 60
    burst_size: Optional[int] = None  # Maximo de requests em burst
    
    def __post_init__(self):
        if self.burst_size is None:
            self.burst_size = min(self.requests_per_minute, 10)


class TokenBucketRateLimiter:
    """Rate limiter com algoritmo token bucket."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_size
        self.max_tokens = config.burst_size
        self.refill_rate = config.requests_per_minute / 60.0  # tokens por segundo
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()
    
    def _refill(self):
        """Recarrega tokens baseado no tempo passado."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.max_tokens, self.tokens + new_tokens)
        self.last_refill = now
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Adquire um token. Retorna True se conseguiu."""
        deadline = time.monotonic() + timeout if timeout else None
        
        while True:
            with self._lock:
                self._refill()
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
            
            # Se nao tem token, espera um pouco
            if deadline and time.monotonic() >= deadline:
                return False
            
            # Calcula tempo de espera ateh proximo token
            wait_time = (1 - self.tokens) / self.refill_rate
            if deadline:
                wait_time = min(wait_time, deadline - time.monotonic())
            
            time.sleep(max(0.01, wait_time))
    
    @property
    def available_tokens(self) -> float:
        """Tokens disponiveis."""
        with self._lock:
            self._refill()
            return self.tokens


class RateLimiterManager:
    """Gerenciador de rate limiters por fonte."""
    
    def __init__(self):
        self._limiters: Dict[str, TokenBucketRateLimiter] = {}
    
    def register(self, source: str, config: RateLimitConfig):
        """Registra um rate limiter para uma fonte."""
        self._limiters[source] = TokenBucketRateLimiter(config)
        logger.info(f"Rate limiter registrado: {source} ({config.requests_per_minute}/min)")
    
    def acquire(self, source: str, timeout: Optional[float] = None) -> bool:
        """Adquire token para uma fonte."""
        if source not in self._limiters:
            return True  # Sem limitacao
        return self._limiters[source].acquire(timeout)
    
    def get_status(self, source: str) -> Optional[Dict]:
        """Obtem status do rate limiter."""
        if source not in self._limiters:
            return None
        limiter = self._limiters[source]
        return {
            "source": source,
            "available_tokens": limiter.available_tokens,
            "max_tokens": limiter.max_tokens,
            "requests_per_minute": limiter.config.requests_per_minute
        }
    
    def get_all_status(self) -> Dict[str, Dict]:
        """Obtem status de todos os limiters."""
        return {source: self.get_status(source) for source in self._limiters}


# Instancia global
rate_limiter_manager = RateLimiterManager()
