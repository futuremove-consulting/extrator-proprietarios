"""Testes para agents/base.py."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from extrator_prop.agents.base import AgentBase, ExtractionStats
from extrator_prop.config import AgentConfig
from extrator_prop.features import FeatureFlags
from extrator_prop.types import CanonicalContact, EntityType, PhoneValidation


class ConcreteAgent(AgentBase):
    """Agente concreto para testes."""
    
    @property
    def agent_name(self) -> str:
        return "test_agent"
    
    @property
    def source_key(self) -> str:
        return "test"
    
    def extract_listing(self, address: str, **kwargs):
        return [
            {"id": "1", "nome": "Joao Silva", "telefone": "11999999999"},
            {"id": "2", "nome": "Empresa XYZ Ltda", "telefone": ""}
        ]
    
    def extract_details(self, record_key: str):
        return {"email": "test@email.com"}
    
    def map_to_canonical(self, raw_record):
        phones = []
        if raw_record.get("telefone"):
            phones.append(PhoneValidation(number=raw_record["telefone"], source="test"))
        
        return CanonicalContact(
            name=raw_record.get("nome", ""),
            source="test",
            source_id=raw_record.get("id"),
            phones=phones
        )


class TestExtractionStats:
    """Testes para ExtractionStats."""
    
    def test_default_values(self):
        stats = ExtractionStats()
        assert stats.total == 0
        assert stats.completed == 0
        assert stats.errors == 0
    
    def test_duration(self):
        import time
        stats = ExtractionStats()
        stats.start_time = time.time()
        time.sleep(0.01)
        stats.end_time = time.time()
        
        assert stats.duration_seconds is not None
        assert stats.duration_seconds > 0
    
    def test_to_dict(self):
        stats = ExtractionStats(total=10, completed=8, errors=2)
        data = stats.to_dict()
        
        assert data["total"] == 10
        assert data["completed"] == 8
        assert data["errors"] == 2


class TestAgentBase:
    """Testes para AgentBase."""
    
    def test_initialization(self, temp_dir, mock_features, mock_config):
        agent = ConcreteAgent(mock_config, mock_features, "test_lot", temp_dir)
        
        assert agent.lot_name == "test_lot"
        assert agent.agent_name == "test_agent"
        assert agent.source_key == "test"
    
    def test_validate_entity_pf(self, mock_features, mock_config, temp_dir):
        agent = ConcreteAgent(mock_config, mock_features, "test", temp_dir)
        
        record = {"nome": "Joao Silva"}
        assert agent.validate_entity(record) == EntityType.PESSOA_FISICA
    
    def test_validate_entity_pj(self, mock_features, mock_config, temp_dir):
        agent = ConcreteAgent(mock_config, mock_features, "test", temp_dir)
        
        record = {"nome": "Empresa Teste Ltda"}
        assert agent.validate_entity(record) == EntityType.PESSOA_JURIDICA
    
    def test_is_pessoa_fisica(self, mock_features, mock_config, temp_dir):
        agent = ConcreteAgent(mock_config, mock_features, "test", temp_dir)
        
        assert agent.is_pessoa_fisica({"nome": "Joao"}) is True
        assert agent.is_pessoa_fisica({"nome": "Empresa Ltda"}) is False
    
    def test_run_extraction(self, temp_dir, mock_features, mock_config):
        mock_config.rate_limit = 1000  # Alto para nao limitar
        agent = ConcreteAgent(mock_config, mock_features, "test_run", temp_dir)
        
        stats = agent.run("Rua Teste, 100")
        
        assert stats.total == 2
        assert stats.completed == 1  # Joao Silva
        assert stats.excluded == 1  # Empresa Ltda
    
    def test_checkpoint_persistence(self, temp_dir, mock_features, mock_config):
        agent = ConcreteAgent(mock_config, mock_features, "test_checkpoint", temp_dir)
        
        agent._checkpoint = {"last_id": "123"}
        agent.save_checkpoint()
        
        # Recarrega
        agent2 = ConcreteAgent(mock_config, mock_features, "test_checkpoint", temp_dir)
        checkpoint = agent2.load_checkpoint()
        
        assert checkpoint.get("last_id") == "123"
