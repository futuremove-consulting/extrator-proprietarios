"""App HTTP do extrator (Flask)."""
from __future__ import annotations

import time

from flask import Flask, jsonify, request

from extrator_prop.config import Config
from extrator_prop.exceptions import ExtratorError
from extrator_prop.logging import get_logger
from extrator_prop.service.extractor_service import ExtractorService

logger = get_logger("api")


def create_app(config: Config | None = None) -> Flask:
    """App factory — injeta Config (test-friendly)."""
    app = Flask(__name__)
    app.config["EXTRATOR_CONFIG"] = config or Config()
    app.config["JSON_SORT_KEYS"] = False

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok", "timestamp": time.time()}), 200

    @app.post("/api/v1/extract")
    def extract():
        payload = request.get_json(silent=True) or {}
        address = payload.get("address") or payload.get("query") or ""
        tipo_documento = payload.get("tipo_documento") or "proprietario"
        if not address.strip():
            return jsonify({"error": "payload deve conter 'address' (ou 'query')"}), 400

        service = ExtractorService(config=app.config["EXTRATOR_CONFIG"])
        try:
            out = service.list_owners(address, tipo_documento)
        except ExtratorError as exc:
            logger.error("extract failed", extra={"address": address, "error": str(exc)})
            return jsonify({"error": "extracao falhou", "detail": str(exc),
                            "details": getattr(exc, "details", None) or {}}), 502
        return jsonify({
            "address": address,
            "tipo_documento": out.tipo_documento,
            "resultados": out.results,
            "stats": out.stats.to_dict(),
        }), 200

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "endpoint nao encontrado"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return jsonify({"error": "metodo nao permitido"}), 405

    return app
