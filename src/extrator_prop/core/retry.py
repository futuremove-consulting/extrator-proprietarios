"""Retry com backoff exponencial e jitter."""

import time
import random
import logging
import functools
from typing import Callable, Optional, Tuple, Type, Any
from dataclasses import dataclass

logger = logging.getLogger("extrator_prop.retry")


@dataclass
class RetryConfig:
    """Configuracao de retry."""
    max_attempts: int = 3
    backoff_factor: float = 2.0
    max_backoff: float = 60.0
    initial_delay: float = 1.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    
    def calculate_delay(self, attempt: int) -> float:
        """Calcula delay para a tentativa."""
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        
        if self.jitter:
            # Adiciona jitter de 25%
            jitter_amount = delay * 0.25
            delay = delay + random.uniform(-jitter_amount, jitter_amount)
        
        return min(delay, self.max_backoff)


def with_retry(config: Optional[RetryConfig] = None):
    """Decorator para retry automatico."""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Tentativa {attempt + 1}/{config.max_attempts} falhou: {e}. "
                            f"Retry em {delay:.1f}s"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"Todas as {config.max_attempts} tentativas falharam: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator


class RetryHandler:
    """Handler de retry para uso explicito."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.attempts = 0
        self.errors = []
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Executa funcao com retry."""
        for attempt in range(self.config.max_attempts):
            try:
                self.attempts = attempt + 1
                return func(*args, **kwargs)
            except self.config.retryable_exceptions as e:
                self.errors.append({"attempt": attempt + 1, "error": str(e)})
                
                if attempt < self.config.max_attempts - 1:
                    delay = self.config.calculate_delay(attempt)
                    time.sleep(delay)
        
        raise self.errors[-1] if self.errors else Exception("Retry falhou")
