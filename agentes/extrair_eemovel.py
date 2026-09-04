#!/usr/bin/env python3
"""Script principal de orquestração para extração EEmovel."""

import sys
import argparse
import json
from pathlib import Path

# Adicionar diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

from eemovel import AgenteEEmovel
from eemovel.extrator import processar_modal_eemovel, validar_dados_modal_eemovel
from eemovel.persister import persistir_proprietario, consolidar_lote


def carregar_dados_tabela(caminho_json: Path) -> list:
    """Carrega dados de tabela de arquivo JSON."""
    with open(caminho_json, 'r', encoding='utf-8') as f:
        return json.load(f)


def inventariar_tabela(agente: AgenteEEmovel, dados_tabela: list, endereco: str,
                       numero_inicial: int, numero_final: int = None):
    """Inventaria tabela e cria manifest inicial."""
    print(f"Inventariando {len(dados_tabela)} registros...")
    print(f"Endereço: {endereco} | Número inicial: {numero_inicial} | Número final: {numero_final or 'N/A'}")

    for i, linha in enumerate(dados_tabela, 1):
        linha['endereco'] = endereco  # Adicionar endereço se não presente
        linha['source_line'] = i

        registro = agente.processar_linha_tabela(linha)
        if registro:
            registro['search_address_raw'] = endereco
            agente.adicionar_ao_manifest(registro)
            print(f"[{i}] {registro.get('name_raw', registro.get('entity_type'))} -> {registro.get('state')} ({registro.get('tipo_pessoa', 'N/A')})")

    # Atualizar checkpoint
    agente.checkpoint_atual['address_canonical'] = endereco.lower().strip()
    agente.checkpoint_atual['address_raw'] = endereco
    agente.checkpoint_atual['number_from'] = numero_inicial
    agente.checkpoint_atual['number_to'] = numero_final
    agente.checkpoint_atual['state'] = 'inventariado'
    agente.salvar_checkpoint()

    counts = agente.checkpoint_atual['counts']
    print(f"\nInventário concluído:")
    print(f"  Total: {counts['manifest_total']}")
    print(f"  Proprietários PF pendentes: {counts['pessoa_fisica_pending']}")
    print(f"  Moradores: {counts['moradores']}")
    print(f"  Empresas excluídas: {counts['empresas_excluidas']}")
    print(f"  Revisão manual: {counts['revisao_manual']}")


def processar_pendentes(agente: AgenteEEmovel, limite: int = None,
                        processar_moradores: bool = False):
    """Processa registros pendentes do manifest (proprietários e opcionalmente moradores)."""
    print("\nProcessando proprietários pendentes...")

    processados = 0
    while True:
        if limite and processados >= limite:
            print(f"Limite de {limite} registros atingido.")
            break

        proximo = agente.obter_proximo_pendente()
        if not proximo:
            print("Não há mais proprietários pendentes.")
            break

        print(f"\nProcessando: {proximo.get('name_raw')} ({proximo.get('tipo_pessoa')})")

        # Simulação de processamento de modal/detalhes
        # Na implementação real, aqui seria feita a extração via browser
        dados_modal_simulados = {
            'nome_completo': proximo.get('name_raw'),
            'tipo_pessoa': proximo.get('tipo_pessoa', 'Proprietário'),
            'endereco_principal': proximo.get('address_raw'),
            'unidade': proximo.get('unit_raw'),
            'inscricao': '',
            'idade': None,
            'data_nascimento': None,
            'cpf': '',
            'rg': '',
            'obito': False,
            'telefones': [
                {'numero': '(11) 99999-9999', 'tipo': 'Celular', 'principal': True}
            ],
            'emails': [
                {'endereco': 'exemplo@email.com', 'tipo': 'Principal', 'principal': True}
            ],
            'enderecos_adicionais': [],
            'imovel': {
                'ano_construcao': 2015,
                'edificio': 'CONDOMINIO RECANTO JACARANDA',
                'padrao_construtivo': 'Residencial Vertical Padrão D',
                'uso_imovel': 'Apartamento Em Condomínio',
                'tipo_terreno': 'Normal',
                'area_terreno_m2': 8254,
                'area_construida_m2': 174
            },
            'metodo_extracao': 'simulado',
            'modal_completo': True
        }

        # Processar dados do modal
        dados_processados = processar_modal_eemovel(dados_modal_simulados)

        # Validar consistência
        if not validar_dados_modal_eemovel(dados_modal_simulados, proximo):
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

        # Salvar checkpoint com posição de scroll simulada
        agente.salvar_checkpoint_com_scroll(scroll_position=processados * 100, creditos=547 - processados)

        processados += 1

    # Processar moradores se solicitado
    if processar_moradores:
        print("\nProcessando moradores (opcional)...")
        moradores_processados = 0
        while True:
            proximo = agente.obter_proximo_morador()
            if not proximo:
                print("Não há mais moradores pendentes.")
                break

            print(f"\nProcessando morador: {proximo.get('name_raw')}")

            # Para moradores, apenas persistir dados básicos (simulado)
            dados_modal_morador = {
                'nome_completo': proximo.get('name_raw'),
                'tipo_pessoa': 'Possível morador',
                'endereco_principal': proximo.get('address_raw'),
                'unidade': proximo.get('unit_raw'),
                'inscricao': '',
                'idade': None,
                'data_nascimento': None,
                'cpf': '',
                'rg': '',
                'obito': False,
                'telefones': [],
                'emails': [],
                'enderecos_adicionais': [],
                'imovel': {},
                'metodo_extracao': 'simulado',
                'modal_completo': True
            }

            dados_processados = processar_modal_eemovel(dados_modal_morador)
            caminhos = persistir_proprietario(
                dados_processados,
                proximo,
                agente.estrutura,
                agente.nome_lote
            )
            print(f"  ✅ Persistido: {caminhos['json'].name}")

            agente.atualizar_estado_registro(
                proximo['record_key'],
                'resultado_persistido',
                dados_processados
            )

            moradores_processados += 1

        print(f"\nMoradores processados: {moradores_processados}")

    print(f"\nProcessamento concluído: {processados} proprietários")


def gerar_relatorio_final(agente: AgenteEEmovel):
    """Gera relatório final de reconciliação."""
    relatorio = agente.gerar_relatorio_reconciliacao()

    relatorio_path = agente.estrutura['curated'] / f'reconciliacao_{agente.nome_lote}.md'
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        f.write(relatorio)

    print(f"\nRelatório salvo: {relatorio_path}")
    print("\n" + relatorio)


def main():
    parser = argparse.ArgumentParser(description='Script de extração EEmovel')
    parser.add_argument('--lote', required=True, help='Nome do lote')
    parser.add_argument('--endereco', required=True, help='Endereço base para pesquisa (ex: "Rua Marc Chagall")')
    parser.add_argument('--numero-inicial', type=int, required=True, help='Número inicial (ex: 397)')
    parser.add_argument('--numero-final', type=int, help='Número final (opcional, ex: 497)')
    parser.add_argument('--dados', required=True, help='Arquivo JSON com dados da tabela')
    parser.add_argument('--limite', type=int, help='Limite de proprietários para processar')
    parser.add_argument('--processar-moradores', action='store_true',
                       help='Também processar moradores (Possível morador)')
    parser.add_argument('--apenas-inventario', action='store_true',
                       help='Apenas inventariar, não processar')

    args = parser.parse_args()

    # Inicializar agente
    agente = AgenteEEmovel('.', args.lote)

    # Carregar dados
    dados_tabela = carregar_dados_tabela(Path(args.dados))

    # Inventariar
    inventariar_tabela(agente, dados_tabela, args.endereco, args.numero_inicial, args.numero_final)

    # Processar se solicitado
    if not args.apenas_inventario:
        processar_pendentes(agente, args.limite, args.processar_moradores)

        # Consolidar lote
        print("\nConsolidando lote...")
        consolidado = consolidar_lote(agente.estrutura, agente.nome_lote)
        print(f"Consolidado: {consolidado['total_registros']} registros")
        print(f"  Proprietários: {consolidado['estatisticas']['proprietarios']}")
        print(f"  Moradores: {consolidado['estatisticas']['moradores']}")
        print(f"  Qualidade alta: {consolidado['estatisticas']['qualidade_alta']}")
        print(f"  Qualidade média: {consolidado['estatisticas']['qualidade_media']}")
        print(f"  Qualidade baixa: {consolidado['estatisticas']['qualidade_baixa']}")

        # Gerar relatório final
        gerar_relatorio_final(agente)
    else:
        print("\nInventário concluído. Use --limite para processar proprietários.")


if __name__ == '__main__':
    main()