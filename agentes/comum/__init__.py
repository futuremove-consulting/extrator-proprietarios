"""Módulo comum para extração de proprietários."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def canonicalizar_texto(texto: str) -> str:
    """Normaliza texto para matching: lowercase, sem acentos, sem pontuação."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    # Remover acentos
    texto = re.sub(r'[àáâãä]', 'a', texto)
    texto = re.sub(r'[èéêë]', 'e', texto)
    texto = re.sub(r'[ìíîï]', 'i', texto)
    texto = re.sub(r'[òóôõö]', 'o', texto)
    texto = re.sub(r'[ùúûü]', 'u', texto)
    texto = re.sub(r'[ç]', 'c', texto)
    # Remover pontuação e espaços extras
    texto = re.sub(r"[^\w\s]", '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def gerar_record_key(name_canonical: str, unit_canonical: str, address_canonical: str) -> str:
    """Gera chave única composta para deduplicação."""
    componentes = f"{name_canonical}|{unit_canonical}|{address_canonical}"
    return hashlib.sha256(componentes.encode()).hexdigest()[:20]


def extrair_digitos_telefone(telefone: str) -> str:
    """Extrai apenas dígitos do telefone."""
    return re.sub(r'\D', '', telefone)


def classificar_entidade(nome: str) -> str:
    """Classifica como pessoa física ou empresa."""
    if not nome:
        return "Revisao Manual"
    nome_upper = nome.upper().strip()
    tokens = ['LTDA', 'S.A.', 'BANCO', 'CAIXA ECONOMICA', 'PARTICIPACOES',
              'CONSORCIOS', 'INCORPORADORA', 'EMPREENDIMENTOS', 'HOLDING',
              'FUNDO', 'IMOBILIARIA', 'CONSTRUTORA', 'EMPRESA']
    for token in tokens:
        if token in nome_upper:
            return "Empresa"
    return "Pessoa Fisica"


def criar_estrutura_lote(nome_lote: str, diretorio_base: str) -> Dict[str, Path]:
    """Cria estrutura de diretórios para um lote."""
    base = Path(diretorio_base) / nome_lote
    estrutura = {
        'base': base,
        'raw': base / 'raw',
        'curated': base / 'curated',
        'checkpoints': base / 'checkpoints',
        'logs': base / 'logs',
        'manifest': base / 'manifest'
    }
    for p in estrutura.values():
        p.mkdir(parents=True, exist_ok=True)
    return estrutura


def salvar_json_seguro(dados: Any, caminho: Path) -> None:
    """Salva JSON de forma determinista e segura."""
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2, sort_keys=True)


def carregar_json(caminho: Path) -> Any:
    """Carrega arquivo JSON."""
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)


def append_ndjson(registro: Dict[str, Any], caminho: Path) -> None:
    """Adiciona linha em arquivo NDJSON (append-only)."""
    with open(caminho, 'a', encoding='utf-8') as f:
        f.write(json.dumps(registro, ensure_ascii=False) + '\n')


def timestamp_iso() -> str:
    """Retorna timestamp atual em formato ISO."""
    return datetime.now().isoformat()


def normalizar_unidade(unidade: str) -> str:
    """Normaliza descrição da unidade para matching (legado - usa parse_unidade)."""
    if not unidade:
        return ""
    return unidade.lower().strip()


def parse_unidade(unidade: str) -> Dict[str, str]:
    """
    Parseia unidade em componentes estruturados.
    
    Returns:
        {
            'unidade_imovel': 'AP 101' ou '',
            'unidade_vaga': 'VG 3M TER' ou '',
            'tipo_unidade': 'apartamento' | 'cobertura' | 'garden' | 'sala' | 'loja' | 'vaga' | 'outro'
        }
    """
    if not unidade:
        return {'unidade_imovel': '', 'unidade_vaga': '', 'tipo_unidade': 'outro'}
    
    unidade_upper = unidade.upper().strip()
    
    # Padrões de vaga
    vaga_patterns = [
        r'VG\s*\d+[A-Z]*\s*(TER|SS\d+|M\s*TER)?',
        r'VAGA\s+\d+',
        r'GARAGEM\s+\d+',
        r'BOX\s+\d+'
    ]
    
    # Padrões de imóvel
    imovel_patterns = [
        r'AP\s+\d+[A-Z]?',
        r'APARTAMENTO\s+\d+[A-Z]?',
        r'CASA\s+\d+[A-Z]?',
        r'SALA\s+\d+[A-Z]?',
        r'LOJA\s+\d+[A-Z]?',
        r'COBERTURA\s+\d+[A-Z]?',
        r'GARDEN\s+\d+[A-Z]?',
        r'TORRE\s+[A-Z]\s+\d+',
        r'BL[OCO]?\s+[A-Z]\s+\d+',
        r'UNIDADE\s+\d+'
    ]
    
    unidade_imovel = ''
    unidade_vaga = ''
    
    # Separar por vírgula, " e ", " + ", ou espaço duplo
    partes = re.split(r',\s*|\s+e\s+|\s+\+\s+|\s{2,}', unidade)
    
    for parte in partes:
        parte = parte.strip()
        if not parte:
            continue
            
        parte_upper = parte.upper()
        
        # Verificar se é vaga
        is_vaga = any(re.search(p, parte_upper) for p in vaga_patterns)
        
        # Verificar se é imóvel
        is_imovel = any(re.search(p, parte_upper) for p in imovel_patterns)
        
        if is_vaga and not is_imovel:
            if unidade_vaga:
                unidade_vaga += '; ' + parte
            else:
                unidade_vaga = parte
        elif is_imovel and not is_vaga:
            if unidade_imovel:
                unidade_imovel += '; ' + parte
            else:
                unidade_imovel = parte
        else:
            # Ambíguo - tentar classificar por palavras-chave
            if any(kw in parte_upper for kw in ['VG', 'VAGA', 'GARAGEM', 'BOX']):
                if unidade_vaga:
                    unidade_vaga += '; ' + parte
                else:
                    unidade_vaga = parte
            else:
                if unidade_imovel:
                    unidade_imovel += '; ' + parte
                else:
                    unidade_imovel = parte
    
    # Classificar tipo
    tipo_unidade = classificar_tipo_unidade(unidade_imovel, unidade_vaga)
    
    return {
        'unidade_imovel': unidade_imovel.strip(),
        'unidade_vaga': unidade_vaga.strip(),
        'tipo_unidade': tipo_unidade
    }


def classificar_tipo_unidade(unidade_imovel: str, unidade_vaga: str) -> str:
    """Classifica tipo de unidade baseado nos componentes parseados."""
    if not unidade_imovel and not unidade_vaga:
        return 'outro'
    
    if unidade_vaga and not unidade_imovel:
        return 'vaga'
    
    imovel_upper = unidade_imovel.upper()
    
    if 'COBERTURA' in imovel_upper:
        return 'cobertura'
    if 'GARDEN' in imovel_upper:
        return 'garden'
    if 'SALA' in imovel_upper:
        return 'sala'
    if 'LOJA' in imovel_upper:
        return 'loja'
    if 'CASA' in imovel_upper:
        return 'casa'
    if any(kw in imovel_upper for kw in ['AP ', 'APARTAMENTO', 'UNIDADE']):
        return 'apartamento'
    
    return 'outro'


def gerar_record_key_v2(name_canonical: str, unidade_imovel: str, unidade_vaga: str, address_canonical: str) -> str:
    """
    Gera chave única v2 com componentes separados para melhor matching.
    
    Componentes: nome|unidade_imovel|unidade_vaga|endereco
    """
    imovel_norm = canonicalizar_texto(unidade_imovel)
    vaga_norm = canonicalizar_texto(unidade_vaga)
    componentes = f"{name_canonical}|{imovel_norm}|{vaga_norm}|{address_canonical}"
    return hashlib.sha256(componentes.encode()).hexdigest()[:20]


def formatar_telefone(telefone: str) -> str:
    """Formata telefone para exibição."""
    digitos = extrair_digitos_telefone(telefone)
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    elif len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"
    return telefone


def validar_email(email: str) -> bool:
    """Validação básica de formato de e-mail."""
    if not email:
        return False
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(padrao, email))


def deduplicar_telefones(telefones: List[str]) -> List[str]:
    """Deduplica telefones por dígitos."""
    vistos = set()
    resultado = []
    for tel in telefones:
        digitos = extrair_digitos_telefone(tel)
        if digitos and digitos not in vistos:
            vistos.add(digitos)
            resultado.append(tel)
    return resultado


def deduplicar_emails(emails: List[str]) -> List[str]:
    """Deduplica e-mails por lowercase."""
    vistos = set()
    resultado = []
    for email in emails:
        email_lower = email.lower().strip()
        if email_lower and email_lower not in vistos:
            vistos.add(email_lower)
            resultado.append(email)
    return resultado


# WhatsApp Validation exports
from .whatsapp_validator import (
    WhatsAppValidator,
    WhatsAppValidationResult,
    ValidationSource,
    ValidationTier
)
from .donodozap_br_validator import DonoDoZapBRValidator
from .donodozap_com_validator import DonoDoZapComValidator
from .whatsapp_validation_service import (
    WhatsAppValidationService,
    ValidationPolicy,
    create_validation_service
)