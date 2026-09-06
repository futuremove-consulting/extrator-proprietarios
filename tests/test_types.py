"""Testes para types.py."""

from extrator_prop.types import (
    EntityType,
    ValidationStatus,
    ConfidenceLevel,
    Address,
    PhoneValidation,
    EmailValidation,
    CanonicalContact
)


class TestEnums:
    """Testes para enums."""
    
    def test_entity_type_values(self):
        assert EntityType.PESSOA_FISICA.value == "Pessoa Fisica"
        assert EntityType.PESSOA_JURIDICA.value == "Pessoa Juridica"
    
    def test_validation_status_values(self):
        assert ValidationStatus.VALIDADO.value == "validado"
        assert ValidationStatus.NAO_VALIDADO.value == "nao_validado"
    
    def test_confidence_level_values(self):
        assert ConfidenceLevel.ALTA.value == "alta"
        assert ConfidenceLevel.MEDIA.value == "media"


class TestAddress:
    """Testes para Address."""
    
    def test_to_dict(self):
        addr = Address(
            street="Rua Teste",
            number="123",
            city="Sao Paulo"
        )
        data = addr.to_dict()
        
        assert data["street"] == "Rua Teste"
        assert data["number"] == "123"
        assert data["city"] == "Sao Paulo"
        # Campos None nao aparecem
        assert "complement" not in data


class TestPhoneValidation:
    """Testes para PhoneValidation."""
    
    def test_defaults(self):
        phone = PhoneValidation(number="11999999999")
        assert phone.number == "11999999999"
        assert phone.is_valid is False
        assert phone.confidence.value == "baixa"


class TestCanonicalContact:
    """Testes para CanonicalContact."""
    
    def test_to_dict(self):
        contact = CanonicalContact(
            name="Joao Silva",
            source="captei",
            source_id="123",
            phones=[PhoneValidation(number="11999999999", source="captei")],
            emails=[EmailValidation(email="joao@email.com", source="captei")]
        )
        
        data = contact.to_dict()
        
        assert data["name"] == "Joao Silva"
        assert data["source"] == "captei"
        assert len(data["phones"]) == 1
        assert data["phones"][0]["number"] == "11999999999"
        assert len(data["emails"]) == 1
