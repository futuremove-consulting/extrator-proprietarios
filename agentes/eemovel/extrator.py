"""Módulo extrator específico para EEmovel."""

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


def processar_modal_eemovel(dados_modal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa dados extraídos do modal/detalhes do EEmovel.

    Args:
        dados_modal: Dados brutos extraídos da página de detalhes

    Returns:
        Registro estruturado com dados curados
    """
    registro = {
        'detalhes': {},
        'telefones': [],
        'emails': [],
        'enderecos_adicionais': [],
        'imovel_detalhes': {},
        'metadata': {}
    }

    # Processar detalhes principais do proprietário/morador
    registro['detalhes'] = {
        'nome_completo': dados_modal.get('nome_completo', ''),
        'tipo_pessoa': dados_modal.get('tipo_pessoa', ''),  # "Proprietário" ou "Possível morador"
        'endereco_principal': dados_modal.get('endereco_principal', ''),
        'unidade': dados_modal.get('unidade', ''),
        'inscricao': dados_modal.get('inscricao', ''),
        'idade': dados_modal.get('idade'),
        'data_nascimento': dados_modal.get('data_nascimento'),
        'cpf': dados_modal.get('cpf', ''),
        'rg': dados_modal.get('rg', ''),
        'obito': dados_modal.get('obito', False)
    }

    # Processar endereços adicionais (específico EEmovel)
    enderecos_adicionais = dados_modal.get('enderecos_adicionais', [])
    for end in enderecos_adicionais:
        if isinstance(end, str) and end.strip():
            registro['enderecos_adicionais'].append(end.strip())
        elif isinstance(end, dict):
            endereco_formatado = _formatar_endereco_adicional(end)
            if endereco_formatado:
                registro['enderecos_adicionais'].append(endereco_formatado)

    # Processar telefones
    telefones_brutos = dados_modal.get('telefones', [])
    telefones_processados = []

    for tel in telefones_brutos:
        numero = tel if isinstance(tel, str) else tel.get('numero', '')
        telefone_processado = {
            'numero_raw': numero,
            'digitos': extrair_digitos_telefone(numero),
            'tipo': tel.get('tipo', '') if isinstance(tel, dict) else '',
            'principal': tel.get('principal', False) if isinstance(tel, dict) else False
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
        endereco = email if isinstance(email, str) else email.get('endereco', '')
        email_processado = {
            'endereco_raw': endereco,
            'endereco_lower': endereco.lower().strip(),
            'valido': validar_email(endereco),
            'tipo': email.get('tipo', '') if isinstance(email, dict) else '',
            'principal': email.get('principal', False) if isinstance(email, dict) else False
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

    # Processar detalhes do imóvel (específico EEmovel)
    imovel = dados_modal.get('imovel', {})
    if imovel:
        registro['imovel_detalhes'] = {
            'ano_construcao': imovel.get('ano_construcao'),
            'edificio': imovel.get('edificio', ''),
            'padrao_construtivo': imovel.get('padrao_construtivo', ''),
            'uso_imovel': imovel.get('uso_imovel', ''),
            'tipo_terreno': imovel.get('tipo_terreno', ''),
            'area_terreno_m2': imovel.get('area_terreno_m2'),
            'area_construida_m2': imovel.get('area_construida_m2')
        }

    # Metadados da extração
    registro['metadata'] = {
        'timestamp_extracao': timestamp_iso(),
        'metodo_extracao': dados_modal.get('metodo_extracao', 'manual'),
        'modal_completo': dados_modal.get('modal_completo', True),
        'total_telefones': len(registro['telefones']),
        'total_emails': len(registro['emails']),
        'total_enderecos_adicionais': len(registro['enderecos_adicionais']),
        'tem_nascimento': bool(registro['detalhes']['data_nascimento']),
        'tem_cpf': bool(registro['detalhes']['cpf']),
        'tem_rg': bool(registro['detalhes']['rg']),
        'tem_dados_imovel': bool(registro['imovel_detalhes']),
        'qualidade': _calcular_qualidade_eemovel(registro)
    }

    return registro


def _formatar_endereco_adicional(end: Dict[str, Any]) -> str:
    """Formata endereço adicional do EEmovel."""
    partes = []
    for campo in ['logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep']:
        valor = end.get(campo, '').strip()
        if valor:
            partes.append(valor)
    return ', '.join(partes) if partes else ''


def _calcular_qualidade_eemovel(registro: Dict[str, Any]) -> str:
    """Calcula score de qualidade do registro extraído do EEmovel."""
    detalhes = registro.get('detalhes', {})
    telefones = registro.get('telefones', [])
    emails = registro.get('emails', [])
    enderecos_adicionais = registro.get('enderecos_adicionais', [])
    imovel = registro.get('imovel_detalhes', {})

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

    # CPF presente (específico EEmovel)
    if detalhes.get('cpf'):
        score += 1

    # RG presente
    if detalhes.get('rg'):
        score += 1

    # Endereços adicionais (riqueza de dados EEmovel)
    if enderecos_adicionais:
        score += 1

    # Dados do imóvel presentes
    if imovel.get('edificio') or imovel.get('area_construida_m2'):
        score += 1

    # Classificar qualidade (threshold maior que Fisgar pela riqueza de dados)
    if score >= 7:
        return 'alta'
    elif score >= 4:
        return 'media'
    else:
        return 'baixa'


def validar_dados_modal_eemovel(dados_modal: Dict[str, Any], registro_manifest: Dict[str, Any]) -> bool:
    """
    Valida se os dados do modal correspondem ao registro do manifest no EEmovel.

    Args:
        dados_modal: Dados extraídos do modal/detalhes
        registro_manifest: Registro do manifest original

    Returns:
        True se dados são consistentes, False caso contrário
    """
    nome_modal = dados_modal.get('nome_completo', '').upper().strip()
    nome_manifest = registro_manifest.get('name_raw', '').upper().strip()

    # Validação básica de nome
    if not _nomes_similares(nome_modal, nome_manifest):
        return False

    # Validar CPF se disponível em ambos
    cpf_modal = dados_modal.get('cpf', '').replace('.', '').replace('-', '').strip()
    cpf_manifest = registro_manifest.get('cpf', '').replace('.', '').replace('-', '').strip() if registro_manifest.get('cpf') else ''

    if cpf_modal and cpf_manifest:
        if cpf_modal != cpf_manifest:
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


def localizar_detalhes_por_linha(dados_linha: Dict[str, Any], selector_base: str = "tr") -> str:
    """
    Gera seletor CSS para localizar o botão/link de detalhes dentro de uma linha específica.
    EEmovel usa "Ver detalhes" ou similar.

    Args:
        dados_linha: Dados da linha da tabela
        selector_base: Seletor base (padrão: tr)

    Returns:
        Seletor CSS para o botão de detalhes
    """
    nome = dados_linha.get('nome', '')
    unidade = dados_linha.get('unidade', '')

    # Estratégia: buscar linha que contém nome e unidade, depois encontrar o botão detalhes
    selector = f'{selector_base}:has-text("{nome}")'
    if unidade:
        selector += f':has-text("{unidade}")'

    # Adicionar botão/link de detalhes - EEmovel pode ter variações
    selector += ' a:has-text("Detalhes"), button:has-text("Detalhes"), a:has-text("Ver"), button:has-text("Ver")'

    return selector


def extrair_dados_tabela_eemovel(linhas_html: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normaliza linhas brutas da tabela EEmovel para formato padrão.

    Args:
        linhas_html: Lista de dicionários com dados brutos de cada linha

    Returns:
        Lista normalizada pronta para processar_linha_tabela
    """
    normalizadas = []

    for linha in linhas_html:
        # EEmovel tem estrutura específica: nome, tipo_pessoa, endereco, unidade, etc.
        normalizada = {
            'nome': linha.get('nome', linha.get('proprietario', linha.get('morador', ''))),
            'tipo_pessoa': linha.get('tipo_pessoa', linha.get('tipo', 'Proprietário')),
            'endereco': linha.get('endereco', linha.get('endereco_completo', '')),
            'unidade': linha.get('unidade', linha.get('apartamento', '')),
            'source_line': linha.get('source_line'),
            'source_record_id': linha.get('source_record_id', linha.get('id')),
            'dom_reference': linha.get('dom_reference', linha.get('selector'))
        }
        normalizadas.append(normalizada)

    return normalizadas


def normalizar_dados_eemovel(dados_brutos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza dados brutos do EEmovel para formato padrão do modal.

    Args:
        dados_brutos: Dados brutos extraídos da página de detalhes

    Returns:
        Dados normalizados para processar_modal_eemovel
    """
    normalizado = {
        'nome_completo': dados_brutos.get('nome', dados_brutos.get('nome_completo', '')),
        'tipo_pessoa': dados_brutos.get('tipo_pessoa', dados_brutos.get('tipo', 'Proprietário')),
        'endereco_principal': dados_brutos.get('endereco_principal', dados_brutos.get('endereco_completo', '')),
        'unidade': dados_brutos.get('unidade', dados_brutos.get('apartamento', '')),
        'inscricao': dados_brutos.get('inscricao', ''),
        'idade': dados_brutos.get('idade'),
        'data_nascimento': dados_brutos.get('data_nascimento'),
        'cpf': dados_brutos.get('cpf', ''),
        'rg': dados_brutos.get('rg', ''),
        'obito': dados_brutos.get('obito', False),
        'telefones': _normalizar_telefones_eemovel(dados_brutos.get('telefones', [])),
        'emails': _normalizar_emails_eemovel(dados_brutos.get('emails', [])),
        'enderecos_adicionais': dados_brutos.get('enderecos_adicionais', []),
        'imovel': dados_brutos.get('imovel', {}),
        'metodo_extracao': dados_brutos.get('metodo', 'manual'),
        'modal_completo': dados_brutos.get('modal_completo', True)
    }

    return normalizado


def _normalizar_telefones_eemovel(telefones_brutos: List[Any]) -> List[Dict[str, Any]]:
    """Normaliza lista de telefones do EEmovel."""
    normalizados = []

    for tel in telefones_brutos:
        if isinstance(tel, str):
            normalizados.append({
                'numero': tel,
                'tipo': '',
                'principal': False
            })
        elif isinstance(tel, dict):
            normalizados.append({
                'numero': tel.get('numero', tel.get('telefone', tel.get('fone', ''))),
                'tipo': tel.get('tipo', tel.get('tipo_telefone', '')),
                'principal': tel.get('principal', tel.get('primario', False))
            })

    return normalizados


def _normalizar_emails_eemovel(emails_brutos: List[Any]) -> List[Dict[str, Any]]:
    """Normaliza lista de e-mails do EEmovel."""
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
                'endereco': email.get('endereco', email.get('email', email.get('e-mail', ''))),
                'tipo': email.get('tipo', email.get('tipo_email', '')),
                'principal': email.get('principal', False)
            })

    return normalizados