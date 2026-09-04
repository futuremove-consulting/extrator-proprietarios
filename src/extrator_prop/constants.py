"""Constantes centralizadas do modulo."""

from typing import Dict

# Limites de rate limiting (requests por minuto)
RATE_LIMITS: Dict[str, int] = {
    "captei": 60,
    "fisgar": 30,
    "eemovel": 30,
    "donodozap_com": 30,
    "donodozap_com_br": 30,
}

# Timeouts (segundos)
DEFAULT_TIMEOUT: float = 30.0
CONNECT_TIMEOUT: float = 10.0
READ_TIMEOUT: float = 30.0

# Retry
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_BACKOFF_FACTOR: float = 2.0
MAX_BACKOFF_SECONDS: float = 60.0

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT: float = 60.0

# URLs base
CAPTEI_BASE_URL: str = "https://app.captei.com.br"
FISGAR_BASE_URL: str = "https://painel.fisgar.com.br"
EEMOVEL_BASE_URL: str = "https://app.eemovel.com.br"

# APIs
CAPTEI_LISTINGS_API: str = "https://app.captei.com.br/api/listings/search"

# Versao
VERSION: str = "0.1.0"
