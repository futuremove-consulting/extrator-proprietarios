"""Type aliases e estruturas de dados."""

from typing import TypedDict, Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class EntityType(str, Enum):
    """Tipo de entidade."""
    PESSOA_FISICA = "Pessoa Fisica"
    PESSOA_JURIDICA = "Pessoa Juridica"
    DESCONHECIDO = "Desconhecido"


class ValidationStatus(str, Enum):
    """Status de validacao."""
    VALIDADO = "validado"
    NAO_VALIDADO = "nao_validado"
    AMBIGUO = "ambiguo_revisao"
    NAO_CORRESPONDE = "nao_correspondente"
    ERRO = "erro"


class ConfidenceLevel(str, Enum):
    """Nivel de confianca."""
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


@dataclass
class Address:
    """Endereco estruturado."""
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    full: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            k: v for k, v in self.__dict__.items() 
            if v is not None
        }


@dataclass 
class PhoneValidation:
    """Resultado de validacao de telefone/whatsapp."""
    number: str
    is_valid: bool = False
    donodozap_com: bool = False
    donodozap_com_br: bool = False
    name_match_score: float = 0.0
    captei_validated: bool = False
    confidence: ConfidenceLevel = ConfidenceLevel.BAIXA
    source: Optional[str] = None


@dataclass
class EmailValidation:
    """Resultado de validacao de e-mail."""
    email: str
    is_valid: bool = False
    source: Optional[str] = None


@dataclass
class CanonicalContact:
    """Contato no modelo canonico unificado."""
    name: str
    source: str
    source_id: Optional[str] = None
    entity_type: EntityType = EntityType.DESCONHECIDO
    phones: List[PhoneValidation] = field(default_factory=list)
    emails: List[EmailValidation] = field(default_factory=list)
    cpf: Optional[str] = None
    address: Optional[Address] = None
    validation_status: ValidationStatus = ValidationStatus.NAO_VALIDADO
    confidence: ConfidenceLevel = ConfidenceLevel.BAIXA
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Converte para dicionario."""
        return {
            "name": self.name,
            "source": self.source,
            "source_id": self.source_id,
            "entity_type": self.entity_type.value,
            "phones": [
                {
                    "number": p.number,
                    "is_valid": p.is_valid,
                    "donodozap_com": p.donodozap_com,
                    "donodozap_com_br": p.donodozap_com_br,
                    "name_match_score": p.name_match_score,
                    "confidence": p.confidence.value,
                    "source": p.source
                }
                for p in self.phones
            ],
            "emails": [
                {
                    "email": e.email,
                    "is_valid": e.is_valid,
                    "source": e.source
                }
                for e in self.emails
            ],
            "cpf": self.cpf,
            "address": self.address.to_dict() if self.address else None,
            "validation_status": self.validation_status.value,
            "confidence": self.confidence.value,
            "metadata": self.metadata
        }
