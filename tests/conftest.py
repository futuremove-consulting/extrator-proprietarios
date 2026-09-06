"""Fixtures e configuracao base para testes."""

import shutil
import tempfile
from pathlib import Path

import pytest

from extrator_prop.config import AgentConfig
from extrator_prop.features import FeatureFlags


@pytest.fixture
def temp_dir():
    """Diretorio temporario para testes."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)


@pytest.fixture
def mock_features():
    """Feature flags para testes."""
    return FeatureFlags(
        CAPTEI_ENABLED=True,
        FISGAR_ENABLED=True,
        EEMOVEL_ENABLED=True,
        DONODOZAP_VALIDATION=True,
        WHATSAPP_VALIDATION=False,
        DRY_RUN=True,
        DEBUG_MODE=True,
        RATE_LIMIT_ENABLED=True,
        RETRY_ENABLED=True,
        CIRCUIT_BREAKER_ENABLED=True
    )


@pytest.fixture
def mock_config():
    """Configuracao para testes."""
    return AgentConfig(
        enabled=True,
        base_url="https://test.example.com",
        timeout=30.0,
        max_retries=3,
        rate_limit=60
    )


@pytest.fixture
def sample_raw_record():
    """Registro bruto de exemplo."""
    return {
        "id": "test-123",
        "nome": "Joao Silva",
        "unidade": "AP 101",
        "endereco": "Rua Teste, 100",
        "telefone": "11999999999",
        "email": "joao@email.com"
    }


@pytest.fixture
def sample_pj_record():
    """Registro PJ de exemplo."""
    return {
        "id": "test-456",
        "nome": "Empresa Teste Ltda",
        "unidade": "Sala 201",
        "endereco": "Rua Teste, 200"
    }
