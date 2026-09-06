"""Testes para retry.py."""

from unittest.mock import MagicMock

import pytest

from extrator_prop.core.retry import RetryConfig, RetryHandler, with_retry


class TestRetryConfig:
    """Testes para RetryConfig."""
    
    def test_default_values(self):
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.backoff_factor == 2.0
        assert config.jitter is True
    
    def test_calculate_delay_no_jitter(self):
        config = RetryConfig(jitter=False, initial_delay=1.0, backoff_factor=2.0)
        
        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0
    
    def test_calculate_delay_with_max(self):
        config = RetryConfig(jitter=False, initial_delay=1.0, backoff_factor=10.0, max_backoff=50.0)
        
        assert config.calculate_delay(10) == 50.0  # Max backoff


class TestRetryHandler:
    """Testes para RetryHandler."""
    
    def test_success_first_try(self):
        handler = RetryHandler()
        mock_func = MagicMock(return_value="success")
        
        result = handler.execute(mock_func)
        
        assert result == "success"
        assert handler.attempts == 1
    
    def test_success_after_retries(self):
        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        handler = RetryHandler(config)
        mock_func = MagicMock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        result = handler.execute(mock_func)
        
        assert result == "success"
        assert handler.attempts == 3
    
    def test_all_attempts_fail(self):
        config = RetryConfig(max_attempts=2, initial_delay=0.01)
        handler = RetryHandler(config)
        mock_func = MagicMock(side_effect=Exception("always fails"))
        
        with pytest.raises(Exception, match="always fails"):
            handler.execute(mock_func)
        
        assert handler.attempts == 2


class TestWithRetryDecorator:
    """Testes para decorator with_retry."""
    
    def test_decorator_success(self):
        call_count = 0
        
        @with_retry(RetryConfig(max_attempts=3, initial_delay=0.01))
        def my_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        assert my_func() == "success"
        assert call_count == 1
    
    def test_decorator_retry_then_success(self):
        call_count = 0
        
        @with_retry(RetryConfig(max_attempts=3, initial_delay=0.01))
        def my_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("fail")
            return "success"
        
        assert my_func() == "success"
        assert call_count == 3
