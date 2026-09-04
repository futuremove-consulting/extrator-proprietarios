"""Módulo persister para EEmovel - responsável pela persistência de dados."""

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
    Persiste dados de um proprietário/morador em formato JSON e Markdown.

    Args:
        dados_extraidos: Dados processados do modal/detalhes
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
            'versao_schema': '1.0',
            'sistema_origem': 'eemovel'
        }
    }

    # Salvar JSON
    json_path = estrutura['curated'] / f'{nome_arquivo}.json'
    salvar_json_seguro(registro_completo, json_path)

    # Salvar Markdown
    md_path = estrutura['curated'] / f'{nome_arquivo}.md'
    markdown = _gerar_markdown_proprietario_eemovel(registro_completo)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    # Salvar RAW adicional
    raw_path = estrutura['raw'] / f'{nome_arquivo}_raw.json'
    salvar_json_seguro({
        'manifest_raw': registro_manifest,
        'modal_raw': dados_extraidos.get('metadata', {}),
        'dom_reference': registro_manifest.get('dom_reference')
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


def _gerar_markdown_proprietario_eemovel(registro: Dict[str, Any]) -> str:
    """Gera representação Markdown do proprietário/morador do EEmovel."""
    manifest = registro.get('manifest', {})
    dados = registro.get('dados_extraidos', {})
    detalhes = dados.get('detalhes', {})
    telefones = dados.get('telefones', [])
    emails = dados.get('emails', [])
    enderecos_adicionais = dados.get('enderecos_adicionais', [])
    imovel = dados.get('imovel_detalhes', {})
    metadata = dados.get('metadata', {})
    registro_metadata = registro.get('metadata', {})

    tipo_pessoa = manifest.get('tipo_pessoa', 'Proprietário')
    tipo_label = "Morador" if tipo_pessoa == "Possível morador" else "Proprietário"

    md = f"""# {tipo_label}: {manifest.get('name_raw', 'N/A')} (EEmovel)

**Record Key:** {manifest.get('record_key', 'N/A')}
**Tipo:** {tipo_pessoa}
**Unidade:** {manifest.get('unit_raw', 'N/A')}
**Endereço Principal:** {manifest.get('address_raw', 'N/A')}
**Entidade:** {manifest.get('entity_type', 'N/A')}
**Lote:** {registro_metadata.get('lote', 'N/A')}
**Sistema origem:** {registro_metadata.get('sistema_origem', 'N/A')}

## Identificação

| Campo | Valor |
|-------|-------|
| Nome completo | {detalhes.get('nome_completo', 'N/A')} |
| Tipo pessoa | {detalhes.get('tipo_pessoa', 'N/A')} |
| Inscrição | {detalhes.get('inscricao', 'N/A')} |
| CPF | {detalhes.get('cpf', 'N/A')} |
| RG | {detalhes.get('rg', 'N/A')} |
| Idade | {detalhes.get('idade', 'N/A')} |
| Data de nascimento | {detalhes.get('data_nascimento', 'N/A')} |
| Óbito | {detalhes.get('obito', False)} |

## Endereços

### Endereço Principal
| Campo | Valor |
|-------|-------|
| Endereço | {detalhes.get('endereco_principal', 'N/A')} |
| Unidade | {detalhes.get('unidade', 'N/A')} |

### Endereços Adicionais ({len(enderecos_adicionais)})

"""

    for i, end in enumerate(enderecos_adicionais, 1):
        md += f"{i}. {end}\n"

    md += f"""
## Imóvel (Detalhes EEmovel)

| Campo | Valor |
|-------|-------|
| Edifício | {imovel.get('edificio', 'N/A')} |
| Ano de construção | {imovel.get('ano_construcao', 'N/A')} |
| Padrão construtivo | {imovel.get('padrao_construtivo', 'N/A')} |
| Uso do imóvel | {imovel.get('uso_imovel', 'N/A')} |
| Tipo de terreno | {imovel.get('tipo_terreno', 'N/A')} |
| Área do terreno | {imovel.get('area_terreno_m2', 'N/A')} m² |
| Área construída | {imovel.get('area_construida_m2', 'N/A')} m² |

## Telefones ({len(telefones)})

"""

    for i, tel in enumerate(telefones, 1):
        principal_icon = '⭐' if tel.get('principal') else ''
        md += f"{i}. {principal_icon} {tel.get('numero_raw', 'N/A')} ({tel.get('tipo', 'N/A')})\n"

    md += f"\n## E-mails ({len(emails)})\n\n"

    for i, email in enumerate(emails, 1):
        principal_icon = '⭐' if email.get('principal') else ''
        status_icon = '✅' if email.get('valido') else '❌'
        md += f"{i}. {principal_icon} {status_icon} {email.get('endereco_raw', 'N/A')} ({email.get('tipo', 'N/A')})\n"

    md += f"""
## Qualidade e Metadados

| Campo | Valor |
|-------|-------|
| Qualidade | {metadata.get('qualidade', 'N/A')} |
| Total telefones | {metadata.get('total_telefones', 0)} |
| Total e-mails | {metadata.get('total_emails', 0)} |
| Endereços adicionais | {metadata.get('total_enderecos_adicionais', 0)} |
| Tem nascimento | {metadata.get('tem_nascimento', False)} |
| Tem CPF | {metadata.get('tem_cpf', False)} |
| Tem RG | {metadata.get('tem_rg', False)} |
| Tem dados imóvel | {metadata.get('tem_dados_imovel', False)} |
| Modal completo | {metadata.get('modal_completo', True)} |
| Método extração | {metadata.get('metodo_extracao', 'N/A')} |

## Timestamps

- Timestamp extração: {metadata.get('timestamp_extracao', 'N/A')}
- Timestamp persistência: {registro_metadata.get('timestamp_persistencia', 'N/A')}
- Estado: {manifest.get('state', 'N/A')}
- Estado timestamp: {manifest.get('state_timestamp', 'N/A')}

## RAW e DOM

- Endereço canônico: {manifest.get('address_canonical', 'N/A')}
- Unidade canônica: {manifest.get('unit_canonical', 'N/A')}
- Nome canônico: {manifest.get('name_canonical', 'N/A')}
- Referência DOM: {manifest.get('dom_reference', 'N/A')}
"""

    return md


def atualizar_proprietario_existente(dados_atualizados: Dict[str, Any],
                                     record_key: str,
                                     estrutura: Dict[str, Path]) -> Optional[Dict[str, Path]]:
    """
    Atualiza dados de um proprietário/morador já existente.

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
    markdown = _gerar_markdown_proprietario_eemovel(dados_existentes)
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
        'sistema_origem': 'eemovel',
        'registros': [],
        'estatisticas': {
            'total_telefones': 0,
            'total_emails': 0,
            'total_enderecos_adicionais': 0,
            'com_nascimento': 0,
            'com_cpf': 0,
            'com_rg': 0,
            'com_dados_imovel': 0,
            'proprietarios': 0,
            'moradores': 0,
            'qualidade_alta': 0,
            'qualidade_media': 0,
            'qualidade_baixa': 0
        }
    }

    for json_file in json_files:
        try:
            dados = json.loads(json_file.read_text(encoding='utf-8'))
            manifest = dados.get('manifest', {})
            dados_extraidos = dados.get('dados_extraidos', {})
            metadata = dados_extraidos.get('metadata', {})

            tipo_pessoa = manifest.get('tipo_pessoa', 'Proprietário')
            if tipo_pessoa == 'Possível morador':
                consolidado['estatisticas']['moradores'] += 1
            else:
                consolidado['estatisticas']['proprietarios'] += 1

            consolidado['registros'].append({
                'record_key': dados.get('record_key'),
                'nome': manifest.get('name_raw'),
                'tipo_pessoa': tipo_pessoa,
                'estado': manifest.get('state'),
                'qualidade': metadata.get('qualidade')
            })

            # Atualizar estatísticas
            consolidado['estatisticas']['total_telefones'] += metadata.get('total_telefones', 0)
            consolidado['estatisticas']['total_emails'] += metadata.get('total_emails', 0)
            consolidado['estatisticas']['total_enderecos_adicionais'] += metadata.get('total_enderecos_adicionais', 0)

            if metadata.get('tem_nascimento'):
                consolidado['estatisticas']['com_nascimento'] += 1

            if metadata.get('tem_cpf'):
                consolidado['estatisticas']['com_cpf'] += 1

            if metadata.get('tem_rg'):
                consolidado['estatisticas']['com_rg'] += 1

            if metadata.get('tem_dados_imovel'):
                consolidado['estatisticas']['com_dados_imovel'] += 1

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