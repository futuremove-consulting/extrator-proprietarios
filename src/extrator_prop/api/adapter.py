"""Adapter: CanonicalContact.to_dict() -> shape PilotCRM ExtractedOwner.

Bridge para
    pilotcrm/apps/pilotcrm/src/modules/captacao/types.ts#ExtractedOwner

Recebe o dict canonico (saida de CanonicalContact.to_dict(), em
``src/extrator_prop/types.py``) e devolve o contrato esperado pelo
``CaptacaoForm``/``MockCaptureProvider`` do PilotCRM:
``[ExtractedOwner]`` com campos {source,fullName,cpf,phone,email,street,
number,complement,unit,cep,city,state,neighborhood,classification,
confidence,whatsappValidation,raw}.
"""
from __future__ import annotations

from typing import Any

# confidence nivel -> score numerico (0..1); alinhado ao DEMO do PilotCRM
# (Maria alta=0.95, João media=0.62, Carlos alta=0.88, empresa alta=0.9)
_CONFIDENCE_SCORE: dict[str, float] = {'alta': 0.9, 'media': 0.6, 'baixa': 0.3}

# source canonico -> CaptacaoSource valido (os 3 agentes)
_SOURCES_VALIDOS = {'captei', 'eemovel', 'fisgar'}


def confidence_to_number(level: str | None) -> float:
    '''Converte nivel semantico em score numerico para o frontend.'''
    if level in _CONFIDENCE_SCORE:
        return _CONFIDENCE_SCORE[level]
    return 0.3


def classify(entity_type: str | None, confidence_level: str | None) -> str:
    '''Mapeia EntityType + confidence -> OwnerClassification PilotCRM.

    Regra alinhada ao DEMO: PF+alta -> proprietario; PF+media/baixa ->
    possivel_morador; PJ -> empresa; desconhecido -> indefinido.
    '''
    if entity_type == 'Pessoa Juridica':
        return 'empresa'
    if entity_type == 'Pessoa Fisica':
        return 'proprietario' if confidence_level == 'alta' else 'possivel_morador'
    return 'indefinido'


def _whatsapp(phone: dict[str, Any] | None) -> dict[str, Any]:
    '''Deriva WhatsAppValidation a partir de PhoneValidation canonico.'''
    if phone is None:
        return {'status': 'sem_whatsapp', 'donodozap_com': False, 'donodozap_com_br': False}
    is_valid = bool(phone.get('is_valid'))
    ddz_com = bool(phone.get('donodozap_com'))
    ddz_br = bool(phone.get('donodozap_com_br'))
    dono = ddz_com or ddz_br
    status = 'validado' if (is_valid or dono) else 'nao_validado'
    return {
        'status': status,
        'donodozap_com': ddz_com,
        'donodozap_com_br': ddz_br,
        'score_nome': phone.get('name_match_score', 0.0),
        'nome_publico': phone.get('name_match_score', 0.0),
        'source': phone.get('source'),
    }


def to_extracted_owner(canon: dict[str, Any]) -> dict[str, Any]:
    '''Canonico dict -> ExtractedOwner dict (PilotCRM).'''
    addr = canon.get('address') or {}
    phones = canon.get('phones') or []
    emails = canon.get('emails') or []
    metadata = canon.get('metadata') or {}
    source = canon.get('source') or 'captei'
    source_safe = source if source in _SOURCES_VALIDOS else 'captei'
    phone0 = phones[0] if phones else None

    return {
        'source': source_safe,
        'fullName': canon.get('name') or '',
        'cpf': canon.get('cpf') or None,
        'phone': phone0.get('number') if phone0 else None,
        'email': emails[0].get('email') if emails else None,
        'street': addr.get('street') or None,
        'number': addr.get('number') or None,
        'complement': addr.get('complement') or None,
        'unit': metadata.get('unit') or None,
        'cep': addr.get('postal_code') or None,
        'city': addr.get('city') or None,
        'state': addr.get('state') or None,
        'neighborhood': addr.get('neighborhood') or None,
        'classification': classify(canon.get('entity_type'), canon.get('confidence')),
        'confidence': confidence_to_number(canon.get('confidence')),
        'whatsappValidation': _whatsapp(phone0),
        'raw': {'source': source, 'source_id': str(canon.get('source_id') or '')},
    }


def to_pilotcrm(canons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    '''Canonico dict list -> [ExtractedOwner] list (PilotCRM CaptacaoResult.items).'''
    return [to_extracted_owner(c) for c in canons]
