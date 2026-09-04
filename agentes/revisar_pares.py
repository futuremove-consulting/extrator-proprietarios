#!/usr/bin/env python3
"""CLI: gera pares de revisao fuzzy (banda 0.75-0.92) a partir de manifests NDJSON.

Uso:
  python3 revisar_pares.py --manifesto captei=caminho.ndjson --manifesto fisgar=caminho.ndjson --saida pares_revisao.json
  python3 revisar_pares.py ... --decisoes decisoes.json   # aplica decisoes; gera grupos_revisados.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comum.identity_resolution import extrair_source_records
from comum.matching_revisao import (
    AUTO_MERGE_THRESHOLD,
    REVIEW_THRESHOLD,
    aplicar_decisoes,
    listar_pares,
)


def carregar_records(args):
    records = []
    for spec in args.manifesto:
        if "=" not in spec:
            print(f"ERRO: --manifesto espera origem=caminho, recebi: {spec}")
            sys.exit(2)
        origem, caminho = spec.split("=", 1)
        recs = extrair_source_records(caminho, origem)
        print(f"  {origem}: {len(recs)} registros PF carregados de {caminho}")
        records.extend(recs)
    return records


def par_para_json(p):
    return {
        "pair_id": p.pair_id,
        "classificacao": p.classificacao,
        "score": round(p.score, 4),
        "sim_nome": round(p.sim_nome, 4),
        "sim_unidade": round(p.sim_unidade, 4),
        "sim_endereco": round(p.sim_endereco, 4),
        "a": {"source": p.r1.source, "nome": p.r1.name_raw, "unidade": p.r1.unit_raw, "record_key": p.r1.record_key},
        "b": {"source": p.r2.source, "nome": p.r2.name_raw, "unidade": p.r2.unit_raw, "record_key": p.r2.record_key},
    }


def main():
    ap = argparse.ArgumentParser(description="Revisao fuzzy com banda (Estrategia Cascata - item 1)")
    ap.add_argument("--manifesto", action="append", required=True, help="origem=caminho do manifest NDJSON (repetivel)")
    ap.add_argument("--saida", required=True, help="arquivo JSON de saida dos pares")
    ap.add_argument("--decisoes", help="JSON opcional {pair_id: aceito|rejeitado}; gera grupos_revisados.json")
    args = ap.parse_args()

    print("Carregando manifests...")
    records = carregar_records(args)
    if len(records) < 2:
        print("Poucos registros para comparar.")
        return

    auto, revisao = listar_pares(records)
    print(f"Auto-merge (score >= {AUTO_MERGE_THRESHOLD}): {len(auto)} pares")
    print(f"Revisao ({REVIEW_THRESHOLD} <= score < {AUTO_MERGE_THRESHOLD}): {len(revisao)} pares")

    saida = {
        "parametros": {"auto_merge": AUTO_MERGE_THRESHOLD, "revisao_min": REVIEW_THRESHOLD},
        "resumo": {"registros": len(records), "pares_auto_merge": len(auto), "pares_revisao": len(revisao)},
        "auto_merge": [par_para_json(p) for p in auto],
        "revisao": [par_para_json(p) for p in revisao],
    }
    Path(args.saida).write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Pares salvos em {args.saida}")

    if args.decisoes:
        decisoes = json.loads(Path(args.decisoes).read_text(encoding="utf-8"))
        grupos, resumo = aplicar_decisoes(revisao, decisoes, auto=auto)
        print("Decisoes aplicadas: " + json.dumps(resumo, ensure_ascii=False))
        caminho_grupos = Path(args.saida).with_name("grupos_revisados.json")
        payload = {
            "resumo": resumo,
            "grupos": [
                {
                    "match_type": g.match_type,
                    "membros": [
                        {"source": m.source, "nome": m.name_raw, "unidade": m.unit_raw, "record_key": m.record_key}
                        for m in g.records
                    ],
                }
                for g in grupos
            ],
        }
        caminho_grupos.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Grupos revisados salvos em {caminho_grupos}")


if __name__ == "__main__":
    main()
