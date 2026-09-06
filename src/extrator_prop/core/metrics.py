"""Coletor de metricas de execucao."""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger("extrator_prop.metrics")


class MetricType(Enum):
    """Tipo de metrica."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """Uma metrica individual."""
    name: str
    type: MetricType
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "labels": self.labels,
            "timestamp": self.timestamp
        }


class MetricsCollector:
    """Coletor de metricas central."""
    
    def __init__(self):
        self._metrics: list[Metric] = []
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._timers: dict[str, list[float]] = {}
    
    def increment(self, name: str, value: float = 1, labels: dict[str, str] | None = None):
        """Incrementa um contador."""
        key = self._make_key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value
        self._metrics.append(Metric(
            name=name,
            type=MetricType.COUNTER,
            value=self._counters[key],
            labels=labels or {}
        ))
    
    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Define um gauge."""
        key = self._make_key(name, labels)
        self._gauges[key] = value
        self._metrics.append(Metric(
            name=name,
            type=MetricType.GAUGE,
            value=value,
            labels=labels or {}
        ))
    
    def timer(self, name: str) -> "TimerContext":
        """Cria um timer."""
        return TimerContext(self, name)
    
    def histogram(self, name: str, value: float, labels: dict[str, str] | None = None):
        """Adiciona ao histograma."""
        key = self._make_key(name, labels)
        if key not in self._timers:
            self._timers[key] = []
        self._timers[key].append(value)
        self._metrics.append(Metric(
            name=name,
            type=MetricType.HISTOGRAM,
            value=value,
            labels=labels or {}
        ))
    
    def _make_key(self, name: str, labels: dict[str, str] | None) -> str:
        """Cria chave unica."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_summary(self) -> dict[str, Any]:
        """Obtem resumo das metricas."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "timers": {
                key: {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0
                }
                for key, values in self._timers.items()
            },
            "total_metrics": len(self._metrics)
        }
    
    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionario."""
        return {
            "summary": self.get_summary(),
            "metrics": [m.to_dict() for m in self._metrics[-100:]]  # Ultimas 100
        }
    
    def reset(self):
        """Reseta metricas."""
        self._metrics.clear()
        self._counters.clear()
        self._gauges.clear()
        self._timers.clear()


class TimerContext:
    """Context manager para timers."""
    
    def __init__(self, collector: MetricsCollector, name: str, labels: dict[str, str] | None = None):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.monotonic()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (time.monotonic() - self.start_time) * 1000
            self.collector.histogram(self.name, duration, self.labels)
        return False


# Instancia global
metrics = MetricsCollector()
