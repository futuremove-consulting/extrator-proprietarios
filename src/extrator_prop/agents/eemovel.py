"""Agente EEmovel para extracao de proprietarios e moradores."""

import json
import os
import subprocess
import sys
from pathlib import Path

from extrator_prop.agents.base import AgentBase
from extrator_prop.config import AgentConfig
from extrator_prop.constants import EEMOVEL_BASE_URL, RATE_LIMITS
from extrator_prop.features import FeatureFlags
from extrator_prop.types import CanonicalContact, EmailValidation, PhoneValidation


class EEmovelAgent(AgentBase):
    """Agente para extracao de proprietarios e moradores do sistema EEmovel."""
    
    def __init__(
        self,
        config: AgentConfig | None = None,
        features: FeatureFlags | None = None,
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
    
    def extract_listing(self, address: str, **kwargs) -> list[dict]:
        """Extrai listagem de proprietarios do EEmovel.

        Com EEMOVEL_BROWSER_ENABLED=1, delega ao runner agent-browser
        (agentes/eemovel/runner.py batch-json). Sem a flag, retorna []
        (stub, compatibilidade com testes).
        """
        self.logger.info(f"Extraindo listagem EEmovel: {address}")

        if os.environ.get("EEMOVEL_BROWSER_ENABLED") != "1":
            self.logger.warning("EEMOVEL_BROWSER_ENABLED != 1 — retornando stub vazio")
            return []

        runner_path = Path(
            os.environ.get("EEMOVEL_RUNNER_PATH", "agentes/eemovel/runner.py")
        )
        if not runner_path.exists():
            self.logger.error(f"Runner nao encontrado: {runner_path}")
            return []

        max_consultas = kwargs.get("max_consultas", int(os.environ.get("EEMOVEL_MAX_CONSULTAS", "10")))
        cmd = [
            sys.executable, str(runner_path),
            "--session", os.environ.get("AGENT_BROWSER_SESSION", "eemovel-runner"),
            "batch-json",
            "--endereco", address,
            "--max-consultas", str(max_consultas),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        except subprocess.TimeoutExpired:
            self.logger.error("Runner agent-browser excedeu o timeout (900s)")
            return []

        if proc.returncode != 0:
            self.logger.error(f"Runner falhou (exit {proc.returncode}): {proc.stderr[-300:]}")
            return []

        try:
            records = json.loads(proc.stdout)
        except json.JSONDecodeError:
            self.logger.error("Runner nao retornou JSON valido")
            return []

        self.logger.info(f"Runner devolveu {len(records)} registros reais")
        return records
    
    def extract_details(self, record_key: str) -> dict | None:
        """Extrai detalhes de um registro (telefones, emails)."""
        self.logger.info(f"Extraindo detalhes: {record_key}")
        
        # TODO: Implementar extracao de detalhes via browser
        return None
    
    def map_to_canonical(self, raw_record: dict) -> CanonicalContact:
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
