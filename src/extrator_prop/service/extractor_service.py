"""Servico HTTP de extracao (Flask).

Entry point:
    extrator-api [--host 0.0.0.0] [--port 8000]

Endpoints:
    GET  /healthz          -> probe de vida
    POST /api/v1/extract   -> extrai proprietarios de um endereco
"""
from __future__ import annotations

from dataclasses import dataclass
from time import time

from extrator_prop.agents import CapteiAgent, EEmovelAgent, FisgarAgent
from extrator_prop.agents.base import AgentBase, ExtractionStats
from extrator_prop.config import AgentConfig, Config
from extrator_prop.exceptions import ExtratorError
from extrator_prop.features import FeatureFlags
from extrator_prop.logging import get_logger
from extrator_prop.types import CanonicalContact

logger = get_logger("service")


@dataclass
class ExtractionResult:
    """Resultado consolidado de uma extracao HTTP."""
    results: list[dict]
    stats: ExtractionStats
    tipo_documento: str


class ExtractorService:
    """Orquestrador stateless — sem persiste em disco (ideal para HTTP).

    Reusa os agentes existentes (Captei/EEmovel/Fisgar) e expõe a lista de
    contatos canônicos já serializados via ``CanonicalContact.to_dict()``,
    compatíveis com o contrato ``ExtractedOwner`` do PilotCRM.
    """

    def __init__(
        self,
        config: Config | None = None,
        features: FeatureFlags | None = None,
    ):
        self.config = config or Config()
        self.features = features or (
            self.config.features if isinstance(self.config.features, FeatureFlags) else FeatureFlags.from_env()
        )

    def _build_agent(self, agent_cls: type[AgentBase], agent_cfg: AgentConfig, lot_name: str) -> AgentBase:
        return agent_cls(config=agent_cfg, features=self.features, lot_name=lot_name)

    def build_agents(self, address: str) -> list[AgentBase]:
        slug = address.lower().strip().replace(" ", "_")[:64]
        agents: list[AgentBase] = []
        if self.features.CAPTEI_ENABLED and self.config.captei.enabled:
            agents.append(self._build_agent(CapteiAgent, self.config.captei, f"{slug}-captei"))
        if self.features.EEMOVEL_ENABLED and self.config.eemovel.enabled:
            agents.append(self._build_agent(EEmovelAgent, self.config.eemovel, f"{slug}-eemovel"))
        if self.features.FISGAR_ENABLED and self.config.fisgar.enabled:
            agents.append(self._build_agent(FisgarAgent, self.config.fisgar, f"{slug}-fisgar"))
        return agents

    def list_owners(self, address: str, tipo_documento: str = "proprietario") -> ExtractionResult:
        stats = ExtractionStats(start_time=time())
        results: list[dict] = []
        try:
            for agent in self.build_agents(address):
                raw_listing = agent.extract_listing(address)
                stats.total += len(raw_listing)
                for record in raw_listing:
                    if not agent.is_pessoa_fisica(record):
                        stats.excluded += 1
                        continue
                    canonical: CanonicalContact = agent.map_to_canonical(record)
                    if canonical is not None:
                        results.append(canonical.to_dict())
                        stats.completed += 1
        except ExtratorError:
            raise
        except Exception as exc:  # pragma: no cover
            logger.error("Falha na extracao", extra={"address": address, "error": str(exc)})
            raise ExtratorError("Falha inesperada durante a extracao", {"address": address}) from exc
        finally:
            stats.end_time = time()
        return ExtractionResult(results=results, stats=stats, tipo_documento=tipo_documento)
