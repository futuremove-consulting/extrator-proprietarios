"""Testes para health.py."""

from extrator_prop.core.health import (
    HealthChecker,
    HealthCheckResult,
    HealthStatus
)


class TestHealthStatus:
    """Testes para HealthStatus."""
    
    def test_status_values(self):
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestHealthCheckResult:
    """Testes para HealthCheckResult."""
    
    def test_to_dict(self):
        result = HealthCheckResult(
            name="test_check",
            status=HealthStatus.HEALTHY,
            message="All good",
            duration_ms=15.5
        )
        
        data = result.to_dict()
        assert data["name"] == "test_check"
        assert data["status"] == "healthy"
        assert data["duration_ms"] == 15.5


class TestHealthChecker:
    """Testes para HealthChecker."""
    
    def test_register_and_check(self):
        checker = HealthChecker()
        checker.register("test", lambda: {"status": "healthy", "message": "OK"})
        
        result = checker.check("test")
        assert result.status == HealthStatus.HEALTHY
        assert result.message == "OK"
    
    def test_check_unregistered(self):
        checker = HealthChecker()
        result = checker.check("unknown")
        
        assert result.status == HealthStatus.UNKNOWN
    
    def test_check_all_healthy(self):
        checker = HealthChecker()
        checker.register("check1", lambda: {"status": "healthy"})
        checker.register("check2", lambda: {"status": "healthy"})
        
        results = checker.check_all()
        assert len(results) == 2
        assert all(r.status == HealthStatus.HEALTHY for r in results.values())
    
    def test_overall_status_healthy(self):
        checker = HealthChecker()
        checker.register("c1", lambda: {"status": "healthy"})
        
        assert checker.get_overall_status() == HealthStatus.HEALTHY
    
    def test_overall_status_unhealthy(self):
        checker = HealthChecker()
        checker.register("c1", lambda: {"status": "healthy"})
        checker.register("c2", lambda: {"status": "unhealthy"})
        
        assert checker.get_overall_status() == HealthStatus.UNHEALTHY
    
    def test_to_dict(self):
        checker = HealthChecker()
        checker.register("c1", lambda: {"status": "healthy"})
        
        data = checker.to_dict()
        assert "status" in data
        assert "checks" in data
