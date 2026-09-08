"""Relatório de créditos — governança transversal (plano seção 8).

Toda execução `live` produz `relatorio_creditos.json` no diretório de logs
do lote: saldo antes/depois (quando informado pelo operador), ações que
consomem crédito, custo verificado e aprovador.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class RelatorioCreditos:
    """Acumula ações que consomem crédito e persiste o relatório da execução."""

    def __init__(self, sistema: str, endereco: str, operador: str | None = None,
                 aprovacao: dict[str, Any] | None = None):
        self.sistema = sistema
        self.endereco = endereco
        self.operador = operador or os.environ.get("EXTRATOR_OPERADOR", "desconhecido")
        self.aprovacao = aprovacao
        self.saldo_antes: str | None = None
        self.saldo_depois: str | None = None
        self.acoes: list[dict[str, Any]] = []

    # --- ações ---
    def registrar(self, evento: str, custo: float | None, detalhe: str = "") -> None:
        self.acoes.append({
            "evento": evento,
            "custo": custo,
            "detalhe": detalhe,
            "timestamp": _agora(),
        })

    def listagem(self, detalhe: str = "") -> None:
        self.registrar("busca_listagem", 1, detalhe)

    def detalhe(self, registro: str) -> None:
        self.registrar("consulta_detalhe", 1, registro)

    def saldo(self, antes: str | None, depois: str | None) -> None:
        self.saldo_antes, self.saldo_depois = antes, depois

    # --- totais ---
    @property
    def total_acoes_pagas(self) -> int:
        return sum(1 for a in self.acoes if a["custo"])

    @property
    def custo_total(self) -> float:
        return sum(a["custo"] or 0 for a in self.acoes)

    # --- persistência ---
    def salvar(self, logs_dir: Path) -> Path:
        caminho = logs_dir / "relatorio_creditos.json"
        dados = {
            "sistema": self.sistema,
            "endereco": self.endereco,
            "operador": self.operador,
            "aprovacao": self.aprovacao,
            "saldo_antes": self.saldo_antes,
            "saldo_depois": self.saldo_depois,
            "total_acoes_pagas": self.total_acoes_pagas,
            "custo_total": self.custo_total,
            "acoes": self.acoes,
        }
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return caminho

    def resumo(self) -> str:
        return (f"creditos: {self.total_acoes_pagas} acao(oes) paga(s), "
                f"custo total {self.custo_total:g}")


def _agora() -> str:
    from datetime import datetime
    return datetime.now().isoformat(timespec="seconds")
