"""Configuracao central do modulo."""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict
from pathlib import Path


@dataclass
class AgentConfig:
    """Configuracao de um agente."""
    enabled: bool = True
    base_url: str = ""
    timeout: float = 30.0
    max_retries: int = 3
    rate_limit: int = 30  # requests por minuto


@dataclass
class Config:
    """Configuracao central do modulo extrator."""
    
    # Diretorios
    base_dir: Path = field(default_factory=lambda: Path.cwd())
    data_dir: Optional[Path] = None
    logs_dir: Optional[Path] = None
    
    # Feature flags (referencia ao modulo features)
    features: Optional[object] = None
    
    # Configuracoes de agentes
    captei: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True,
        base_url="https://app.captei.com.br",
        rate_limit=60
    ))
    
    fisgar: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True,
        base_url="https://painel.fisgar.com.br",
        rate_limit=30
    ))
    
    eemovel: AgentConfig = field(default_factory=lambda: AgentConfig(
        enabled=True,
        base_url="https://app.eemovel.com.br",
        rate_limit=30
    ))
    
    # Credenciais (carregadas de env)
    captei_token: Optional[str] = None
    captei_user_key: Optional[str] = None
    fisgar_username: Optional[str] = None
    fisgar_password: Optional[str] = None
    eemovel_username: Optional[str] = None
    eemovel_password: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json ou text
    log_file: Optional[Path] = None
    
    @classmethod
    def from_env(cls) -> "Config":
        """Carrega configuracao de variaveis de ambiente."""
        config = cls()
        
        # Diretorios
        if data_dir := os.getenv("FP_DATA_DIR"):
            config.data_dir = Path(data_dir)
        if logs_dir := os.getenv("FP_LOGS_DIR"):
            config.logs_dir = Path(logs_dir)
        
        # Credenciais
        config.captei_token = os.getenv("CAPTEI_TOKEN")
        config.captei_user_key = os.getenv("CAPTEI_USER_KEY")
        config.fisgar_username = os.getenv("FISGAR_USERNAME")
        config.fisgar_password = os.getenv("FISGAR_PASSWORD")
        config.eemovel_username = os.getenv("EEMOVEL_USERNAME")
        config.eemovel_password = os.getenv("EEMOVEL_PASSWORD")
        
        # Logging
        config.log_level = os.getenv("LOG_LEVEL", "INFO")
        config.log_format = os.getenv("LOG_FORMAT", "json")
        
        return config
    
    def validate(self) -> list:
        """Valida configuracao e retorna lista de erros."""
        errors = []
        
        if self.captei.enabled and not self.captei_token:
            errors.append("CAPTEI_TOKEN nao configurado")
        if self.captei.enabled and not self.captei_user_key:
            errors.append("CAPTEI_USER_KEY nao configurado")
        
        if self.fisgar.enabled and not self.fisgar_username:
            errors.append("FISGAR_USERNAME nao configurado")
        
        if self.eemovel.enabled and not self.eemovel_username:
            errors.append("EEMOVEL_USERNAME nao configurado")
        
        return errors


# Instancia global
config = Config.from_env()
