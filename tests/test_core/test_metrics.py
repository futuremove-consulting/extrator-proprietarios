"""Testes para metrics.py."""

import pytest
from extrator_prop.core.metrics import (
    MetricsCollector,
    MetricType,
    TimerContext
)


class TestMetricType:
    """Testes para MetricType."""
    
    def test_type_values(self):
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"


class TestMetricsCollector:
    """Testes para MetricsCollector."""
    
    def test_increment(self):
        collector = MetricsCollector()
        collector.increment("requests", 1, {"source": "captei"})
        collector.increment("requests", 1, {"source": "captei"})
        
        summary = collector.get_summary()
        assert summary["counters"]["requests{source=captei}"] == 2
    
    def test_gauge(self):
        collector = MetricsCollector()
        collector.gauge("active_sessions", 5.0)
        collector.gauge("active_sessions", 10.0)
        
        summary = collector.get_summary()
        assert summary["gauges"]["active_sessions"] == 10.0  # Ultimo valor
    
    def test_histogram(self):
        collector = MetricsCollector()
        collector.histogram("request_duration", 100.0)
        collector.histogram("request_duration", 200.0)
        collector.histogram("request_duration", 300.0)
        
        summary = collector.get_summary()
        timer_data = summary["timers"]["request_duration"]
        assert timer_data["count"] == 3
        assert timer_data["avg"] == 200.0
        assert timer_data["min"] == 100.0
        assert timer_data["max"] == 300.0
    
    def test_timer_context(self):
        collector = MetricsCollector()
        
        with collector.timer("operation"):
            pass  # Operacao instantanea
        
        summary = collector.get_summary()
        assert "operation" in summary["timers"]
    
    def test_reset(self):
        collector = MetricsCollector()
        collector.increment("test")
        collector.gauge("value", 1.0)
        
        collector.reset()
        summary = collector.get_summary()
        
        assert len(summary["counters"]) == 0
        assert len(summary["gauges"]) == 0
    
    def test_to_dict(self):
        collector = MetricsCollector()
        collector.increment("requests")
        
        data = collector.to_dict()
        assert "summary" in data
        assert "metrics" in data
