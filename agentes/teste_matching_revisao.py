#!/usr/bin/env python3
"""Smoke test do matching com banda de revisao (Estrategia Cascata - item 1)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from comum.identity_resolution import SourceRecord
from comum.matching_revisao import (
    AUTO_MERGE_THRESHOLD,
    REVIEW_THRESHOLD,
    avaliar_par,
    listar_pares,
    similaridade_unidades,
)


def rec(nome, unidade, source="captei", endereco="Rua Marc Chagall, 397", key=None):
    return SourceRecord(
        record_key=key or nome,
        source=source,
        source_record_id=nome,
        name_raw=nome,
        name_canonical=nome.lower(),
        unit_raw=unidade,
        unit_canonical=unidade.lower(),
        address_raw=endereco,
        address_canonical=endereco.lower(),
        entity_type="Pessoa Fisica",
        tipo_pessoa="Proprietario",
        cpf="",
        rg="",
        telefones=[],
        emails=[],
        enderecos_adicionais=[],
        data_nascimento="",
        idade=None,
        obito=False,
        imovel_detalhes={},
        whatsapp_status=None,
        quality="media",
        raw_payload={},
    )


CASOS = [
    ("abreviatura + unidade equivalente",
     rec("MARIA AP. DE SOUZA", "AP 22 E VG", "captei", key="k1"),
     rec("MARIA APARECIDA SOUZA", "APT 22", "fisgar", key="k2"),
     "auto_merge"),
    ("mesmo nome, unidade diferente",
     rec("JOSE SILVA", "AP 10", "captei", key="k3"),
     rec("JOSE SILVA", "AP 20", "fisgar", key="k4"),
     "revisao"),
    ("pessoas diferentes, mesma unidade",
     rec("PEDRO OLIVEIRA", "AP 30", "captei", key="k5"),
     rec("ANA SANTOS", "AP 30", "fisgar", key="k6"),
     "nao_merge"),
    ("registro identico em 2 fontes",
     rec("PAULA ELEONORA DA CUNHA", "AP 22 E VG", "captei", key="k7"),
     rec("PAULA ELEONORA DA CUNHA", "AP 22 E VG", "fisgar", key="k8"),
     "auto_merge"),
    ("inicial solta (S.) vai para revisao",
     rec("JOSE S. SILVA", "AP 44", "captei", key="k9"),
     rec("JOSE SOARES SILVA", "AP 44", "fisgar", key="k10"),
     "revisao"),
]


def main():
    print("=== Smoke test: matching com banda de revisao ===")
    falhas = 0
    for nome_caso, a, b, esperado in CASOS:
        aval = avaliar_par(a, b)
        ok = aval.classificacao == esperado
        falhas += 0 if ok else 1
        status = "OK    " if ok else "FALHOU"
        print(
            f"[{status}] {nome_caso}: score={aval.score:.3f} "
            f"(nome={aval.sim_nome:.3f} un={aval.sim_unidade:.3f} end={aval.sim_endereco:.3f}) "
            f"-> {aval.classificacao} (esperado: {esperado})"
        )

    sim = similaridade_unidades("AP 22 E VG 3", "VG 3 E AP 22")
    ok_ordem = sim >= 0.95
    falhas += 0 if ok_ordem else 1
    print(f"[{'OK    ' if ok_ordem else 'FALHOU'}] unidade com partes trocadas: sim={sim:.3f} (esperado >= 0.95)")

    assert AUTO_MERGE_THRESHOLD > REVIEW_THRESHOLD, "banda invertida"

    todos = [r for _, a, b, _ in CASOS for r in (a, b)]
    auto, revisao = listar_pares(todos)
    print(f"listar_pares sobre os 10 registros: {len(auto)} auto_merge, {len(revisao)} revisao")

    print("=== RESULTADO:", "TUDO OK" if falhas == 0 else f"{falhas} FALHAS", "===")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
