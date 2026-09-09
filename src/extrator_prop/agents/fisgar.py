"""Agente Fisgar para extracao de proprietarios."""

import json
import os
import subprocess
import sys
from pathlib import Path

from extrator_prop.agents.base import AgentBase
from extrator_prop.config import AgentConfig
from extrator_prop.constants import FISGAR_BASE_URL, RATE_LIMITS
from extrator_prop.features import FeatureFlags
from extrator_prop.types import (
    Address,
    CanonicalContact,
    ConfidenceLevel,
    EmailValidation,
    EntityType,
    PhoneValidation,
)


class FisgarAgent(AgentBase):
    """Agente para extracao de proprietarios do sistema Fisgar."""
    
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
    
    def extract_listing(self, address: str, **kwargs) -> list[dict]:
        """Extrai listagem de proprietarios do Fisgar.

        Com FISGAR_BROWSER_ENABLED=1, delega ao runner agent-browser
        (agentes/fisgar/runner.py batch-json). Sem a flag, retorna []
        (stub, compatibilidade com testes).
        """
        self.logger.info(f"Extraindo listagem Fisgar: {address}")

        if os.environ.get("FISGAR_BROWSER_ENABLED") != "1":
            self.logger.warning("FISGAR_BROWSER_ENABLED != 1 - stub vazio")
            return []

        runner_path = Path(
            os.environ.get("FISGAR_RUNNER_PATH", "agentes/fisgar/runner.py")
        )
        if not runner_path.exists():
            self.logger.error(f"Runner nao encontrado: {runner_path}")
            return []

        max_c = kwargs.get("max_consultas",
            int(os.environ.get("FISGAR_MAX_CONSULTAS", "10")))
        cmd = [
            sys.executable, str(runner_path),
            "--session", os.environ.get("AGENT_BROWSER_SESSION",
                                          "fisgar-runner"),
            "batch-json",
            "--endereco", address,
            "--max-consultas", str(max_c),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=900)
        except subprocess.TimeoutExpired:
            self.logger.error("Runner Fisgar excedeu timeout (900s)")
            return []

        if proc.returncode != 0:
            self.logger.error(
                f"Runner falhou (exit {proc.returncode})")
            return []

        try:
            records = json.loads(proc.stdout)
        except json.JSONDecodeError:
            self.logger.error("Runner nao retornou JSON valido")
            return []

        self.logger.info(f"Runner devolveu {len(records)} registros reais")
        return records
    
    def extract_details(self, record_key: str) -> dict | None:
        """Extrai detalhes de um registro."""
        self.logger.info(f"Extraindo detalhes: {record_key}")
        # TODO: Implementar extracao de detalhes
        return None
    
    def map_to_canonical(self, raw_record: dict) -> CanonicalContact:
        """Mapeia registro bruto do Fisgar para modelo canonico.

        Espelha o EEmovelAgent (etapa 2.4): telefones/emails como lista
        str ou dict, Address estruturado, cpf do modal Fisgar, confidence
        ALTA com contato ou CPF, MEDIA com unidade identificada,
        BAIXA caso contrario.
        """
        phones = []
        tels = raw_record.get("telefones", [])
        if isinstance(tels, str):
            tels = [tels]
        single = raw_record.get("telefone", "")
        if single:
            tels = list(tels) + [single]
        for phone_raw in tels:
            if isinstance(phone_raw, str) and phone_raw.strip():
                phones.append(PhoneValidation(number=phone_raw,
                                              source="fisgar"))
            elif isinstance(phone_raw, dict) and phone_raw.get("numero"):
                phones.append(PhoneValidation(
                    number=phone_raw.get("numero", ""),
                    source="fisgar"
                ))

        emails = []
        mails = raw_record.get("emails", [])
        if isinstance(mails, str):
            mails = [mails]
        single_m = raw_record.get("email", "")
        if single_m:
            mails = list(mails) + [single_m]
        for email_raw in mails:
            if isinstance(email_raw, str) and email_raw.strip():
                emails.append(EmailValidation(email=email_raw,
                                              source="fisgar"))
            elif isinstance(email_raw, dict) and email_raw.get("email"):
                emails.append(EmailValidation(
                    email=email_raw.get("email", ""),
                    source="fisgar"
                ))

        address = Address(
            street=raw_record.get("street"),
            number=raw_record.get("number"),
            city=raw_record.get("city"),
            full=raw_record.get("endereco"),
        )

        cpf = raw_record.get("cpf") or None
        unidade = raw_record.get("unidade")
        if phones or emails or cpf:
            confidence = ConfidenceLevel.ALTA
        elif unidade:
            confidence = ConfidenceLevel.MEDIA
        else:
            confidence = ConfidenceLevel.BAIXA

        contact = CanonicalContact(
            name=raw_record.get("nome", ""),
            source=self.source_key,
            source_id=raw_record.get("id"),
            entity_type=EntityType.PESSOA_FISICA,
            phones=phones,
            emails=emails,
            cpf=cpf,
            address=address,
            confidence=confidence,
            metadata={
                "unidade": unidade,
                "endereco": raw_record.get("endereco"),
                "tipo": raw_record.get("tipo", "proprietario"),
            }
        )

        return contact
