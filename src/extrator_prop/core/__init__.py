"""Modulos core do sistema."""

from extrator_prop.core.rate_limiter import (
    RateLimiterManager,
    TokenBucketRateLimiter,
    RateLimitConfig,
    rate_limiter_manager
)
from extrator_prop.core.retry import (
    RetryConfig,
    RetryHandler,
    with_retry
)
from extrator_prop.core.health import (
    HealthChecker,
    HealthCheckResult,
    HealthStatus,
    health_checker
)
from extrator_prop.core.metrics import (
    MetricsCollector,
    Metric,
    MetricType,
    TimerContext,
    metrics
)

__all__ = [
    "RateLimiterManager",
    "TokenBucketRateLimiter",
    "RateLimitConfig",
    "rate_limiter_manager",
    "RetryConfig",
    "RetryHandler",
    "with_retry",
    "HealthChecker",
    "HealthCheckResult",
    "HealthStatus",
    "health_checker",
    "MetricsCollector",
    "Metric",
    "MetricType",
    "TimerContext",
    "metrics",
]
