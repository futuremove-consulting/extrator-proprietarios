"""Testes para features.py."""

from extrator_prop.features import FeatureFlags


class TestFeatureFlags:
    """Testes para FeatureFlags."""
    
    def test_default_values(self):
        """Testa valores padrao."""
        features = FeatureFlags()
        
        assert features.CAPTEI_ENABLED is True
        assert features.FISGAR_ENABLED is True
        assert features.EEMOVEL_ENABLED is True
        assert features.DONODOZAP_VALIDATION is True
        assert features.WHATSAPP_VALIDATION is False
        assert features.DRY_RUN is False
        assert features.DEBUG_MODE is False
    
    def test_from_env_all_true(self, monkeypatch):
        """Testa carga de env com todos true."""
        monkeypatch.setenv("FP_CAPTEI_ENABLED", "true")
        monkeypatch.setenv("FP_FISGAR_ENABLED", "1")
        monkeypatch.setenv("FP_EEMOVEL_ENABLED", "yes")
        monkeypatch.setenv("FP_DONODOZAP", "on")
        
        features = FeatureFlags.from_env()
        
        assert features.CAPTEI_ENABLED is True
        assert features.FISGAR_ENABLED is True
        assert features.EEMOVEL_ENABLED is True
        assert features.DONODOZAP_VALIDATION is True
    
    def test_from_env_all_false(self, monkeypatch):
        """Testa carga de env com todos false."""
        monkeypatch.setenv("FP_CAPTEI_ENABLED", "false")
        monkeypatch.setenv("FP_FISGAR_ENABLED", "0")
        monkeypatch.setenv("FP_EEMOVEL_ENABLED", "no")
        
        features = FeatureFlags.from_env()
        
        assert features.CAPTEI_ENABLED is False
        assert features.FISGAR_ENABLED is False
        assert features.EEMOVEL_ENABLED is False
    
    def test_to_dict(self):
        """Testa conversao para dict."""
        features = FeatureFlags(CAPTEI_ENABLED=True, FISGAR_ENABLED=False)
        result = features.to_dict()
        
        assert isinstance(result, dict)
        assert result["CAPTEI_ENABLED"] is True
        assert result["FISGAR_ENABLED"] is False
    
    def test_dry_run_flag(self, mock_features):
        """Testa flag de dry run."""
        assert mock_features.DRY_RUN is True
    
    def test_rate_limit_flag(self, mock_features):
        """Testa flag de rate limit."""
        assert mock_features.RATE_LIMIT_ENABLED is True
