"""Regras de validação cross-origem para consolidação multi-origem."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re

from comum import validar_email


class ValidationSeverity(str, Enum):
    ERROR = "error"      # Bloqueia merge / requer revisão manual
    WARNING = "warning"  # Alerta mas permite merge
    INFO = "info"        # Informativo


@dataclass
class ValidationResult:
    field: str
    severity: ValidationSeverity
    message: str
    sources_involved: List[str]
    suggested_action: str = ""


class ValidationRule:
    """Regra de validação cross-origem."""
    
    def __init__(self, name: str, severity: ValidationSeverity, 
                 check_fn: callable, message: str, suggested_action: str = ""):
        self.name = name
        self.severity = severity
        self.check_fn = check_fn
        self.message = message
        self.suggested_action = suggested_action
    
    def validate(self, field_values: Dict[str, Any], sources: List[str]) -> Optional[ValidationResult]:
        try:
            if self.check_fn(field_values, sources):
                return None
            return ValidationResult(
                field=self.name,
                severity=self.severity,
                message=self.message,
                sources_involved=sources,
                suggested_action=self.suggested_action
            )
        except Exception as e:
            return ValidationResult(
                field=self.name,
                severity=ValidationSeverity.WARNING,
                message=f"Erro na validação {self.name}: {e}",
                sources_involved=sources
            )


def validar_cpf(cpf: str) -> bool:
    """Valida CPF (dígitos verificadores)."""
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    # Calcular primeiro dígito
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10
    
    # Calcular segundo dígito
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10
    
    return cpf[-2:] == f"{digito1}{digito2}"


def extrair_cpf_texto(texto: str) -> str:
    """Extrai o primeiro CPF VALIDO (digito verificador conferido) de um texto livre.

    Cobre formas com mascara (000.000.000-00) e sem mascara (00000000000).
    Retorna apenas os digitos do CPF valido, ou '' se nenhum for encontrado.
    """
    if not texto:
        return ""
    candidatos = re.findall(r"\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2}", str(texto))
    for cand in candidatos:
        if validar_cpf(cand):
            return re.sub(r"\D", "", cand)
    return ""


def validar_rg(rg: str) -> bool:
    """Validação básica de RG (formato)."""
    if not rg:
        return False
    # RG pode ter vários formatos por estado
    # Aceitar se tem pelo menos 7 dígitos
    digitos = re.sub(r'\D', '', rg)
    return len(digitos) >= 7


# --- Regras de Validação ---

REGRAS_VALIDACAO = [
    # CPF
    ValidationRule(
        name="cpf_consistency",
        severity=ValidationSeverity.ERROR,
        check_fn=lambda vals, srcs: len(set(v for v in vals.values() if v and validar_cpf(v))) <= 1,
        message="CPFs diferentes encontrados entre origens",
        suggested_action="Revisão manual: verificar qual CPF está correto"
    ),
    
    ValidationRule(
        name="cpf_validity",
        severity=ValidationSeverity.WARNING,
        check_fn=lambda vals, srcs: all(not v or validar_cpf(v) for v in vals.values()),
        message="CPF inválido encontrado",
        suggested_action="Verificar dígitos do CPF"
    ),
    
    # RG
    ValidationRule(
        name="rg_consistency",
        severity=ValidationSeverity.WARNING,
        check_fn=lambda vals, srcs: len(set(v for v in vals.values() if v)) <= 1,
        message="RGs diferentes entre origens",
        suggested_action="Verificar qual RG está correto"
    ),
    
    # Nome
    ValidationRule(
        name="nome_consistency",
        severity=ValidationSeverity.WARNING,
        check_fn=lambda vals, srcs: _nomes_sao_compativeis(list(vals.values())),
        message="Nomes significativamente diferentes entre origens",
        suggested_action="Verificar se é mesma pessoa (homonímia) ou erro de digitação"
    ),
    
    # Telefone
    ValidationRule(
        name="telefone_consistency",
        severity=ValidationSeverity.INFO,
        check_fn=lambda vals, srcs: True,  # Sempre passa - telefones podem ser complementares
        message="Telefones diferentes entre origens (podem ser complementares)",
        suggested_action="Unificar todos os telefones (política union_dedup)"
    ),
    
    # Email
    ValidationRule(
        name="email_validity",
        severity=ValidationSeverity.WARNING,
        check_fn=lambda vals, srcs: all(not v or validar_email(v) for emails in vals.values() for v in (emails if isinstance(emails, list) else [emails])),
        message="Email inválido encontrado",
        suggested_action="Verificar formato do email"
    ),
    
    # Tipo de pessoa
    ValidationRule(
        name="tipo_pessoa_consistency",
        severity=ValidationSeverity.ERROR,
        check_fn=lambda vals, srcs: _tipos_pessoa_compativeis(list(vals.values())),
        message="Tipos de pessoa conflitantes (Proprietário vs Morador)",
        suggested_action="Revisão manual: separar em Golden Records distintos"
    ),
    
    # Endereço
    ValidationRule(
        name="endereco_consistency",
        severity=ValidationSeverity.WARNING,
        check_fn=lambda vals, srcs: _enderecos_sao_compativeis(list(vals.values())),
        message="Endereços principais divergentes",
        suggested_action="Verificar se mesma unidade/endereço"
    ),
    
    # Data nascimento
    ValidationRule(
        name="data_nascimento_consistency",
        severity=ValidationSeverity.WARNING,
        check_fn=lambda vals, srcs: _datas_nascimento_compativeis(list(vals.values())),
        message="Datas de nascimento diferentes",
        suggested_action="Verificar qual data está correta"
    ),
    
    # WhatsApp
    ValidationRule(
        name="whatsapp_status",
        severity=ValidationSeverity.INFO,
        check_fn=lambda vals, srcs: True,  # Informativo apenas
        message="Status WhatsApp disponível apenas no Captei",
        suggested_action="Preservar status do Captei no Golden Record"
    ),
]


def _nomes_sao_compativeis(nomes: List[str]) -> bool:
    """Verifica se nomes são compatíveis (permitindo variações)."""
    nomes_validos = [n for n in nomes if n]
    if len(nomes_validos) <= 1:
        return True
    
    # Normalizar para comparação
    norm = [re.sub(r'[^\w\s]', '', n).upper().strip() for n in nomes_validos]
    
    # Verificar se um contém o outro (ex: "ANA PAULA" vs "ANA PAULA RODRIGUES")
    for i, n1 in enumerate(norm):
        for n2 in norm[i+1:]:
            if n1 in n2 or n2 in n1:
                return True
            # Similaridade alta
            from difflib import SequenceMatcher
            if SequenceMatcher(None, n1, n2).ratio() > 0.85:
                return True
    
    return False


def _tipos_pessoa_compativeis(tipos: List[str]) -> bool:
    """Verifica se tipos de pessoa são compatíveis."""
    tipos_validos = [t for t in tipos if t]
    if len(tipos_validos) <= 1:
        return True
    
    # Proprietário e Morador são INCOMPATÍVEIS (devem ser Golden Records separados)
    tem_proprietario = any('propriet' in t.lower() for t in tipos_validos)
    tem_morador = any('morador' in t.lower() for t in tipos_validos)
    
    return not (tem_proprietario and tem_morador)


def _enderecos_sao_compativeis(enderecos: List[str]) -> bool:
    """Verifica se endereços são compatíveis."""
    end_validos = [e for e in enderecos if e]
    if len(end_validos) <= 1:
        return True
    
    # Normalizar
    norm = [re.sub(r'[^\w\s]', '', e).upper().strip() for e in end_validos]
    
    # Verificar similaridade
    from difflib import SequenceMatcher
    for i, n1 in enumerate(norm):
        for n2 in norm[i+1:]:
            if SequenceMatcher(None, n1, n2).ratio() > 0.7:
                return True
    
    return False


def _datas_nascimento_compativeis(datas: List[str]) -> bool:
    """Verifica se datas de nascimento são compatíveis."""
    datas_validas = [d for d in datas if d]
    if len(datas_validas) <= 1:
        return True
    
    # Normalizar formato DD/MM/YYYY
    norm = []
    for d in datas_validas:
        d = re.sub(r'[^\d]', '/', d)
        parts = d.split('/')
        if len(parts) == 3:
            try:
                dia, mes, ano = parts
                if len(ano) == 2:
                    ano = '19' + ano if int(ano) > 30 else '20' + ano
                norm.append(f"{int(dia):02d}/{int(mes):02d}/{ano}")
            except:
                pass
    
    return len(set(norm)) <= 1


def executar_validacoes(field_values: Dict[str, Dict[str, Any]], 
                        golden_record: Dict[str, Any]) -> List[ValidationResult]:
    """
    Executa todas as validações cross-origem.
    
    Args:
        field_values: Dict {field_name: {source: value}}
        golden_record: Golden Record sendo construído (para contexto)
    
    Returns:
        Lista de ValidationResult
    """
    resultados = []
    
    for regra in REGRAS_VALIDACAO:
        if regra.name in field_values:
            vals = field_values[regra.name]
            sources = list(vals.keys())
            result = regra.validate(vals, sources)
            if result:
                resultados.append(result)
    
    return resultados


def classificar_validacoes(resultados: List[ValidationResult]) -> Dict[str, List[ValidationResult]]:
    """Classifica validações por severidade."""
    return {
        'errors': [r for r in resultados if r.severity == ValidationSeverity.ERROR],
        'warnings': [r for r in resultados if r.severity == ValidationSeverity.WARNING],
        'infos': [r for r in resultados if r.severity == ValidationSeverity.INFO]
    }


def tem_erros_bloqueantes(resultados: List[ValidationResult]) -> bool:
    """Verifica se há erros que bloqueiam o merge automático."""
    return any(r.severity == ValidationSeverity.ERROR for r in resultados)