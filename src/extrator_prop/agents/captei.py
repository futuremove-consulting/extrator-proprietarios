"""Agente Captei para extracao de proprietarios."""

from typing import Optional, Dict, List
from pathlib import Path

from extrator_prop.agents.base import AgentBase
from extrator_prop.config import AgentConfig
from extrator_prop.features import FeatureFlags
from extrator_prop.constants import CAPTEI_BASE_URL, RATE_LIMITS
from extrator_prop.types import CanonicalContact


class CapteiAgent(AgentBase):
    """Agente para extracao de proprietarios do sistema Captei."""
    
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
                base_url=CAPTEI_BASE_URL,
                rate_limit=RATE_LIMITS.get("captei", 60)
            )
        if features is None:
            features = FeatureFlags.from_env()
        
        super().__init__(config, features, lot_name, base_dir)
        
        # Headers especificos do Captei
        self._token = None
        self._user_key = None
    
    @property
    def agent_name(self) -> str:
        return "captei"
    
    @property
    def source_key(self) -> str:
        return "captei"
    
    def set_credentials(self, token: str, user_key: str):
        """Configura credenciais da API."""
        self._token = token
        self._user_key = user_key
        self.http.default_headers.update({
            "Token": token,
            "User-Key": user_key
        })
    
    def extract_listing(self, address: str, **kwargs) -> List[Dict]:
        """Extrai listagem de proprietarios do Captei."""
        self.logger.info(f"Extraindo listagem Captei: {address}")
        
        if not self.http:
            raise RuntimeError("HTTP client nao configurado")
        
        # Usar API de Listings se disponivel
        # Para captacao ativa, seria outro endpoint
        response = self.http.get(
            "/api/listings/search",
            params={
                "text": address,
                "status": "active",
                "page_size": 100
            }
        )
        
        if response.ok:
            data = response.json()
            return data.get("data", [])
        
        return []
    
    def extract_details(self, record_key: str) -> Optional[Dict]:
        """Extrai detalhes de um registro."""
        self.logger.info(f"Extraindo detalhes: {record_key}")
        # Captei pode nao ter endpoint de detalhes publico
        return None
    
    def map_to_canonical(self, raw_record: Dict) -> CanonicalContact:
        """Mapeia registro bruto do Captei para modelo canonico."""
        address_data = raw_record.get("address", {})
        
        phones = []
        # Captei nao expoe telefone na API publica
        
        emails = []
        
        contact = CanonicalContact(
            name=raw_record.get("advertiser_name", raw_record.get("name", "")),
            source=self.source_key,
            source_id=raw_record.get("id"),
            phones=phones,
            emails=emails,
            metadata={
                "portal": raw_record.get("portal"),
                "property_type": raw_record.get("property_type"),
                "business_type": raw_record.get("business_type"),
                "raw_address": address_data.get("full")
            }
        )
        
        return contact
