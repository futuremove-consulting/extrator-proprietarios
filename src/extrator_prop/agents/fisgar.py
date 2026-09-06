"""Agente Fisgar para extracao de proprietarios."""

from typing import Optional, Dict, List
from pathlib import Path

from extrator_prop.agents.base import AgentBase
from extrator_prop.config import AgentConfig
from extrator_prop.features import FeatureFlags
from extrator_prop.constants import FISGAR_BASE_URL, RATE_LIMITS
from extrator_prop.types import CanonicalContact, PhoneValidation, EmailValidation


class FisgarAgent(AgentBase):
    """Agente para extracao de proprietarios do sistema Fisgar."""
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        features: Optional[FeatureFlags] = None,
        lot_name: str = "default",
        base_dir: Path = Path(".")
    ):
        if config is None:
            config = AgentConfig(
                enabled=True,
                base_url=FISGAR_BASE_URL,
                rate_limit=RATE_LIMITS.get("fisgar", 30)
            )
        if features is None:
            features = FeatureFlags.from_env()
        
        super().__init__(config, features, lot_name, base_dir)
        
        self._auth_token = None
    
    @property
    def agent_name(self) -> str:
        return "fisgar"
    
    @property
    def source_key(self) -> str:
        return "fisgar"
    
    def authenticate(self, username: str, password: str):
        """Autentica no Fisgar."""
        self.logger.info("Autenticando no Fisgar")
        # TODO: Implementar autenticacao real
        self._auth_token = "dummy_token"
        self.http.default_headers["Authorization"] = f"Bearer {self._auth_token}"
    
    def extract_listing(self, address: str, **kwargs) -> List[Dict]:
        """Extrai listagem de proprietarios do Fisgar."""
        self.logger.info(f"Extraindo listagem Fisgar: {address}")
        
        # TODO: Implementar extracao real
        # Por enquanto retorna vazio
        return []
    
    def extract_details(self, record_key: str) -> Optional[Dict]:
        """Extrai detalhes de um registro."""
        self.logger.info(f"Extraindo detalhes: {record_key}")
        # TODO: Implementar extracao de detalhes
        return None
    
    def map_to_canonical(self, raw_record: Dict) -> CanonicalContact:
        """Mapeia registro bruto do Fisgar para modelo canonico."""
        phones = []
        phone_raw = raw_record.get("telefone", "")
        if phone_raw:
            phones.append(PhoneValidation(number=phone_raw, source="fisgar"))
        
        emails = []
        email_raw = raw_record.get("email", "")
        if email_raw:
            emails.append(EmailValidation(email=email_raw, source="fisgar"))
        
        contact = CanonicalContact(
            name=raw_record.get("nome", ""),
            source=self.source_key,
            source_id=raw_record.get("id"),
            phones=phones,
            emails=emails,
            metadata={
                "unidade": raw_record.get("unidade"),
                "endereco": raw_record.get("endereco")
            }
        )
        
        return contact
