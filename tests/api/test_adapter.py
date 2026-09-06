"""Testes do adapter CanonicalContact -> ExtractedOwner (PilotCRM)."""
import copy

from extrator_prop.api.adapter import (
    classify,
    confidence_to_number,
    to_extracted_owner,
    to_pilotcrm,
)

CANON_PF = {
    'name': 'Maria Silva',
    'source': 'captei',
    'source_id': '1',
    'entity_type': 'Pessoa Fisica',
    'confidence': 'alta',
    'cpf': '529.982.247-25',
    'phones': [
        {
            'number': '(11) 91234-5678',
            'is_valid': True,
            'donodozap_com': True,
            'donodozap_com_br': True,
            'name_match_score': 0.9,
            'source': 'captei',
        }
    ],
    'emails': [{'email': 'maria.silva@example.com', 'is_valid': True, 'source': 'captei'}],
    'address': {
        'street': 'Av. Paulista',
        'number': '1000',
        'complement': 'Apto 52',
        'neighborhood': 'Bela Vista',
        'city': 'Sao Paulo',
        'state': 'SP',
        'postal_code': '01310-100',
        'full': 'Av. Paulista, 1000',
    },
    'validation_status': 'validado',
    'metadata': {},
}

CANON_PJ = {
    'name': 'Imobiliaria Ltda',
    'source': 'fisgar',
    'source_id': None,
    'entity_type': 'Pessoa Juridica',
    'confidence': 'baixa',
    'cpf': None,
    'phones': [],
    'emails': [],
    'address': {'city': 'Sao Paulo'},
    'validation_status': 'nao_validado',
    'metadata': {},
}

CANON_MORADOR = {
    'name': 'Joao',
    'source': 'eemovel',
    'entity_type': 'Pessoa Fisica',
    'confidence': 'media',
    'cpf': None,
    'phones': [
        {
            'number': '(11) 9999-9999',
            'is_valid': False,
            'donodozap_com': False,
            'donodozap_com_br': False,
            'name_match_score': 0.1,
            'source': 'eemovel',
        }
    ],
    'emails': [],
    'address': {},
    'validation_status': 'nao_validado',
    'metadata': {},
}


def test_classify_pf_alta_proprietario():
    assert classify('Pessoa Fisica', 'alta') == 'proprietario'


def test_classify_pf_media_possivel_morador():
    assert classify('Pessoa Fisica', 'media') == 'possivel_morador'


def test_classify_pj_empresa():
    assert classify('Pessoa Juridica', 'baixa') == 'empresa'


def test_confidence_map():
    assert confidence_to_number('alta') == 0.9
    assert confidence_to_number('media') == 0.6
    assert confidence_to_number('baixa') == 0.3
    assert confidence_to_number(None) == 0.3


def test_to_extracted_owner_pf_donodozap():
    out = to_extracted_owner(CANON_PF)
    assert out['source'] == 'captei'
    assert out['fullName'] == 'Maria Silva'
    assert out['cpf'] == '529.982.247-25'
    assert out['phone'] == '(11) 91234-5678'
    assert out['email'] == 'maria.silva@example.com'
    assert out['street'] == 'Av. Paulista'
    assert out['number'] == '1000'
    assert out['cep'] == '01310-100'
    assert out['complement'] == 'Apto 52'
    assert out['city'] == 'Sao Paulo'
    assert out['state'] == 'SP'
    assert out['neighborhood'] == 'Bela Vista'
    assert out['classification'] == 'proprietario'
    assert out['confidence'] == 0.9
    wa = out['whatsappValidation']
    assert wa['status'] == 'validado'
    assert wa['donodozap_com_br'] is True


def test_to_extracted_owner_pj_sem_phone():
    out = to_extracted_owner(CANON_PJ)
    assert out['classification'] == 'empresa'
    assert out['phone'] is None
    assert out['whatsappValidation']['status'] == 'sem_whatsapp'
    assert out['cpf'] is None


def test_to_extracted_owner_morador_possivel():
    out = to_extracted_owner(CANON_MORADOR)
    assert out['classification'] == 'possivel_morador'
    assert out['whatsappValidation']['status'] == 'nao_validado'


def test_fields_all_keys_present():
    out = to_extracted_owner(CANON_PF)
    esperado = {
        'source', 'fullName', 'cpf', 'phone', 'email', 'street', 'number',
        'complement', 'unit', 'cep', 'city', 'state', 'neighborhood',
        'classification', 'confidence', 'whatsappValidation', 'raw',
    }
    assert set(out) == esperado


def test_source_invalid_fallback_captei():
    c = copy.deepcopy(CANON_PF)
    c['source'] = 'donodozap'
    out = to_extracted_owner(c)
    assert out['source'] == 'captei'


def test_to_pilotcrm_list():
    items = to_pilotcrm([CANON_PF, CANON_PJ])
    assert len(items) == 2
    assert items[0]['fullName'] == 'Maria Silva'
    assert items[1]['classification'] == 'empresa'
