#!/usr/bin/env python3
"""Script principal de orquestração para extração Captei."""

import sys
import argparse
import json
from pathlib import Path

# Adicionar diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

from captei import AgenteCaptei
from captei.extrator import processar_modal_captei, validar_dados_modal
from captei.persister import persistir_proprietario, consolidar_lote


def carregar_dados_tabela(caminho_json: Path) -> list:
    """Carrega dados de tabela de arquivo JSON."""
    with open(caminho_json, 'r', encoding='utf-8') as f:
        return json.load(f)


def inventariar_tabela(agente: AgenteCaptei, dados_tabela: list, endereco: str):
    """Inventaria tabela e cria manifest inicial."""
    print(f"Inventariando {len(dados_tabela)} registros...")
    
    for i, linha in enumerate(dados_tabela, 1):
        linha['endereco'] = endereco  # Adicionar endereço se não presente
        linha['source_line'] = i
        
        registro = agente.processar_linha_tabela(linha)
        if registro:
            registro['search_address_raw'] = endereco
            if registro.get('entity_type') == 'Pessoa Fisica':
                registro['state'] = 'pendente_modal'
            agente.adicionar_ao_manifest(registro)
            print(f"[{i}] {registro.get('name_raw', registro.get('entity_type'))} -> {registro.get('state')}")
    
    # Atualizar checkpoint
    agente.checkpoint_atual['address_canonical'] = endereco.lower().strip()
    agente.checkpoint_atual['address_raw'] = endereco
    agente.checkpoint_atual['state'] = 'inventariado'
    agente.salvar_checkpoint()
    
    counts = agente.checkpoint_atual['counts']
    print(f"\nInventário concluído:")
    print(f"  Total: {counts['manifest_total']}")
    print(f"  PF pendentes: {counts['pessoa_fisica_pending']}")
    print(f"  Empresas excluídas: {counts['companies_excluded']}")


def processar_pendentes(agente: AgenteCaptei, limite: int = None):
    """Processa registros pendentes do manifest."""
    print("\nProcessando registros pendentes...")
    
    processados = 0
    while True:
        if limite and processados >= limite:
            print(f"Limite de {limite} registros atingido.")
            break
        
        proximo = agente.obter_proximo_pendente()
        if not proximo:
            print("Não há mais registros pendentes.")
            break
        
        print(f"\nProcessando: {proximo.get('name_raw')}")
        
        # Simulação de processamento de modal
        # Na implementação real, aqui seria feita a extração via browser
        dados_modal_simulados = {
            'nome_completo': proximo.get('name_raw'),
            'papel': 'Proprietário',
            'endereco_retornado': proximo.get('address_raw'),
            'unidade': proximo.get('unit_raw'),
            'inscricao': '',
            'idade': None,
            'data_nascimento': None,
            'data_nascimento_ausente': True,
            'telefones': [
                {'numero': '(11) 99999-9999', 'tipo': 'Celular', 'whatsapp_status': 'nao_validado'}
            ],
            'emails': [
                {'endereco': 'exemplo@email.com', 'tipo': 'Principal'}
            ],
            'metodo_extracao': 'simulado',
            'modal_completo': True
        }
        
        # Processar dados do modal
        dados_processados = processar_modal_captei(dados_modal_simulados)
        
        # Validar consistência
        if not validar_dados_modal(dados_modal_simulados, proximo):
            print("  ⚠️  Dados do modal inconsistentes com manifest")
            agente.atualizar_estado_registro(
                proximo['record_key'],
                'wrong_modal_prevented'
            )
            continue
        
        # Persistir dados
        caminhos = persistir_proprietario(
            dados_processados,
            proximo,
            agente.estrutura,
            agente.nome_lote
        )
        
        print(f"  ✅ Persistido: {caminhos['json'].name}")
        
        # Atualizar estado
        agente.atualizar_estado_registro(
            proximo['record_key'],
            'resultado_persistido',
            dados_processados
        )
        
        processados += 1
    
    print(f"\nProcessamento concluído: {processados} registros")


def gerar_relatorio_final(agente: AgenteCaptei):
    """Gera relatório final de reconciliação."""
    relatorio = agente.gerar_relatorio_reconciliacao()
    
    relatorio_path = agente.estrutura['curated'] / f'reconciliacao_{agente.nome_lote}.md'
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        f.write(relatorio)
    
    print(f"\nRelatório salvo: {relatorio_path}")
    print("\n" + relatorio)


def main():
    parser = argparse.ArgumentParser(description='Script de extração Captei')
    parser.add_argument('--lote', required=True, help='Nome do lote')
    parser.add_argument('--endereco', required=True, help='Endereço para pesquisa')
    parser.add_argument('--dados', required=True, help='Arquivo JSON com dados da tabela')
    parser.add_argument('--limite', type=int, help='Limite de registros para processar')
    parser.add_argument('--apenas-inventario', action='store_true', 
                       help='Apenas inventariar, não processar')
    
    args = parser.parse_args()
    
    # Inicializar agente
    agente = AgenteCaptei('.', args.lote)
    
    # Carregar dados
    dados_tabela = carregar_dados_tabela(Path(args.dados))
    
    # Inventariar
    inventariar_tabela(agente, dados_tabela, args.endereco)
    
    # Processar se solicitado
    if not args.apenas_inventario:
        processar_pendentes(agente, args.limite)
        
        # Consolidar lote
        print("\nConsolidando lote...")
        consolidado = consolidar_lote(agente.estrutura, agente.nome_lote)
        print(f"Consolidado: {consolidado['total_registros']} registros")
        
        # Gerar relatório final
        gerar_relatorio_final(agente)
    else:
        print("\nInventário concluído. Use --limite para processar registros.")


if __name__ == '__main__':
    main()