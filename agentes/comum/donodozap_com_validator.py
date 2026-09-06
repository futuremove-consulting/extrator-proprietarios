"""Validador para donodozap.com usando agent-browser (Vercel)."""

import time

from .whatsapp_validator import (
    ValidationSource,
    ValidationTier,
    WhatsAppValidationResult,
    WhatsAppValidator,
)


class DonoDoZapComValidator(WhatsAppValidator):
    """Validador para donodozap.com via agent-browser."""

    @property
    def source(self) -> ValidationSource:
        return ValidationSource.DONODOZAP_COM

    @property
    def base_url(self) -> str:
        return "https://donodozap.com"

    async def validate(self, phone: str) -> WhatsAppValidationResult:
        start_time = time.time()
        digits = self._normalize_phone(phone)
        formatted = self._format_phone(digits)

        try:
            # Open page via agent-browser
            await agent_browser_agent_browser_open(url=self.base_url, session="donodozap_com")
            
            # Wait for input and fill
            await agent_browser_agent_browser_wait_for_selector(
                selector='input[type="tel"], input[placeholder*="WhatsApp"], input[placeholder*="número"], input[type="text"]',
                session="donodozap_com",
                waitTimeoutMs=10000
            )
            await agent_browser_agent_browser_fill(
                selector='input[type="tel"], input[placeholder*="WhatsApp"], input[placeholder*="número"], input[type="text"]',
                text=formatted,
                session="donodozap_com"
            )

            # Click consultar/descobrir
            await agent_browser_agent_browser_click(
                selector='button:has-text("Consultar"), button:has-text("Descobrir"), button[type="submit"]',
                session="donodozap_com"
            )

            # Wait for result
            await agent_browser_agent_browser_wait_for_text(
                text="Nome",
                session="donodozap_com",
                waitTimeoutMs=15000
            )

            # Extract result
            result = await self._extract_result_via_browser(digits, formatted)
            result.tempo_resposta_ms = int((time.time() - start_time) * 1000)
            return result

        except Exception as e:
            return WhatsAppValidationResult(
                phone_digits=digits,
                phone_formatted=formatted,
                source=self.source,
                tier=ValidationTier.FAILED,
                erro=str(e),
                tempo_resposta_ms=int((time.time() - start_time) * 1000)
            )

    async def _extract_result_via_browser(self, digits: str, formatted: str) -> WhatsAppValidationResult:
        snapshot = await agent_browser_agent_browser_snapshot(session="donodozap_com")
        page_text = str(snapshot)
        
        tier = ValidationTier.NOT_FOUND
        nome_exibicao = None
        foto_url = None
        
        if "nome" in page_text.lower() and len(page_text) > 500:
            tier = ValidationTier.FREE
        
        if "foto" in page_text.lower() or "img" in page_text.lower():
            tier = ValidationTier.PAID

        return WhatsAppValidationResult(
            phone_digits=digits,
            phone_formatted=formatted,
            source=self.source,
            tier=tier,
            nome_exibicao=nome_exibicao,
            foto_perfil_url=foto_url,
            custo_estimado=0.50 if tier == ValidationTier.PAID else 0.0,
            raw_response={"page_text_length": len(page_text)}
        )

    async def validate_batch(self, phones: list[str]) -> list[WhatsAppValidationResult]:
        results = []
        for phone in phones:
            result = await self.validate(phone)
            results.append(result)
            await asyncio.sleep(2)
        return results