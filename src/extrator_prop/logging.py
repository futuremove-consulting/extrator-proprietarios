"""Logging estruturado para producao."""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Formatter JSON para logs estruturados."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Adiciona campos extras
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent
        if hasattr(record, "source"):
            log_data["source"] = record.source
        if hasattr(record, "record_key"):
            log_data["record_key"] = record.record_key
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        # Adiciona excecao se existir
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Formatter texto para desenvolvimento."""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        base = f"[{timestamp}] {record.levelname:8s} {record.name}: {record.getMessage()}"
        
        if hasattr(record, "agent"):
            base += f" [agent={record.agent}]"
        if hasattr(record, "source"):
            base += f" [source={record.source}]"
        
        if record.exc_info:
            base += f"
{self.formatException(record.exc_info)}"
        
        return base


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[Path] = None
) -> logging.Logger:
    """Configura logging do modulo."""
    logger = logging.getLogger("extrator_prop")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove handlers existentes
    logger.handlers.clear()
    
    # Formatter
    if format_type == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (se especificado)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Obtem logger com nome especifico."""
    return logging.getLogger(f"extrator_prop.{name}")
