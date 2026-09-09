"""Wrapper subprocess da CLI agent-browser (sessao nomeada persistente).

Extraido do runner EEmovel (Fluxo 1) para reuso pelos runners Fisgar
(Fluxo 2) e Captei (Fluxo 3) - etapa 2.1 do PLANO_FLUXOS_EXTRACAO.
"""

from __future__ import annotations

import os
import subprocess


class AgentBrowser:
    """Wrapper subprocess da CLI agent-browser (sessão nomeada persistente)."""

    def __init__(self, session: str | None = None, timeout: int = 60):
        self.session = session or os.environ.get("AGENT_BROWSER_SESSION", "extrator-runner")
        self.timeout = timeout
        self._bin = os.environ.get("AGENT_BROWSER_BIN", "agent-browser")

    def run(self, *args: str, timeout: int | None = None) -> str:
        cmd = [self._bin, "--session", self.session, *args]
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout or self.timeout,
            env={**os.environ, "PATH": os.environ.get("AB_PATH_OVERRIDE", os.environ["PATH"])},
        )
        if proc.returncode != 0:
            raise RuntimeError(f"agent-browser {' '.join(args[:2])} falhou (exit {proc.returncode}): {proc.stderr.strip()[:300]}")
        return proc.stdout
