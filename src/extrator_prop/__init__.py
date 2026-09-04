"""Extrator de Proprietarios - Modulo de captacao e validacao."""

__version__ = "0.1.0"
__author__ = "Future Move Consulting"

from extrator_prop.features import FeatureFlags
from extrator_prop.config import Config
from extrator_prop.exceptions import (
    ExtratorError,
    AgentError,
    ValidationError,
    RateLimitError,
    AuthenticationError
)

__all__ = [
    "__version__",
    "FeatureFlags",
    "Config",
    "ExtratorError",
    "AgentError",
    "ValidationError",
    "RateLimitError",
    "AuthenticationError",
]
