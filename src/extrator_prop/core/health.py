"""Health check para monitoramento."""

import time
import logging
from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("extrator_prop.health")


class HealthStatus(Enum):
    """Status de health."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Resultado de um health check."""
    name: str
    status: HealthStatus
    message: str
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class HealthChecker:
    """Health checker para o modulo."""
    
    def __init__(self):
        self._checks: Dict[str, callable] = {}
        self._last_results: Dict[str, HealthCheckResult] = {}
    
    def register(self, name: str, check_func: callable):
        """Registra um health check."""
        self._checks[name] = check_func
    
    def check(self, name: str) -> HealthCheckResult:
        """Executa um health check especifico."""
        if name not in self._checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Health check '{name}' nao registrado"
            )
        
        start = time.monotonic()
        try:
            result = self._checks[name]()
            if isinstance(result, HealthCheckResult):
                result.duration_ms = (time.monotonic() - start) * 1000
                self._last_results[name] = result
                return result
            else:
                # Assume que retornou dict
                result_dict = result if isinstance(result, dict) else {"status": "healthy"}
                duration = (time.monotonic() - start) * 1000
                status = HealthStatus(result_dict.get("status", "healthy"))
                return HealthCheckResult(
                    name=name,
                    status=status,
                    message=result_dict.get("message", ""),
                    duration_ms=duration,
                    metadata=result_dict.get("metadata", {})
                )
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                duration_ms=duration
            )
    
    def check_all(self) -> Dict[str, HealthCheckResult]:
        """Executa todos os health checks."""
        results = {}
        for name in self._checks:
            results[name] = self.check(name)
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """Obtem status geral."""
        results = self.check_all()
        
        statuses = [r.status for r in results.values()]
        
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        
        return HealthStatus.UNKNOWN
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionario."""
        results = self.check_all()
        overall = self.get_overall_status()
        
        return {
            "status": overall.value,
            "checks": {name: result.to_dict() for name, result in results.items()},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Instancia global
health_checker = HealthChecker()
