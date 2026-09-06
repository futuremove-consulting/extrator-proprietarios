"""Cliente HTTP com retry, timeout e circuit breaker."""

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("extrator_prop.http")


class CircuitState(Enum):
    """Estado do circuit breaker."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker para proteger contra falhas em cascata."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    _failures: int = 0
    _last_failure_time: float = 0.0
    _state: CircuitState = CircuitState.CLOSED
    
    def can_execute(self) -> bool:
        """Verifica se pode executar."""
        if self._state == CircuitState.CLOSED:
            return True
        
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                return True
            return False
        
        # HALF_OPEN permite uma tentativa
        return True
    
    def record_success(self):
        """Registra sucesso."""
        self._failures = 0
        self._state = CircuitState.CLOSED
    
    def record_failure(self):
        """Registra falha."""
        self._failures += 1
        self._last_failure_time = time.time()
        
        if self._failures >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit breaker aberto ({self._failures} falhas)")


@dataclass
class HTTPResponse:
    """Resposta HTTP."""
    status_code: int
    body: str
    headers: dict[str, str] = field(default_factory=dict)
    duration_ms: float = 0.0
    
    def json(self) -> Any:
        """Parse JSON."""
        return json.loads(self.body)
    
    @property
    def ok(self) -> bool:
        """Verifica se foi sucesso."""
        return 200 <= self.status_code < 300


class HTTPClient:
    """Cliente HTTP com retry e circuit breaker."""
    
    def __init__(
        self,
        base_url: str = "",
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        headers: dict[str, str] | None = None
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.default_headers = headers or {}
        self.circuit_breaker = CircuitBreaker()
    
    def request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None
    ) -> HTTPResponse:
        """Executa requisicao HTTP com retry."""
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker aberto")
        
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            url = f"{url}?{query}"
        
        merged_headers = {**self.default_headers, **(headers or {})}
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                start = time.time()
                
                body = json.dumps(data).encode() if data else None
                req = urllib.request.Request(
                    url, 
                    data=body,
                    headers=merged_headers,
                    method=method
                )
                
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    duration = (time.time() - start) * 1000
                    resp_body = resp.read().decode("utf-8")
                    resp_headers = dict(resp.headers)
                    
                    response = HTTPResponse(
                        status_code=resp.status,
                        body=resp_body,
                        headers=resp_headers,
                        duration_ms=duration
                    )
                    
                    self.circuit_breaker.record_success()
                    return response
                    
            except urllib.error.HTTPError as e:
                last_error = e
                if e.code in (424, 429):  # Rate limit
                    wait = (attempt + 1) * self.backoff_factor
                    logger.warning(f"Rate limit, aguardando {wait}s")
                    time.sleep(wait)
                elif e.code >= 500:  # Server error, retry
                    wait = (attempt + 1) * self.backoff_factor
                    time.sleep(wait)
                else:  # Client error, nao retry
                    raise
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait = (attempt + 1) * self.backoff_factor
                    time.sleep(wait)
        
        self.circuit_breaker.record_failure()
        raise last_error or Exception("Falha na requisicao")
    
    def get(self, path: str, params: dict | None = None, **kwargs) -> HTTPResponse:
        """GET request."""
        return self.request("GET", path, params=params, **kwargs)
    
    def post(self, path: str, data: dict | None = None, **kwargs) -> HTTPResponse:
        """POST request."""
        return self.request("POST", path, data=data, **kwargs)
