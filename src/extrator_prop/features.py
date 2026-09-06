"""Feature flags para ativacao gradual de funcionalidades."""

import os
from dataclasses import dataclass


@dataclass
class FeatureFlags:
    """Feature flags para controle de funcionalidades."""
    
    # Agentes
    CAPTEI_ENABLED: bool = True
    FISGAR_ENABLED: bool = True
    EEMOVEL_ENABLED: bool = True
    
    # Funcionalidades
    DONODOZAP_VALIDATION: bool = True
    WHATSAPP_VALIDATION: bool = False
    CPF_VALIDATION: bool = False
    EMAIL_VALIDATION: bool = False
    
    # Modos de operacao
    DRY_RUN: bool = False
    DEBUG_MODE: bool = False
    VERBOSE_LOGGING: bool = False
    
    # Rate limiting e resiliencia
    RATE_LIMIT_ENABLED: bool = True
    RETRY_ENABLED: bool = True
    CIRCUIT_BREAKER_ENABLED: bool = True
    
    @classmethod
    def from_env(cls, env: dict | None = None) -> "FeatureFlags":
        """Carrega feature flags de variaveis de ambiente."""
        env = env or os.environ
        
        def bool_var(key: str, default: bool) -> bool:
            val = env.get(key, str(default).lower())
            return val.lower() in ("true", "1", "yes", "on")
        
        return cls(
            CAPTEI_ENABLED=bool_var("FP_CAPTEI_ENABLED", True),
            FISGAR_ENABLED=bool_var("FP_FISGAR_ENABLED", True),
            EEMOVEL_ENABLED=bool_var("FP_EEMOVEL_ENABLED", True),
            DONODOZAP_VALIDATION=bool_var("FP_DONODOZAP", True),
            WHATSAPP_VALIDATION=bool_var("FP_WHATSAPP", False),
            CPF_VALIDATION=bool_var("FP_CPF", False),
            EMAIL_VALIDATION=bool_var("FP_EMAIL", False),
            DRY_RUN=bool_var("FP_DRY_RUN", False),
            DEBUG_MODE=bool_var("FP_DEBUG_MODE", False),
            VERBOSE_LOGGING=bool_var("FP_VERBOSE", False),
            RATE_LIMIT_ENABLED=bool_var("FP_RATE_LIMIT", True),
            RETRY_ENABLED=bool_var("FP_RETRY", True),
            CIRCUIT_BREAKER_ENABLED=bool_var("FP_CIRCUIT_BREAKER", True),
        )
    
    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            k: v for k, v in self.__dict__.items() 
            if not k.startswith("_")
        }


# Instancia global padrao
features = FeatureFlags.from_env()
