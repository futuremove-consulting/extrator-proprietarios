"""Módulo persister para Captei - responsável pela persistência de dados."""

from pathlib import Path
from typing import Dict, Any, Optional
import json

from comum import (
    salvar_json_seguro,
    timestamp_iso
)


def persistir_proprietario(dados_extraidos: Dict[str, Any], 
                           registro_manifest: Dict[str, Any],
                           estrutura: Dict[str, Path],
                           nome_lote: str) -> Dict[str, Path]:
    """
    Persiste dados de um proprietário em formato JSON e Markdown.
    
    Args:
        dados_extraidos: Dados processados do modal
        registro_manifest: Registro original do manifest
        estrutura: Estrutura de diretórios do lote
        nome_lote: Nome do lote
        
    Returns:
        Dicionário com caminhos dos arquivos criados
    """
    record_key = registro_manifest.get('record_key', 'unknown')
    nome_raw = registro_manifest.get('name_raw', 'unknown')
    
    # Criar nome seguro para arquivo
    nome_arquivo = _criar_nome_arquivo_seguro(nome_raw, record_key)
    
    # Consolidar dados
    registro_completo = {
        'record_key': record_key,
        'manifest': registro_manifest,
        'dados_extraidos': dados_extraidos,
        'metadata': {
            'lote': nome_lote,
            'timestamp_persistencia': timestamp_iso(),
            'versao_schema': '1.0'
        }
    }
    
    # Salvar JSON
    json_path = estrutura['curated'] / f'{nome_arquivo}.json'
    salvar_json_seguro(registro_completo, json_path)
    
    # Salvar Markdown
    md_path = estrutura['curated'] / f'{nome_arquivo}.md'
    markdown = _gerar_markdown_proprietario(registro_completo)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    # Salvar RAW adicional
    raw_path = estrutura['raw'] / f'{nome_arquivo}_raw.json'
    salvar_json_seguro({
        'manifest_raw': registro_manifest,
        'modal_raw': dados_extraidos.get('metadata', {})
    }, raw_path)
    
    return {
        'json': json_path,
        'markdown': md_path,
        'raw': raw_path
    }


def _criar_nome_arquivo_seguro(nome: str, record_key: str) -> str:
    """Cria nome de arquivo seguro a partir do nome e record_key."""
    # Remover caracteres inválidos para nome de arquivo
    nome_limpo = nome.replace('/', '-').replace('\\', '-').replace(':', '-')
    nome_limpo = nome_limpo.replace('*', '').replace('?', '').replace('"', '')
    nome_limpo = nome_limpo.replace('<', '').replace('>', '').replace('|', '')
    nome_limpo = nome_limpo.strip()
    
    # Limitar tamanho e adicionar key
    if len(nome_limpo) > 50:
        nome_limpo = nome_limpo[:50]
    
    return f"{nome_limpo}_{record_key}"


def _gerar_markdown_proprietario(registro: Dict[str, Any]) -> str:
    """Gera representação Markdown do proprietário."""
    manifest = registro.get('manifest', {})
    dados = registro.get('dados_extraidos', {})
    detalhes = dados.get('detalhes', {})
    telefones = dados.get('telefones', [])
    emails = dados.get('emails', [])
    metadata = dados.get('metadata', {})
    registro_metadata = registro.get('metadata', {})
    
    md = f"""# Proprietário: {manifest.get('name_raw', 'N/A')}

**Record Key:** {manifest.get('record_key', 'N/A')}  
**Unidade:** {manifest.get('unit_raw', 'N/A')}  
**Endereço:** {manifest.get('address_raw', 'N/A')}  
**Tipo:** {manifest.get('entity_type', 'N/A')}  
**Lote:** {registro_metadata.get('lote', 'N/A')}  

## Identificação

| Campo | Valor |
|-------|-------|
| Nome completo | {detalhes.get('nome_completo', 'N/A')} |
| Papel | {detalhes.get('papel', 'N/A')} |
| Inscrição | {detalhes.get('inscricao', 'N/A')} |
| Idade | {detalhes.get('idade', 'N/A')} |
| Data de nascimento | {detalhes.get('data_nascimento', 'N/A')} |
| Nascimento ausente | {detalhes.get('data_nascimento_ausente', False)} |

## Endereço

| Campo | Valor |
|-------|-------|
| Endereço retornado | {detalhes.get('endereco_retornado', 'N/A')} |
| Unidade | {detalhes.get('unidade', 'N/A')} |

## Telefones ({len(telefones)})

"""
    
    for i, tel in enumerate(telefones, 1):
        status_icon = '✅' if tel.get('validado') else '❌'
        md += f"{i}. {status_icon} {tel.get('numero_raw', 'N/A')} ({tel.get('tipo', 'N/A')})\n"
    
    md += f"\n## E-mails ({len(emails)})\n\n"
    
    for i, email in enumerate(emails, 1):
        status_icon = '✅' if email.get('valido') else '❌'
        md += f"{i}. {status_icon} {email.get('endereco_raw', 'N/A')} ({email.get('tipo', 'N/A')})\n"
    
    md += f"""
## Qualidade e Metadados

| Campo | Valor |
|-------|-------|
| Qualidade | {metadata.get('qualidade', 'N/A')} |
| Total telefones | {metadata.get('total_telefones', 0)} |
| Total e-mails | {metadata.get('total_emails', 0)} |
| WhatsApp validado | {metadata.get('whatsapp_validado', False)} |
| Tem nascimento | {metadata.get('tem_nascimento', False)} |
| Modal completo | {metadata.get('modal_completo', True)} |
| Método extração | {metadata.get('metodo_extracao', 'N/A')} |

## Timestamps

- Timestamp extração: {metadata.get('timestamp_extracao', 'N/A')}
- Timestamp persistência: {registro_metadata.get('timestamp_persistencia', 'N/A')}
- Estado: {manifest.get('state', 'N/A')}
- Estado timestamp: {manifest.get('state_timestamp', 'N/A')}

## RAW

- Endereço canônico: {manifest.get('address_canonical', 'N/A')}
- Unidade canônica: {manifest.get('unit_canonical', 'N/A')}
- Nome canônico: {manifest.get('name_canonical', 'N/A')}
"""
    
    return md


def atualizar_proprietario_existente(dados_atualizados: Dict[str, Any],
                                     record_key: str,
                                     estrutura: Dict[str, Path]) -> Optional[Dict[str, Path]]:
    """
    Atualiza dados de um proprietário já existente.
    
    Args:
        dados_atualizados: Novos dados para atualizar
        record_key: Chave do registro a atualizar
        estrutura: Estrutura de diretórios
        
    Returns:
        Caminhos dos arquivos atualizados ou None se não encontrado
    """
    # Buscar arquivo existente
    json_files = list(estrutura['curated'].glob(f'*_{record_key}.json'))
    
    if not json_files:
        return None
    
    json_path = json_files[0]
    md_path = json_path.with_suffix('.md')
    
    # Carregar dados existentes
    dados_existentes = json.loads(json_path.read_text(encoding='utf-8'))
    
    # Atualizar dados
    dados_existentes['dados_extraidos'].update(dados_atualizados)
    dados_existentes['metadata']['timestamp_atualizacao'] = timestamp_iso()
    
    # Salvar atualizações
    salvar_json_seguro(dados_existentes, json_path)
    
    # Recriar markdown
    markdown = _gerar_markdown_proprietario(dados_existentes)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    return {
        'json': json_path,
        'markdown': md_path
    }


def consolidar_lote(estrutura: Dict[str, Path], nome_lote: str) -> Dict[str, Any]:
    """
    Consolida todos os registros de um lote em arquivos sumarizados.
    
    Args:
        estrutura: Estrutura de diretórios do lote
        nome_lote: Nome do lote
        
    Returns:
        Dicionário com estatísticas da consolidação
    """
    json_files = list(estrutura['curated'].glob('*.json'))
    
    consolidado = {
        'lote': nome_lote,
        'timestamp_consolidacao': timestamp_iso(),
        'total_registros': len(json_files),
        'registros': [],
        'estatisticas': {
            'total_telefones': 0,
            'total_emails': 0,
            'whatsapp_validados': 0,
            'com_nascimento': 0,
            'qualidade_alta': 0,
            'qualidade_media': 0,
            'qualidade_baixa': 0
        }
    }
    
    for json_file in json_files:
        try:
            dados = json.loads(json_file.read_text(encoding='utf-8'))
            consolidado['registros'].append({
                'record_key': dados.get('record_key'),
                'nome': dados.get('manifest', {}).get('name_raw'),
                'estado': dados.get('manifest', {}).get('state'),
                'qualidade': dados.get('dados_extraidos', {}).get('metadata', {}).get('qualidade')
            })
            
            # Atualizar estatísticas
            dados_extraidos = dados.get('dados_extraidos', {})
            metadata = dados_extraidos.get('metadata', {})
            
            consolidado['estatisticas']['total_telefones'] += metadata.get('total_telefones', 0)
            consolidado['estatisticas']['total_emails'] += metadata.get('total_emails', 0)
            
            if metadata.get('whatsapp_validado'):
                consolidado['estatisticas']['whatsapp_validados'] += 1
            
            if metadata.get('tem_nascimento'):
                consolidado['estatisticas']['com_nascimento'] += 1
            
            qualidade = metadata.get('qualidade', '')
            if qualidade == 'alta':
                consolidado['estatisticas']['qualidade_alta'] += 1
            elif qualidade == 'media':
                consolidado['estatisticas']['qualidade_media'] += 1
            elif qualidade == 'baixa':
                consolidado['estatisticas']['qualidade_baixa'] += 1
                
        except Exception as e:
            print(f"Erro ao processar {json_file}: {e}")
    
    # Salvar consolidado
    consolidado_path = estrutura['curated'] / f'consolidado_{nome_lote}.json'
    salvar_json_seguro(consolidado, consolidado_path)
    
    return consolidado