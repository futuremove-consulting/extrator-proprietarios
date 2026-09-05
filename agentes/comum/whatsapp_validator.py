"""WhatsApp Validation - Base classes and types for Dono do Zap validators."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import re


class ValidationSource(Enum):
    """Source of WhatsApp validation."""
    CAPTEI = "captei"
    DONODOZAP_BR = "donodozap.com.br"
    DONODOZAP_COM = "donodozap.com"
    MANUAL = "manual"


class ValidationTier(Enum):
    """Validation tier/level."""
    FREE = "free"           # Nome apenas (busca inicial gratuita)
    PAID = "paid"           # Relatório completo (foto, dados adicionais)
    FAILED = "failed"       # Falha na consulta
    NOT_FOUND = "not_found" # Número não encontrado


@dataclass
class WhatsAppValidationResult:
    """Resultado padronizado de validação de WhatsApp."""
    phone_digits: str                    # Apenas dígitos (ex: 5511999999999)
    phone_formatted: str                 # Formatado para exibição
    source: ValidationSource
    tier: ValidationTier
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Dados da validação
    nome_exibicao: Optional[str] = None      # Nome público do WhatsApp
    foto_perfil_url: Optional[str] = None    # URL da foto de perfil
    status_whatsapp: Optional[str] = None    # "ativo", "inativo", "não_cadastrado"
    dados_adicionais: Dict[str, Any] = field(default_factory=dict)

    # Metadados
    custo_estimado: float = 0.0              # Custo em reais (0 para gratuito)
    tempo_resposta_ms: int = 0
    erro: Optional[str] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phone_digits": self.phone_digits,
            "phone_formatted": self.phone_formatted,
            "source": self.source.value,
            "tier": self.tier.value,
            "timestamp": self.timestamp,
            "nome_exibicao": self.nome_exibicao,
            "foto_perfil_url": self.foto_perfil_url,
            "status_whatsapp": self.status_whatsapp,
            "dados_adicionais": self.dados_adicionais,
            "custo_estimado": self.custo_estimado,
            "tempo_resposta_ms": self.tempo_resposta_ms,
            "erro": self.erro
        }

    def is_valid(self) -> bool:
        """Verifica se a validação foi bem-sucedida (mesmo que só tier FREE)."""
        return self.tier in (ValidationTier.FREE, ValidationTier.PAID) and self.nome_exibicao is not None

    def has_paid_data(self) -> bool:
        """Verifica se tem dados do relatório pago."""
        return self.tier == ValidationTier.PAID


class WhatsAppValidator(ABC):
    """Classe base abstrata para validadores de WhatsApp."""

    def __init__(self, headless: bool = True, timeout_ms: int = 30000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._browser = None
        self._page = None

    @property
    @abstractmethod
    def source(self) -> ValidationSource:
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        pass

    @abstractmethod
    async def validate(self, phone: str) -> WhatsAppValidationResult:
        """Valida um número de WhatsApp. Retorna WhatsAppValidationResult."""
        pass

    @abstractmethod
    async def validate_batch(self, phones: List[str]) -> List[WhatsAppValidationResult]:
        """Valida múltiplos números em lote."""
        pass

    def _normalize_phone(self, phone: str) -> str:
        """Normaliza telefone para apenas dígitos com código do país."""
        digits = re.sub(r'\D', '', phone)
        if not digits.startswith('55') and len(digits) >= 10:
            digits = '55' + digits
        return digits

    def _format_phone(self, digits: str) -> str:
        """Formata para exibição: (XX) XXXXX-XXXX"""
        if len(digits) == 13 and digits.startswith('55'):
            return f"({digits[2:4]}) {digits[4:9]}-{digits[9:]}"
        elif len(digits) == 12 and digits.startswith('55'):
            return f"({digits[2:4]}) {digits[4:8]}-{digits[8:]}"
        elif len(digits) == 11:
            return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        elif len(digits) == 10:
            return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        return digits

    async def __aenter__(self):
        await self._init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_browser()

    @abstractmethod
    async def _init_browser(self):
        pass

    @abstractmethod
    async def _close_browser(self):
        pass