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
    """Normaliza descrição da unidade para matching."""
    if not unidade:
        return ""
    return unidade.lower().strip()


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