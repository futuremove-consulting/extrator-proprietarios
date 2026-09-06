"""Serviço unificado de validação WhatsApp - orquestra múltiplos validadores."""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .whatsapp_validator import (
    WhatsAppValidator,
    WhatsAppValidationResult,
    ValidationSource,
    ValidationTier
)
from .donodozap_br_validator import DonoDoZapBRValidator
from .donodozap_com_validator import DonoDoZapComValidator
from .process_logger import ProcessLearningLogger


@dataclass
class ValidationPolicy:
    """Política de validação para um número."""
    phone: str
    sources_to_try: List[ValidationSource] = field(default_factory=list)
    require_paid_tier: bool = False
    stop_on_first_valid: bool = True
    max_cost_per_phone: float = 1.00


class WhatsAppValidationService:
    """Serviço unificado que gerencia múltiplos validadores de WhatsApp."""

    def __init__(
        self,
        logger: Optional[ProcessLearningLogger] = None,
        headless: bool = True,
        validators_config: Optional[Dict[str, Any]] = None
    ):
        self.logger = logger
        self.headless = headless
        self.validators_config = validators_config or {}

        # Inicializar validadores
        self.validators: Dict[ValidationSource, WhatsAppValidator] = {}
        self._init_validators()

        # Cache de resultados para evitar consultas duplicadas
        self._cache: Dict[str, WhatsAppValidationResult] = {}

        # Estatísticas
        self.stats = {
            "total_validations": 0,
            "by_source": {},
            "by_tier": {},
            "total_cost": 0.0,
            "cache_hits": 0
        }

    def _init_validators(self):
        """Inicializa validadores disponíveis."""
        # donodozap.com.br
        self.validators[ValidationSource.DONODOZAP_BR] = DonoDoZapBRValidator(
            headless=self.headless,
            timeout_ms=self.validators_config.get("timeout_ms", 30000)
        )

        # donodozap.com
        self.validators[ValidationSource.DONODOZAP_COM] = DonoDoZapComValidator(
            headless=self.headless,
            timeout_ms=self.validators_config.get("timeout_ms", 30000)
        )

    def _get_validator(self, source: ValidationSource) -> Optional[WhatsAppValidator]:
        return self.validators.get(source)

    async def validate_phone(
        self,
        phone: str,
        policy: Optional[ValidationPolicy] = None
    ) -> WhatsAppValidationResult:
        """Valida um único número seguindo a política definida."""
        digits = self._normalize_phone(phone)

        # Verificar cache
        if digits in self._cache:
            self.stats["cache_hits"] += 1
            return self._cache[digits]

        # Política padrão: tentar ambos donodozap, depois Captei (se disponível)
        if policy is None:
            policy = ValidationPolicy(
                phone=phone,
                sources_to_try=[
                    ValidationSource.DONODOZAP_BR,
                    ValidationSource.DONODOZAP_COM
                ],
                stop_on_first_valid=True,
                max_cost_per_phone=1.00
            )

        best_result = None
        total_cost = 0.0

        for source in policy.sources_to_try:
            if total_cost >= policy.max_cost_per_phone:
                break

            validator = self._get_validator(source)
            if not validator:
                continue

            try:
                if self.logger:
                    with self.logger.action(
                        "validate_whatsapp", source.value, "whatsapp_validation",
                        {"phone": phone}
                    ) as action:
                        result = await validator.validate(phone)
                        action.add_output("tier", result.tier.value)
                        action.add_output("nome", result.nome_exibicao)
                        action.add_cost(queries=1, cost=result.custo_estimado)
                else:
                    result = await validator.validate(phone)

                total_cost += result.custo_estimado

                # Atualizar estatísticas
                self._update_stats(source, result)

                # Se tem resultado válido e stop_on_first_valid
                if result.is_valid() and policy.stop_on_first_valid:
                    best_result = result
                    break

                # Se tier PAID e require_paid_tier, usar esse
                if policy.require_paid_tier and result.has_paid_data():
                    best_result = result
                    break

                # Manter melhor resultado até agora
                if best_result is None or self._is_better_result(result, best_result):
                    best_result = result

            except Exception as e:
                if self.logger:
                    self.logger.log_decision(
                        stage="whatsapp_validation",
                        decision=f"validator_error_{source.value}",
                        rationale=f"Erro ao validar {phone} com {source.value}: {str(e)}",
                        data={"phone": phone, "source": source.value, "error": str(e)}
                    )

        if best_result is None:
            best_result = WhatsAppValidationResult(
                phone_digits=digits,
                phone_formatted=self._format_phone(digits),
                source=ValidationSource.MANUAL,
                tier=ValidationTier.FAILED,
                erro="Nenhum validador retornou resultado válido"
            )

        # Cachear resultado
        self._cache[digits] = best_result

        return best_result

    async def validate_batch(
        self,
        phones: List[str],
        policy: Optional[ValidationPolicy] = None,
        max_concurrent: int = 1
    ) -> List[WhatsAppValidationResult]:
        """Valida múltiplos números."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def validate_one(phone: str) -> WhatsAppValidationResult:
            async with semaphore:
                return await self.validate_phone(phone, policy)

        tasks = [validate_one(phone) for phone in phones]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def validate_owner_phones(
        self,
        owner_data: Dict[str, Any],
        policy: Optional[ValidationPolicy] = None
    ) -> Dict[str, Any]:
        """
        Valida todos os telefones de um proprietário.
        owner_data deve conter: telefones (lista), nome, etc.
        """
        telefones = owner_data.get("telefones", [])
        if not telefones:
            return {"validated": [], "best_match": None}

        # Extrair apenas números
        phone_numbers = []
        for tel in telefones:
            if isinstance(tel, dict):
                num = tel.get("numero_raw") or tel.get("numero") or tel.get("digitos")
            else:
                num = tel
            if num:
                phone_numbers.append(num)

        if not phone_numbers:
            return {"validated": [], "best_match": None}

        # Validar todos
        results = await self.validate_batch(phone_numbers, policy)

        # Consolidar resultados
        validated = []
        best_match = None

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                result = WhatsAppValidationResult(
                    phone_digits=self._normalize_phone(phone_numbers[i]),
                    phone_formatted=phone_numbers[i],
                    source=ValidationSource.MANUAL,
                    tier=ValidationTier.FAILED,
                    erro=str(result)
                )

            validated.append({
                "original_phone": phone_numbers[i],
                "result": result.to_dict()
            })

            # Melhor match: primeiro válido com nome
            if best_match is None and result.is_valid():
                best_match = result.to_dict()

        return {
            "validated": validated,
            "best_match": best_match,
            "total_cost": sum(r.get("custo_estimado", 0) for r in validated if isinstance(r, dict)),
            "sources_used": list(set(r.get("source") for r in validated if isinstance(r, dict)))
        }

    def _is_better_result(self, new: WhatsAppValidationResult, current: WhatsAppValidationResult) -> bool:
        """Determina se novo resultado é melhor que o atual."""
        # Prioridade: PAID > FREE > NOT_FOUND > FAILED
        tier_priority = {
            ValidationTier.PAID: 4,
            ValidationTier.FREE: 3,
            ValidationTier.NOT_FOUND: 2,
            ValidationTier.FAILED: 1
        }

        new_priority = tier_priority.get(new.tier, 0)
        current_priority = tier_priority.get(current.tier, 0)

        if new_priority != current_priority:
            return new_priority > current_priority

        # Mesmo tier: preferir com nome
        if new.nome_exibicao and not current.nome_exibicao:
            return True

        return False

    def _update_stats(self, source: ValidationSource, result: WhatsAppValidationResult):
        self.stats["total_validations"] += 1
        self.stats["total_cost"] += result.custo_estimado

        src_key = source.value
        if src_key not in self.stats["by_source"]:
            self.stats["by_source"][src_key] = {"count": 0, "cost": 0.0, "valid": 0}
        self.stats["by_source"][src_key]["count"] += 1
        self.stats["by_source"][src_key]["cost"] += result.custo_estimado
        if result.is_valid():
            self.stats["by_source"][src_key]["valid"] += 1

        tier_key = result.tier.value
        self.stats["by_tier"][tier_key] = self.stats["by_tier"].get(tier_key, 0) + 1

    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()

    def get_cache_size(self) -> int:
        return len(self._cache)

    def clear_cache(self):
        self._cache.clear()

    def _normalize_phone(self, phone: str) -> str:
        digits = re.sub(r'\D', '', phone)
        if not digits.startswith('55') and len(digits) >= 10:
            digits = '55' + digits
        return digits

    def _format_phone(self, digits: str) -> str:
        if len(digits) == 13 and digits.startswith('55'):
            return f"({digits[2:4]}) {digits[4:9]}-{digits[9:]}"
        elif len(digits) == 12 and digits.startswith('55'):
            return f"({digits[2:4]}) {digits[4:8]}-{digits[8:]}"
        elif len(digits) == 11:
            return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
        elif len(digits) == 10:
            return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
        return digits


# Importar re para funções estáticas
import re


async def create_validation_service(
    logger: Optional[ProcessLearningLogger] = None,
    headless: bool = True
) -> WhatsAppValidationService:
    """Factory para criar serviço de validação inicializado."""
    service = WhatsAppValidationService(logger=logger, headless=headless)
    return service