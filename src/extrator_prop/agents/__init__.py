"""Agentes de extracao."""

from extrator_prop.agents.base import AgentBase, ExtractionStats
from extrator_prop.agents.captei import CapteiAgent
from extrator_prop.agents.fisgar import FisgarAgent
from extrator_prop.agents.eemovel import EEmovelAgent

__all__ = [
    "AgentBase",
    "ExtractionStats",
    "CapteiAgent",
    "FisgarAgent",
    "EEmovelAgent",
]
