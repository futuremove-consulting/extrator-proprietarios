"""Validador para donodozap.com.br usando agent-browser (Vercel)."""

import asyncio
import time

from .whatsapp_validator import (
    ValidationSource,
    ValidationTier,
    WhatsAppValidationResult,
    WhatsAppValidator,
)


class DonoDoZapBRValidator(WhatsAppValidator):
    """Validador para donodozap.com.br usando agent-browser MCP."""

    @property
    def source(self) -> ValidationSource:
        return ValidationSource.DONODOZAP_BR

    @property
    def base_url(self) -> str:
        return "https://donodozap.com.br"

    def __init__(self, headless: bool = True, timeout_ms: int = 30000):
        super().__init__(headless, timeout_ms)
        self._session = None

    async def _ensure_session(self):
        """Garante sessão agent-browser ativa."""
        if self._session is None:
            self._session = "donodozap_br"
        return self._session

    async def _init_browser(self):
        """No-op: agent-browser gerencia sessão externamente."""
        pass

    async def _close_browser(self):
        """No-op: agent-browser gerencia sessão externamente."""
        pass

    async def validate(self, phone: str) -> WhatsAppValidationResult:
        start_time = time.time()
        digits = self._normalize_phone(phone)
        formatted = self._format_phone(digits)

        try:
            # Abrir página
            await self._agent_browser_open(self.base_url)

            # Preencher input do telefone
            await self._agent_browser_fill_phone(formatted)

            # Clicar consultar
            await self._agent_browser_click_consultar()

            # Aguardar resultado
            await asyncio.sleep(3)

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

    async def _agent_browser_open(self, url: str):
        """Abre URL no agent-browser."""
        from agent_browser import agent_browser_open
        await agent_browser_open(url=url, session=self._session)

    async def _agent_browser_fill_phone(self, formatted: str):
        """Preenche input do telefone."""
        from agent_browser import agent_browser_fill
        # Tentar múltiplos seletores comuns
        selectors = [
            'input[type="tel"]',
            'input[placeholder*="WhatsApp"]',
            'input[placeholder*="número"]',
            'input[placeholder*="telefone"]',
            'input[type="text"]',
            '#telefone',
            '#phone',
            'input[name="phone"]'
        ]
        for selector in selectors:
            try:
                await agent_browser_fill(selector=selector, text=formatted, session=self._session, clear=True)
                return
            except:
                continue
        raise Exception("Input de telefone não encontrado")

    async def _agent_browser_click_consultar(self):
        """Clica botão consultar."""
        from agent_browser import agent_browser_click
        selectors = [
            'button:has-text("Consultar")',
            'button:has-text("Descobrir")',
            'button[type="submit"]',
            'button:has-text("Buscar")',
            'input[type="submit"]',
            '.btn-consultar',
            '#btn-consultar'
        ]
        for selector in selectors:
            try:
                await agent_browser_click(selector=selector, session=self._session)
                return
            except:
                continue
        raise Exception("Botão consultar não encontrado")

    async def _extract_result(self, digits: str, formatted: str) -> WhatsAppValidationResult:
        """Extrai dados da página de resultado via agent-browser eval."""
        from agent_browser import agent_browser_eval

        # Script para extrair dados da página
        script = """
        () => {
            const result = {
                nome_exibicao: null,
                foto_perfil_url: null,
                status_whatsapp: null,
                tier: 'not_found',
                custo_estimado: 0.0,
                page_html: document.body.innerHTML
            };

            // Procurar nome exibido
            const nomeSelectors = [
                '.resultado-nome',
                '[data-testid="nome"]',
                'h2:has-text("Nome")',
                '.nome-exibicao',
                '.nome-resultado',
                '.card-nome',
                '.result-name'
            ];
            for (const sel of nomeSelectors) {
                const elem = document.querySelector(sel);
                if (elem && elem.innerText.trim()) {
                    result.nome_exibicao = elem.innerText.trim();
                    break;
                }
            }

            // Procurar por texto "Nome:" ou similar
            if (!result.nome_exibicao) {
                const allText = document.body.innerText;
                const nomeMatch = allText.match(/Nome[:\\s]+([^\n]+)/i);
                if (nomeMatch) result.nome_exibicao = nomeMatch[1].trim();
            }

            // Procurar foto de perfil
            const imgSelectors = [
                'img[alt*="foto"]',
                'img[alt*="perfil"]',
                '.foto-perfil img',
                '.profile-photo img',
                '.avatar img',
                'img.foto',
                'img.perfil'
            ];
            for (const sel of imgSelectors) {
                const elem = document.querySelector(sel);
                if (elem && elem.src) {
                    result.foto_perfil_url = elem.src;
                    break;
                }
            }

            // Procurar status WhatsApp
            const statusSelectors = [
                '.status-whatsapp',
                '[data-testid="status"]',
                '.whatsapp-status',
                '.status'
            ];
            for (const sel of statusSelectors) {
                const elem = document.querySelector(sel);
                if (elem && elem.innerText.trim()) {
                    result.status_whatsapp = elem.innerText.trim();
                    break;
                }
            }

            // Buscar no texto da página
            if (!result.status_whatsapp) {
                const allText = document.body.innerText;
                const statusMatch = allText.match(/Status[:\\s]+([^\n]+)/i) || allText.match(/WhatsApp[:\\s]+([^\n]+)/i);
                if (statusMatch) result.status_whatsapp = statusMatch[1].trim();
            }

            // Determinar tier
            if (result.foto_perfil_url) {
                result.tier = 'paid';
                result.custo_estimado = 0.50;
            } else if (result.nome_exibicao) {
                result.tier = 'free';
                result.custo_estimado = 0.0;
            } else {
                result.tier = 'not_found';
                result.custo_estimado = 0.0;
            }

            return result;
        }
        """

        try:
            eval_result = await agent_browser_eval(script=script, session=self._session)
            data = eval_result

            # Capturar HTML para debug
            html = data.get("page_html", "")
            if not html:
                from agent_browser import agent_browser_read
                read_result = await agent_browser_read(session=self._session)
                html = read_result

            return WhatsAppValidationResult(
                phone_digits=digits,
                phone_formatted=formatted,
                source=self.source,
                tier=ValidationTier(data.get("tier", "not_found")),
                nome_exibicao=data.get("nome_exibicao"),
                foto_perfil_url=data.get("foto_perfil_url"),
                status_whatsapp=data.get("status_whatsapp"),
                custo_estimado=data.get("custo_estimado", 0.0),
                raw_response={"html_length": len(html), "page_url": self.base_url}
            )

        except Exception as e:
            # Fallback: tentar ler página
            try:
                from agent_browser import agent_browser_read
                html = await agent_browser_read(session=self._session)
                return WhatsAppValidationResult(
                    phone_digits=digits,
                    phone_formatted=formatted,
                    source=self.source,
                    tier=ValidationTier.NOT_FOUND,
                    erro=f"Extract failed: {e}",
                    raw_response={"html_length": len(html) if html else 0}
                )
            except:
                return WhatsAppValidationResult(
                    phone_digits=digits,
                    phone_formatted=formatted,
                    source=self.source,
                    tier=ValidationTier.FAILED,
                    erro=f"Extract failed: {e}"
                )

    async def validate_batch(self, phones: list[str]) -> list[WhatsAppValidationResult]:
        results = []
        for phone in phones:
            result = await self.validate(phone)
            results.append(result)
            await asyncio.sleep(2)  # Delay para não ser bloqueado
        return results

    async def close(self):
        """Fecha sessão (agent-browser gerencia ciclo de vida)."""
        self._session = None