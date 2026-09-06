"""Pacote da API HTTP do extrator."""
from extrator_prop.api.adapter import to_extracted_owner, to_pilotcrm
from extrator_prop.api.app import create_app
from extrator_prop.service.extractor_service import ExtractorService

__all__ = ['ExtractorService', 'create_app', 'to_extracted_owner', 'to_pilotcrm']
