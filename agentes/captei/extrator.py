"""Módulo extrator específico para Captei."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from comum import (
    extrair_digitos_telefone,
    deduplicar_telefones,
    deduplicar_emails,
    validar_email,
    timestamp_iso
)


def processar_modal_captei(dados_modal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa dados extraídos do modal do Captei.
    
    Args:
        dados_modal: Dados brutos extraídos do modal
        
    Returns:
        Registro estruturado com dados curados
    """
    registro = {
        'detalhes': {},
        'telefones': [],
        'emails': [],
        'metadata': {}
    }
    
    # Processar detalhes principais
    registro['detalhes'] = {
        'nome_completo': dados_modal.get('nome_completo', ''),
        'papel': dados_modal.get('papel', ''),
        'endereco_retornado': dados_modal.get('endereco_retornado', ''),
        'unidade': dados_modal.get('unidade', ''),
        'inscricao': dados_modal.get('inscricao', ''),
        'idade': dados_modal.get('idade'),
        'data_nascimento': dados_modal.get('data_nascimento'),
        'data_nascimento_ausente': dados_modal.get('data_nascimento_ausente', False)
    }
    
    # Processar telefones
    telefones_brutos = dados_modal.get('telefones', [])
    telefones_processados = []
    
    for tel in telefones_brutos:
        telefone_processado = {
            'numero_raw': tel.get('numero', ''),
            'digitos': extrair_digitos_telefone(tel.get('numero', '')),
            'tipo': tel.get('tipo', ''),
            'whatsapp_status': tel.get('whatsapp_status', 'nao_validado'),
            'validado': tel.get('whatsapp_status') == 'validado'
        }
        telefones_processados.append(telefone_processado)
    
    # Deduplicar telefones
    telefones_deduplicados = deduplicar_telefones(
        [t['numero_raw'] for t in telefones_processados]
    )
    
    # Manter apenas telefones deduplicados com seus metadados
    registro['telefones'] = [
        t for t in telefones_processados 
        if t['numero_raw'] in telefones_deduplicados
    ]
    
    # Processar e-mails
    emails_brutos = dados_modal.get('emails', [])
    emails_processados = []
    
    for email in emails_brutos:
        email_processado = {
            'endereco_raw': email.get('endereco', ''),
            'endereco_lower': email.get('endereco', '').lower().strip(),
            'valido': validar_email(email.get('endereco', '')),
            'tipo': email.get('tipo', '')
        }
        emails_processados.append(email_processado)
    
    # Deduplicar e-mails
    emails_deduplicados = deduplicar_emails(
        [e['endereco_raw'] for e in emails_processados]
    )
    
    registro['emails'] = [
        e for e in emails_processados 
        if e['endereco_raw'] in emails_deduplicados
    ]
    
    # Metadados da extração
    registro['metadata'] = {
        'timestamp_extracao': timestamp_iso(),
        'metodo_extracao': dados_modal.get('metodo_extracao', 'manual'),
        'modal_completo': dados_modal.get('modal_completo', True),
        'whatsapp_validado': any(t['validado'] for t in registro['telefones']),
        'total_telefones': len(registro['telefones']),
        'total_emails': len(registro['emails']),
        'tem_nascimento': bool(registro['detalhes']['data_nascimento']),
        'qualidade': _calcular_qualidade(registro)
    }
    
    return registro


def _calcular_qualidade(registro: Dict[str, Any]) -> str:
    """Calcula score de qualidade do registro extraído."""
    detalhes = registro.get('detalhes', {})
    telefones = registro.get('telefones', [])
    emails = registro.get('emails', [])
    
    score = 0
    
    # Nome completo presente
    if detalhes.get('nome_completo'):
        score += 1
    
    # Pelo menos um telefone
    if telefones:
        score += 1
    
    # Telefone validado
    if any(t.get('validado') for t in telefones):
        score += 1
    
    # Pelo menos um e-mail válido
    if any(e.get('valido') for e in emails):
        score += 1
    
    # Data de nascimento presente
    if detalhes.get('data_nascimento'):
        score += 1
    
    # Classificar qualidade
    if score >= 4:
        return 'alta'
    elif score >= 2:
        return 'media'
    else:
        return 'baixa'


def validar_dados_modal(dados_modal: Dict[str, Any], registro_manifest: Dict[str, Any]) -> bool:
    """
    Valida se os dados do modal correspondem ao registro do manifest.
    
    Args:
        dados_modal: Dados extraídos do modal
        registro_manifest: Registro do manifest original
        
    Returns:
        True se dados são consistentes, False caso contrário
    """
    nome_modal = dados_modal.get('nome_completo', '').upper().strip()
    nome_manifest = registro_manifest.get('name_raw', '').upper().strip()
    
    # Validação básica de nome (permite pequenas variações)
    if not _nomes_similares(nome_modal, nome_manifest):
        return False
    
    unidade_modal = dados_modal.get('unidade', '').upper().strip()
    unidade_manifest = registro_manifest.get('unit_raw', '').upper().strip()
    
    # Validação de unidade quando disponível
    if unidade_modal and unidade_manifest:
        if unidade_modal != unidade_manifest:
            return False
    
    return True


def _nomes_similares(nome1: str, nome2: str) -> bool:
    """Verifica se dois nomes são similares (para validação de modal)."""
    # Remover acentos e espaços extras
    nome1 = re.sub(r'[^\w\s]', '', nome1).lower().strip()
    nome2 = re.sub(r'[^\w\s]', '', nome2).lower().strip()
    
    # Comparação direta
    if nome1 == nome2:
        return True
    
    # Verificar se um contém o outro (para variações de nome completo)
    if nome1 in nome2 or nome2 in nome1:
        return True
    
    return False


def extrair_telefones_ver_mais(dados_paginados: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extrai e consolida telefones de múltiplas páginas "VER MAIS".
    
    Args:
        dados_paginados: Lista de dados de cada página de telefones
        
    Returns:
        Lista consolidada de telefones
    """
    todos_telefones = []
    
    for pagina in dados_paginados:
        telefones_pagina = pagina.get('telefones', [])
        todos_telefones.extend(telefones_pagina)
    
    # Deduplicar
    return deduplicar_telefones([t.get('numero', '') for t in todos_telefones])


def normalizar_status_whatsapp(status_bruto: str) -> str:
    """Normaliza status de WhatsApp do Captei."""
    if not status_bruto:
        return 'nao_validado'
    
    status_lower = status_bruto.lower().strip()
    
    if status_lower in ['validado', 'valid', 'whatsapp_validado']:
        return 'validado'
    elif status_lower in ['invalido', 'invalid', 'nao_validado']:
        return 'nao_validado'
    elif status_lower in ['pendente', 'pending', 'verificando']:
        return 'pendente'
    else:
        return 'desconhecido'