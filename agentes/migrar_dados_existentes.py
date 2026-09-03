#!/usr/bin/env python3
"""Script para migrar dados extraídos anteriormente para o novo formato."""

import sys
import json
from pathlib import Path

# Adicionar diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

from captei import AgenteCaptei
from fisgar import AgenteFisgar
from comum import (
    criar_estrutura_lote,
    salvar_json_seguro,
    timestamp_iso
)


def migrar_captei_parcial(caminho_json: Path, nome_lote: str = "captei_migrado"):
    """Migra dados do JSON parcial do Captei para o novo formato."""
    print(f"Migrando dados do Captei de {caminho_json}...")
    
    # Carregar dados existentes
    with open(caminho_json, 'r', encoding='utf-8') as f:
        dados_originais = json.load(f)
    
    # Criar estrutura para lote migrado
    estrutura = criar_estrutura_lote(nome_lote, '.')
    
    # Criar agente
    agente = AgenteCaptei('.', nome_lote)
    
    # Processar cada registro
    registros_migrados = 0
    for record in dados_originais.get('records', []):
        # Converter para formato do novo sistema
        registro_novo = {
            'record_key': record.get('record_key'),
            'name_raw': record.get('name_raw'),
            'name_canonical': record.get('name_canonical'),
            'unit_raw': record.get('unit_raw'),
            'unit_canonical': record.get('unit_canonical'),
            'address_raw': dados_originais.get('lote', ''),
            'address_canonical': record.get('search_address_canonical'),
            'entity_type': record.get('entity_type'),
            'state': 'resultado_persistido',  # Já foi processado
            'timestamp': timestamp_iso(),
            'source_system': record.get('source_system'),
            'data_nascimento': record.get('birth_date'),
            'idade': record.get('age_raw'),
            'inscricao': record.get('inscricao_raw'),
            'telefones': record.get('phones', []),
            'emails': record.get('emails', []),
            'metadata': {
                'migrado': True,
                'data_migracao': timestamp_iso(),
                'origem': caminho_json.name
            }
        }
        
        # Adicionar ao manifest
        agente.adicionar_ao_manifest(registro_novo)
        
        # Salvar arquivo individual
        nome_arquivo = f"{record.get('name_raw', 'unknown')}_{record.get('record_key', 'unknown')}"
        nome_arquivo = nome_arquivo.replace('/', '-').replace('\\', '-').replace(':', '-')
        
        json_path = estrutura['curated'] / f'{nome_arquivo}.json'
        salvar_json_seguro(registro_novo, json_path)
        
        registros_migrados += 1
        print(f"  [{registros_migrados}] {record.get('name_raw')}")
    
    # Atualizar checkpoint
    agente.checkpoint_atual['state'] = 'migrado'
    agente.checkpoint_atual['counts']['pessoa_fisica_completed'] = registros_migrados
    agente.checkpoint_atual['counts']['pessoa_fisica_pending'] = 0
    agente.salvar_checkpoint()
    
    print(f"\nMigração concluída: {registros_migrados} registros")
    print(f"Lote migrado: {nome_lote}")
    print(f"Estrutura criada em: {estrutura['base']}")
    
    return estrutura


def criar_lote_teste_com_dados_reais():
    """Cria um lote de teste usando dados reais extraídos anteriormente."""
    caminho_captei = Path("/home/rochagus/projetos-linux/extrator-proprietarios/extracted/Base Proprietários/Captei_Parcial_2026-09-03_PF/captei_pf_partial.json")
    
    if caminho_captei.exists():
        print("Arquivo de dados Captei encontrado. Criando lote de migração...")
        estrutura = migrar_captei_parcial(caminho_captei, "captei_migrado_teste")
        return estrutura
    else:
        print("Arquivo de dados Captei não encontrado.")
        return None


def main():
    print("=== Script de Migração de Dados Existentes ===\n")
    
    # Criar lote de teste com dados reais
    estrutura = criar_lote_teste_com_dados_reais()
    
    if estrutura:
        print(f"\nEstrutura criada: {estrutura['base']}")
        print(f"Manifest: {estrutura['manifest']}")
        print(f"Curated: {estrutura['curated']}")
        print(f"Checkpoints: {estrutura['checkpoints']}")
        print(f"Logs: {estrutura['logs']}")
        print(f"Raw: {estrutura['raw']}")


if __name__ == '__main__':
    main()