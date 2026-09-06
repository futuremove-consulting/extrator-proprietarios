"""Extrator de Proprietarios - Modulo de captacao e validacao."""

__version__ = "0.1.0"
__author__ = "Future Move Consulting"

from extrator_prop.config import Config
from extrator_prop.exceptions import (
    AgentError,
    AuthenticationError,
    ExtratorError,
    RateLimitError,
    ValidationError,
)
from extrator_prop.features import FeatureFlags

__all__ = [
    "AgentError",
    "AuthenticationError",
    "Config",
    "ExtratorError",
    "FeatureFlags",
    "RateLimitError",
    "ValidationError",
    "__version__",
]
