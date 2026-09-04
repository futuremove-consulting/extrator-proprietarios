"""Classe base para todos os agentes de extracao."""

import json
import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, field

from extrator_prop.config import AgentConfig
from extrator_prop.features import FeatureFlags
from extrator_prop.constants import RATE_LIMITS, DEFAULT_TIMEOUT
from extrator_prop.exceptions import AgentError, RateLimitError, ValidationError
from extrator_prop.types import CanonicalContact, EntityType, ValidationStatus
from extrator_prop.logging import setup_logging, get_logger
from extrator_prop.http import HTTPClient


@dataclass
class ExtractionStats:
    """Estatisticas de extracao."""
    total: int = 0
    pending: int = 0
    completed: int = 0
    excluded: int = 0
    errors: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "pending": self.pending,
            "completed": self.completed,
            "excluded": self.excluded,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds
        }


class AgentBase(ABC):
    """Classe base para agentes de extracao."""
    
    def __init__(
        self,
        config: AgentConfig,
        features: FeatureFlags,
        lot_name: str,
        base_dir: Path = Path(".")
    ):
        self.config = config
        self.features = features
        self.lot_name = lot_name
        self.base_dir = base_dir
        
        # Logger
        self.logger = get_logger(self.agent_name)
        
        # Diretorios
        self.lot_dir = base_dir / "data" / "lots" / lot_name
        self.lot_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivos
        self.manifest_path = self.lot_dir / "manifest.ndjson"
        self.checkpoint_path = self.lot_dir / "checkpoint.json"
        self.log_path = self.lot_dir / "extraction_log.jsonl"
        
        # Estado
        self.stats = ExtractionStats()
        self._manifest: List[Dict] = []
        self._checkpoint: Dict = {}
        
        # HTTP Client (se aplicavel)
        if self.requires_http:
            self.http = HTTPClient(
                base_url=config.base_url,
                timeout=config.timeout,
                max_retries=config.max_retries
            )
        else:
            self.http = None
    
    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Nome do agente."""
        pass
    
    @property
    @abstractmethod
    def source_key(self) -> str:
        """Chave de origem (ex: captei, fisgar, eemovel)."""
        pass
    
    @property
    def requires_http(self) -> bool:
        """Se o agente requer cliente HTTP."""
        return True
    
    @abstractmethod
    def extract_listing(self, address: str, **kwargs) -> List[Dict]:
        """Extrai listagem bruta da fonte."""
        pass
    
    @abstractmethod
    def extract_details(self, record_key: str) -> Optional[Dict]:
        """Extrai detalhes de um registro."""
        pass
    
    @abstractmethod
    def map_to_canonical(self, raw_record: Dict) -> CanonicalContact:
        """Mapeia registro bruto para modelo canonico."""
        pass
    
    def validate_entity(self, record: Dict) -> EntityType:
        """Valida tipo de entidade."""
        name = record.get("name", "")
        if not name:
            return EntityType.DESCONHECIDO
        
        # Heuristicas simples
        pj_indicators = ["ltda", "s.a.", "sa ", "eireli ", "me ", "epp "]
        name_lower = name.lower()
        
        for indicator in pj_indicators:
            if indicator in name_lower:
                return EntityType.PESSOA_JURIDICA
        
        return EntityType.PESSOA_FISICA
    
    def is_pessoa_fisica(self, record: Dict) -> bool:
        """Verifica se e pessoa fisica."""
        return self.validate_entity(record) == EntityType.PESSOA_FISICA
    
    def append_to_manifest(self, record: Dict):
        """Adiciona registro ao manifest."""
        with open(self.manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "
")
        self._manifest.append(record)
    
    def save_checkpoint(self):
        """Salva checkpoint."""
        checkpoint = {
            "lot_name": self.lot_name,
            "agent": self.agent_name,
            "source": self.source_key,
            "stats": self.stats.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checkpoint": self._checkpoint
        }
        with open(self.checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
    
    def load_checkpoint(self) -> Dict:
        """Carrega checkpoint."""
        if self.checkpoint_path.exists():
            with open(self.checkpoint_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._checkpoint = data.get("checkpoint", {})
                return self._checkpoint
        return {}
    
    def log_extraction(self, event: str, data: Dict = None):
        """Log de extracao."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": self.agent_name,
            "event": event,
            "data": data or {}
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "
")
    
    def check_rate_limit(self):
        """Verifica rate limit (placeholder para implementacao futura)."""
        # TODO: Implementar rate limit real
        pass
    
    def run(self, address: str, **kwargs) -> ExtractionStats:
        """Executa extracao completa."""
        self.logger.info(f"Iniciando extracao: {address}", extra={"agent": self.agent_name})
        self.stats.start_time = time.time()
        
        try:
            # 1. Carregar checkpoint
            self.load_checkpoint()
            
            # 2. Extrair listagem
            listing = self.extract_listing(address, **kwargs)
            self.stats.total = len(listing)
            self.logger.info(f"Listagem extraida: {len(listing)} registros")
            
            # 3. Processar cada registro
            for record in listing:
                try:
                    # Validar entidade
                    if not self.is_pessoa_fisica(record):
                        record["entity_type"] = EntityType.PESSOA_JURIDICA.value
                        record["state"] = "empresa_classificada"
                        self.stats.excluded += 1
                        self.append_to_manifest(record)
                        continue
                    
                    # Extrair detalhes (se necessario)
                    record_key = record.get("record_key", "")
                    if record_key and self.requires_details:
                        details = self.extract_details(record_key)
                        if details:
                            record.update(details)
                    
                    # Mapear para canonico
                    canonical = self.map_to_canonical(record)
                    record["canonical"] = canonical.to_dict()
                    record["state"] = "resultado_persistido"
                    self.stats.completed += 1
                    
                    self.append_to_manifest(record)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar registro: {e}", extra={"agent": self.agent_name})
                    self.stats.errors += 1
                    record["state"] = "erro"
                    record["error"] = str(e)
                    self.append_to_manifest(record)
                
                # Rate limit
                self.check_rate_limit()
            
            # 4. Salvar checkpoint final
            self.save_checkpoint()
            
        except Exception as e:
            self.logger.error(f"Erro na extracao: {e}", extra={"agent": self.agent_name})
            raise AgentError(self.agent_name, str(e))
        
        finally:
            self.stats.end_time = time.time()
            duration = self.stats.duration_seconds or 0
            self.logger.info(
                f"Extracao concluida: {self.stats.completed}/{self.stats.total} em {duration:.1f}s",
                extra={"agent": self.agent_name, "duration_ms": duration * 1000}
            )
        
        return self.stats
    
    @property
    def requires_details(self) -> bool:
        """Se o agente requer extracao de detalhes."""
        return True
