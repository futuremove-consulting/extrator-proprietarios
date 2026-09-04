#!/usr/bin/env python3
"""CLI para consolidação multi-origem (Captei + Fisgar + EEmovel)."""

import sys
import argparse
import json
from pathlib import Path

# Adicionar diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

from comum.consolidation import consolidar_multi_origem, ConsolidationPipeline


def main():
    parser = argparse.ArgumentParser(description='Consolidação multi-origem de proprietários')
    parser.add_argument('--lote', required=True, help='Nome do lote para consolidação')
    parser.add_argument('--manifests-dir', default='.', help='Diretório base dos manifests (padrão: .)')
    parser.add_argument('--apenas-relatorio', action='store_true', 
                       help='Apenas gerar relatório, não salvar Golden Records')
    parser.add_argument('--output-dir', help='Diretório de saída personalizado')
    
    args = parser.parse_args()
    
    print(f"=== Consolidação Multi-Origem ===")
    print(f"Lote: {args.lote}")
    print(f"Manifests dir: {args.manifests_dir}")
    print()
    
    # Executar pipeline
    try:
        report = consolidar_multi_origem(args.lote, args.manifests_dir)
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Exibir resumo
    print(f"\n=== CONSOLIDAÇÃO CONCLUÍDA ===")
    print(f"Total Source Records: {report.total_source_records}")
    print(f"Total Golden Records: {report.total_golden_records}")
    print(f"  Multi-Origem: {report.golden_records_multi_origem}")
    print(f"  Single-Origem: {report.golden_records_single_origem}")
    print(f"Requer Revisão: {report.requires_review}")
    print(f"Distribuição Qualidade: {report.quality_distribution}")
    
    # Mostrar grupos de identidade
    if report.identity_groups:
        print(f"\nGrupos de Identidade ({len(report.identity_groups)}):")
        for i, g in enumerate(report.identity_groups, 1):
            print(f"  {i}. [{g['match_type']}] {g['confidence']:.0%} - {', '.join(g['sources'])}")
            print(f"     Nomes: {', '.join(g['names'])}")
    
    # Mostrar Golden Records que requerem revisão
    review_records = [g for g in report.golden_records if g.get('requires_review')]
    if review_records:
        print(f"\n⚠️  Golden Records que requerem revisão manual ({len(review_records)}):")
        for g in review_records:
            print(f"  - {g['golden_key']}: {g['nome']} ({g['match_type']}) - {g['quality']}")
    
    print(f"\nRelatório salvo em: {args.manifests_dir}/{args.lote}/consolidado/")
    print(f"  - golden_records_{args.lote}.json")
    print(f"  - relatorio_consolidacao_{args.lote}.md")


if __name__ == '__main__':
    main()