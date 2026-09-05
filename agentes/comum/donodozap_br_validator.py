"""Validador para donodozap.com.br usando Playwright."""

import asyncio
import time
import re
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page

from .whatsapp_validator import (
    WhatsAppValidator,
    WhatsAppValidationResult,
    ValidationSource,
    ValidationTier
)


class DonoDoZapBRValidator(WhatsAppValidator):
    """Validador para donodozap.com.br"""

    @property
    def source(self) -> ValidationSource:
        return ValidationSource.DONODOZAP_BR

    @property
    def base_url(self) -> str:
        return "https://donodozap.com.br"

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

            # Encontrar input do telefone
            phone_input = await self._page.wait_for_selector(
                'input[type="tel"], input[placeholder*="WhatsApp"], input[placeholder*="número"], input[type="text"]',
                timeout=self.timeout_ms
            )

            # Limpar e preencher
            await phone_input.fill("")
            await phone_input.type(formatted, delay=50)

            # Clicar botão consultar
            consultar_btn = await self._page.wait_for_selector(
                'button:has-text("Consultar"), button:has-text("Descobrir"), button[type="submit"]',
                timeout=self.timeout_ms
            )
            await consultar_btn.click()

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
        """Extrai dados da página de resultado."""

        # Verificar se há nome exibido (tier FREE)
        nome_selectors = [
            '.resultado-nome',
            '[data-testid="nome"]',
            'h2:has-text("Nome")',
            '.nome-exibicao',
            'text=/Nome.*:/'
        ]

        nome_exibicao = None
        for selector in nome_selectors:
            try:
                elem = await self._page.query_selector(selector)
                if elem:
                    nome_exibicao = await elem.inner_text()
                    if nome_exibicao:
                        nome_exibicao = nome_exibicao.strip()
                        break
            except:
                continue

        # Verificar se há foto de perfil (tier PAID)
        foto_url = None
        try:
            img_elem = await self._page.query_selector('img[alt*="foto"], img[alt*="perfil"], .foto-perfil img')
            if img_elem:
                foto_url = await img_elem.get_attribute('src')
        except:
            pass

        # Verificar status WhatsApp
        status_selectors = [
            '.status-whatsapp',
            '[data-testid="status"]',
            'text=/Status.*:/',
            'text=/WhatsApp.*:/'
        ]

        status_whatsapp = None
        for selector in status_selectors:
            try:
                elem = await self._page.query_selector(selector)
                if elem:
                    status_whatsapp = (await elem.inner_text()).strip()
                    break
            except:
                continue

        # Determinar tier
        if foto_url:
            tier = ValidationTier.PAID
            custo = 0.50  # Estimativa baseada em PIX
        elif nome_exibicao:
            tier = ValidationTier.FREE
            custo = 0.0
        else:
            tier = ValidationTier.NOT_FOUND
            custo = 0.0

        # Capturar HTML raw para debug
        html = await self._page.content()

        return WhatsAppValidationResult(
            phone_digits=digits,
            phone_formatted=formatted,
            source=self.source,
            tier=tier,
            nome_exibicao=nome_exibicao,
            foto_perfil_url=foto_url,
            status_whatsapp=status_whatsapp,
            custo_estimado=custo,
            raw_response={"html_length": len(html), "page_url": self._page.url}
        )

    async def validate_batch(self, phones: List[str]) -> List[WhatsAppValidationResult]:
        results = []
        for phone in phones:
            result = await self.validate(phone)
            results.append(result)
            # Delay entre consultas para não ser bloqueado
            await asyncio.sleep(2)
        return results