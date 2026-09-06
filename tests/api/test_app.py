"""Testes da API HTTP do extrator."""
import pytest

from extrator_prop.api.app import create_app
from extrator_prop.config import Config
from extrator_prop.features import FeatureFlags


@pytest.fixture
def client():
    cfg = Config()
    for c in (cfg.captei, cfg.eemovel, cfg.fisgar):
        c.enabled = True
    cfg.features = FeatureFlags()
    app = create_app(config=cfg)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_healthz_wrong_method(client):
    r = client.delete("/healthz")
    assert r.status_code == 405


def test_extract_missing_address(client):
    r = client.post("/api/v1/extract", json={})
    assert r.status_code == 400
    assert "address" in r.get_json()["error"]


def test_extract_validation_error_address_vazio(client):
    r = client.post("/api/v1/extract", json={"address": "   "})
    assert r.status_code == 400


def test_extract_success(monkeypatch, client):
    """Pipeline real: listing -> is_pessoa_fisica -> map_to_canonical."""
    raw = [
        {"name": "João Silva", "advertiser_name": "João Silva", "id": "1"},
        {"name": "Imobiliária Ltda", "id": "2"},
    ]

    def fake_listing(self, address, **kw):
        return raw

    monkeypatch.setattr("extrator_prop.agents.captei.CapteiAgent.extract_listing", fake_listing)

    r = client.post("/api/v1/extract", json={"address": "Rua Teste"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["stats"]["total"] == 2
    assert body["stats"]["completed"] == 1
    assert body["stats"]["excluded"] == 1
    assert body["stats"]["errors"] == 0
    assert len(body["resultados"]) == 1
    res = body["resultados"][0]
    assert res["name"] == "João Silva"
    assert res["source"] == "captei"
    assert res["source_id"] == "1"
    # ponte PilotCRM: items no shape ExtractedOwner (ver adapter.py)
    assert "items" in body
    item = body["items"][0]
    assert item["fullName"] == "João Silva"
    assert item["source"] == "captei"
    assert item["classification"] in {"proprietario", "possivel_morador", "empresa", "indefinido"}


def test_extract_all_agents_disabled(client):
    """Flags desativadas -> resultset vazio sem erro."""
    client.application.config["EXTRATOR_CONFIG"].features.CAPTEI_ENABLED = False
    client.application.config["EXTRATOR_CONFIG"].features.EEMOVEL_ENABLED = False
    client.application.config["EXTRATOR_CONFIG"].features.FISGAR_ENABLED = False
    r = client.post("/api/v1/extract", json={"address": "Rua Teste"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["resultados"] == []
    assert body["stats"]["total"] == 0
