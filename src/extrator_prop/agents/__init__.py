"""Agentes de extracao."""

from extrator_prop.agents.base import AgentBase, ExtractionStats
from extrator_prop.agents.captei import CapteiAgent
from extrator_prop.agents.eemovel import EEmovelAgent
from extrator_prop.agents.fisgar import FisgarAgent

__all__ = [
    "AgentBase",
    "CapteiAgent",
    "EEmovelAgent",
    "ExtractionStats",
    "FisgarAgent",
]
