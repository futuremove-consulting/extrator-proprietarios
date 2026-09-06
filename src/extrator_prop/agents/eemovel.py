"""Agente EEmovel para extracao de proprietarios e moradores."""

from typing import Optional, Dict, List
from pathlib import Path

from extrator_prop.agents.base import AgentBase
from extrator_prop.config import AgentConfig
from extrator_prop.features import FeatureFlags
from extrator_prop.constants import EEMOVEL_BASE_URL, RATE_LIMITS
from extrator_prop.types import CanonicalContact, PhoneValidation, EmailValidation


class EEmovelAgent(AgentBase):
    """Agente para extracao de proprietarios e moradores do sistema EEmovel."""
    
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
                base_url=EEMOVEL_BASE_URL,
                rate_limit=RATE_LIMITS.get("eemovel", 30)
            )
        if features is None:
            features = FeatureFlags.from_env()
        
        super().__init__(config, features, lot_name, base_dir)
        
        self._session_cookies = None
    
    @property
    def agent_name(self) -> str:
        return "eemovel"
    
    @property
    def source_key(self) -> str:
        return "eemovel"
    
    @property
    def requires_details(self) -> bool:
        """EEmovel requer extracao de detalhes."""
        return True
    
    def authenticate(self, username: str, password: str):
        """Autentica no EEmovel."""
        self.logger.info("Autenticando no EEmovel")
        # TODO: Implementar autenticacao real
        self._session_cookies = {}
    
    def extract_listing(self, address: str, **kwargs) -> List[Dict]:
        """Extrai listagem de proprietarios do EEmovel."""
        self.logger.info(f"Extraindo listagem EEmovel: {address}")
        
        # TODO: Implementar extracao real
        return []
    
    def extract_details(self, record_key: str) -> Optional[Dict]:
        """Extrai detalhes de um registro (telefones, emails)."""
        self.logger.info(f"Extraindo detalhes: {record_key}")
        
        # TODO: Implementar extracao de detalhes via browser
        return None
    
    def map_to_canonical(self, raw_record: Dict) -> CanonicalContact:
        """Mapeia registro bruto do EEmovel para modelo canonico."""
        phones = []
        for phone_raw in raw_record.get("telefones", []):
            if isinstance(phone_raw, str):
                phones.append(PhoneValidation(number=phone_raw, source="eemovel"))
            elif isinstance(phone_raw, dict):
                phones.append(PhoneValidation(
                    number=phone_raw.get("numero", ""),
                    source="eemovel"
                ))
        
        emails = []
        for email_raw in raw_record.get("emails", []):
            if isinstance(email_raw, str):
                emails.append(EmailValidation(email=email_raw, source="eemovel"))
            elif isinstance(email_raw, dict):
                emails.append(EmailValidation(
                    email=email_raw.get("email", ""),
                    source="eemovel"
                ))
        
        contact = CanonicalContact(
            name=raw_record.get("nome", ""),
            source=self.source_key,
            source_id=raw_record.get("id"),
            phones=phones,
            emails=emails,
            metadata={
                "unidade": raw_record.get("unidade"),
                "vaga": raw_record.get("vaga"),
                "tipo": raw_record.get("tipo")  # proprietario ou morador
            }
        )
        
        return contact
