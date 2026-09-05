"""Validador para donodozap.com usando Playwright."""

import asyncio
import time
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page

from .whatsapp_validator import (
    WhatsAppValidator,
    WhatsAppValidationResult,
    ValidationSource,
    ValidationTier
)


class DonoDoZapComValidator(WhatsAppValidator):
    """Validador para donodozap.com"""

    @property
    def source(self) -> ValidationSource:
        return ValidationSource.DONODOZAP_COM

    @property
    def base_url(self) -> str:
        return "https://donodozap.com"

    async def _init_browser(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._page = await self._browser.new_page()
        await self._page.goto(self.base_url, wait_until="networkidle")

    async def _close_browser(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def validate(self, phone: str) -> WhatsAppValidationResult:
        start_time = time.time()
        digits = self._normalize_phone(phone)
        formatted = self._format_phone(digits)

        try:
            await self._page.goto(self.base_url, wait_until="networkidle")

            # donodozap.com tem seletor de país + input
            # Encontrar input do telefone
            phone_input = await self._page.wait_for_selector(
                'input[type="tel"], input[name="phone"], input[placeholder*="número"], input[placeholder*="numero"], input[type="text"]',
                timeout=self.timeout_ms
            )

            # Limpar e preencher
            await phone_input.fill("")
            await phone_input.type(formatted, delay=50)

            # Clicar botão descobrir
            descobrir_btn = await self._page.wait_for_selector(
                'button:has-text("Descobrir"), button[type="submit"], button:has-text("Consultar")',
                timeout=self.timeout_ms
            )
            await descobrir_btn.click()

            # Aguardar resultado
            await self._page.wait_for_timeout(3000)

            # Extrair resultado
            result = await self._extract_result(digits, formatted)

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

    async def _extract_result(self, digits: str, formatted: str) -> WhatsAppValidationResult:
        """Extrai dados da página de resultado do donodozap.com"""

        # Verificar se há nome exibido (tier FREE)
        nome_exibicao = None
        nome_selectors = [
            '.result-name',
            '[data-testid="result-name"]',
            'h2:has-text("Nome")',
            '.nome-resultado',
            'text=/Nome.*:/',
            '.card-title'
        ]

        for selector in nome_selectors:
            try:
                elem = await self._page.query_selector(selector)
                if elem:
                    text = (await elem.inner_text()).strip()
                    if text and len(text) > 2:
                        nome_exibicao = text
                        break
            except:
                continue

        # Verificar foto de perfil (tier PAID)
        foto_url = None
        try:
            img_elem = await self._page.query_selector('img[alt*="foto"], img[alt*="perfil"], .profile-photo img, .avatar img')
            if img_elem:
                foto_url = await img_elem.get_attribute('src')
        except:
            pass

        # Verificar se há botão de desbloqueio (indica tier PAID disponível)
        has_paid_unlock = False
        try:
            unlock_btn = await self._page.query_selector('button:has-text("Desbloquear"), button:has-text("PIX"), button:has-text("Pagar")')
            if unlock_btn:
                has_paid_unlock = True
        except:
            pass

        # Determinar tier
        if foto_url or has_paid_unlock:
            tier = ValidationTier.PAID
            custo = 0.50
        elif nome_exibicao:
            tier = ValidationTier.FREE
            custo = 0.0
        else:
            tier = ValidationTier.NOT_FOUND
            custo = 0.0

        html = await self._page.content()

        return WhatsAppValidationResult(
            phone_digits=digits,
            phone_formatted=formatted,
            source=self.source,
            tier=tier,
            nome_exibicao=nome_exibicao,
            foto_perfil_url=foto_url,
            custo_estimado=custo,
            raw_response={"html_length": len(html), "page_url": self._page.url, "has_paid_unlock": has_paid_unlock}
        )

    async def validate_batch(self, phones: List[str]) -> List[WhatsAppValidationResult]:
        results = []
        for phone in phones:
            result = await self.validate(phone)
            results.append(result)
            await asyncio.sleep(2)
        return results