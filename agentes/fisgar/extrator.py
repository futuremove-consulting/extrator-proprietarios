"""Módulo extrator específico para Fisgar."""

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


def processar_modal_fisgar(dados_modal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa dados extraídos do modal do Fisgar.
    
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
        'data_nascimento_ausente': dados_modal.get('data_nascimento_ausente', False),
        'cpf': dados_modal.get('cpf', ''),
        'rg': dados_modal.get('rg', '')
    }
    
    # Processar telefones (Fisgar não tem validação WhatsApp explícita)
    telefones_brutos = dados_modal.get('telefones', [])
    telefones_processados = []
    
    for tel in telefones_brutos:
        telefone_processado = {
            'numero_raw': tel.get('numero', ''),
            'digitos': extrair_digitos_telefone(tel.get('numero', '')),
            'tipo': tel.get('tipo', ''),
            'principal': tel.get('principal', False),
            'observacao': tel.get('observacao', '')
        }
        telefones_processados.append(telefone_processado)
    
    # Deduplicar telefones
    telefones_deduplicados = deduplicar_telefones(
        [t['numero_raw'] for t in telefones_processados]
    )
    
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
            'tipo': email.get('tipo', ''),
            'principal': email.get('principal', False)
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
        'total_telefones': len(registro['telefones']),
        'total_emails': len(registro['emails']),
        'tem_nascimento': bool(registro['detalhes']['data_nascimento']),
        'tem_cpf': bool(registro['detalhes']['cpf']),
        'qualidade': _calcular_qualidade_fisgar(registro)
    }
    
    return registro


def _calcular_qualidade_fisgar(registro: Dict[str, Any]) -> str:
    """Calcula score de qualidade do registro extraído do Fisgar."""
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
    
    # Telefone principal marcado
    if any(t.get('principal') for t in telefones):
        score += 1
    
    # Pelo menos um e-mail válido
    if any(e.get('valido') for e in emails):
        score += 1
    
    # Data de nascimento presente
    if detalhes.get('data_nascimento'):
        score += 1
    
    # CPF presente (específico do Fisgar)
    if detalhes.get('cpf'):
        score += 1
    
    # Classificar qualidade
    if score >= 5:
        return 'alta'
    elif score >= 3:
        return 'media'
    else:
        return 'baixa'


def validar_dados_modal_fisgar(dados_modal: Dict[str, Any], registro_manifest: Dict[str, Any]) -> bool:
    """
    Valida se os dados do modal correspondem ao registro do manifest no Fisgar.
    
    Args:
        dados_modal: Dados extraídos do modal
        registro_manifest: Registro do manifest original
        
    Returns:
        True se dados são consistentes, False caso contrário
    """
    nome_modal = dados_modal.get('nome_completo', '').upper().strip()
    nome_manifest = registro_manifest.get('name_raw', '').upper().strip()
    
    # Validação básica de nome
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
    
    # Verificar se um contém o outro
    if nome1 in nome2 or nome2 in nome1:
        return True
    
    return False


def localizar_cta_por_linha(dados_linha: Dict[str, Any], selector_base: str = "tr") -> str:
    """
    Gera seletor CSS para localizar o CTA dentro de uma linha específica.
    
    Args:
        dados_linha: Dados da linha da tabela
        selector_base: Seletor base (padrão: tr)
        
    Returns:
        Seletor CSS para o CTA
    """
    nome = dados_linha.get('nome', '')
    unidade = dados_linha.get('unidade', '')
    
    # Estratégia: buscar linha que contém nome e unidade, depois encontrar o CTA descendente
    # Exemplo: tr:has-text("NOME"):has-text("UNIDADE") button:has-text("Consultar")
    
    selector = f'{selector_base}:has-text("{nome}")'
    if unidade:
        selector += f':has-text("{unidade}")'
    
    # Adicionar botão Consultar
    selector += ' button:has-text("Consultar")'
    
    return selector


def extrair_links_tel_mailto(conteudo_html: str) -> Dict[str, List[str]]:
    """
    Extrai links tel: e mailto: de conteúdo HTML.
    
    Args:
        conteudo_html: Conteúdo HTML do modal
        
    Returns:
        Dicionário com listas de telefones e e-mails
    """
    telefones = []
    emails = []
    
    # Extrair links tel:
    tel_pattern = r'href=["\']tel:([^"\']+)["\']'
    telefones_encontrados = re.findall(tel_pattern, conteudo_html)
    telefones.extend(telefones_encontrados)
    
    # Extrair links mailto:
    mailto_pattern = r'href=["\']mailto:([^"\']+)["\']'
    emails_encontrados = re.findall(mailto_pattern, conteudo_html)
    emails.extend(emails_encontrados)
    
    return {
        'telefones': telefones,
        'emails': emails
    }


def normalizar_dados_fisgar(dados_brutos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza dados brutos do Fisgar para formato padrão.
    
    Args:
        dados_brutos: Dados brutos extraídos
        
    Returns:
        Dados normalizados
    """
    normalizado = {
        'nome_completo': dados_brutos.get('nome', ''),
        'papel': dados_brutos.get('tipo_pessoa', ''),
        'endereco_retornado': dados_brutos.get('endereco_completo', ''),
        'unidade': dados_brutos.get('unidade', ''),
        'inscricao': dados_brutos.get('inscricao', ''),
        'idade': dados_brutos.get('idade'),
        'data_nascimento': dados_brutos.get('data_nascimento'),
        'cpf': dados_brutos.get('cpf', ''),
        'rg': dados_brutos.get('rg', ''),
        'telefones': _normalizar_telefones_fisgar(dados_brutos.get('telefones', [])),
        'emails': _normalizar_emails_fisgar(dados_brutos.get('emails', [])),
        'metodo_extracao': dados_brutos.get('metodo', 'manual'),
        'modal_completo': dados_brutos.get('modal_completo', True)
    }
    
    return normalizado


def _normalizar_telefones_fisgar(telefones_brutos: List[Any]) -> List[Dict[str, Any]]:
    """Normaliza lista de telefones do Fisgar."""
    normalizados = []
    
    for tel in telefones_brutos:
        if isinstance(tel, str):
            normalizados.append({
                'numero': tel,
                'tipo': '',
                'principal': False,
                'observacao': ''
            })
        elif isinstance(tel, dict):
            normalizados.append({
                'numero': tel.get('numero', tel.get('telefone', '')),
                'tipo': tel.get('tipo', ''),
                'principal': tel.get('principal', False),
                'observacao': tel.get('observacao', '')
            })
    
    return normalizados


def _normalizar_emails_fisgar(emails_brutos: List[Any]) -> List[Dict[str, Any]]:
    """Normaliza lista de e-mails do Fisgar."""
    normalizados = []
    
    for email in emails_brutos:
        if isinstance(email, str):
            normalizados.append({
                'endereco': email,
                'tipo': '',
                'principal': False
            })
        elif isinstance(email, dict):
            normalizados.append({
                'endereco': email.get('endereco', email.get('email', '')),
                'tipo': email.get('tipo', ''),
                'principal': email.get('principal', False)
            })
    
    return normalizados