"""Fixtures e configuracao base para testes."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from extrator_prop.features import FeatureFlags
from extrator_prop.config import Config, AgentConfig
from extrator_prop.constants import RATE_LIMITS


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
    return Config(
        captei=AgentConfig(enabled=True, base_url="https://test.captei.com.br", rate_limit=60),
        fisgar=AgentConfig(enabled=True, base_url="https://test.fisgar.com.br", rate_limit=30),
        eemovel=AgentConfig(enabled=True, base_url="https://test.eemovel.com.br", rate_limit=30),
        log_level="DEBUG",
        log_format="text"
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
