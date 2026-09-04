#!/usr/bin/env python3
"""Teste end-to-end do Sondador de Cotas (simulacao completa, sem tocar nos sistemas)."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIR = Path("/tmp/sondagem_teste")
ARQ_APROVACAO = Path("/tmp/aprovacao_teste.json")

falhas = 0


def check(nome, cond, detalhe=""):
    global falhas
    ok = bool(cond)
    falhas += 0 if ok else 1
    print("[%s] %s %s" % ("OK    " if ok else "FALHOU", nome, detalhe))


def run(*argv, expect=0):
    r = subprocess.run(
        [sys.executable, str(BASE / "sondar_cotas.py"), "--dir", str(DIR), *argv],
        capture_output=True, text=True,
    )
    check(
        "exit %d: %s" % (expect, " ".join(argv[:3])),
        r.returncode == expect,
        "" if r.returncode == expect else (r.stdout + r.stderr)[-300:],
    )
    return r


def main():
    shutil.rmtree(DIR, ignore_errors=True)
    ARQ_APROVACAO.write_text(
        json.dumps({"aprovado": True, "por": "leonardo", "escopo": "lote_teste"}),
        encoding="utf-8",
    )

    # 0) medir sem sessao deve falhar (exit 1)
    run("medir", "--pergunta", "P1", "--sistema", "captei", "--evento", "busca_listagem", expect=1)

    # 1) iniciar sessao
    run("iniciar", "--lote", "mar_chagall", "--operador", "agente_teste")

    # 2) P1: busca de listagem sem abrir consulta nos 3 sistemas (deltas 0)
    for sistema, saldo, cont in (("captei", 77, 0), ("fisgar", 0, 12), ("eemovel", 0, 100)):
        run("medir", "--pergunta", "P1", "--sistema", sistema, "--evento", "busca_listagem",
            "--tipo-saldo", "capcoins" if sistema == "captei" else "consultas",
            "--saldo-antes", str(saldo), "--saldo-depois", str(saldo),
            "--contador-antes", str(cont), "--contador-depois", str(cont))

    # 3) P2: 1 consulta Captei — saldo 77 -> 76, contador mensal imovel (pre-pago)
    run("medir", "--pergunta", "P2", "--sistema", "captei", "--evento", "consulta_detalhe",
        "--tipo-saldo", "capcoins", "--saldo-antes", "77", "--saldo-depois", "76",
        "--contador-antes", "3", "--contador-depois", "3",
        "--pago", "--aprovacao", str(ARQ_APROVACAO), "--observacao", "modal paula cunha ap 22")

    # 4) P3: 1 detalhe EEmovel — contador 100 -> 101 e moradores vieram juntos
    run("medir", "--pergunta", "P3", "--sistema", "eemovel", "--evento", "consulta_detalhe",
        "--tipo-saldo", "consultas", "--contador-antes", "100", "--contador-depois", "101",
        "--moradores-inclusos", "true", "--pago", "--aprovacao", str(ARQ_APROVACAO))

    # 5) P4: 1 modal Fisgar — contador 12 -> 13
    run("medir", "--pergunta", "P4", "--sistema", "fisgar", "--evento", "consulta_modal",
        "--tipo-saldo", "consultas", "--contador-antes", "12", "--contador-depois", "13",
        "--pago", "--aprovacao", str(ARQ_APROVACAO))

    # 6) P5 teste negativo: evento pago SEM aprovacao deve ser BLOQUEADO (exit 2)
    run("medir", "--pergunta", "P5", "--sistema", "captei", "--evento", "validar_whatsapp",
        "--pago", expect=2)

    # 7) veredito
    run("veredito")
    ver = json.loads((DIR / "vereditos.json").read_text(encoding="utf-8"))

    p1 = ver["P1_listagem_gratuita"]
    check("P1: 3 sistemas gratuitos", all(p1[s] == "gratuita" for s in ("captei", "fisgar", "eemovel")), json.dumps(p1))

    p2 = ver["P2_captei_modalidade"]
    check("P2: pre_pago_capcoins", p2["modalidade"] == "pre_pago_capcoins")
    check("P2: plano 500/mes invalido p/ consultas", p2["plano_500_mes_valido_para_consultas"] is False)
    check("P2: saldo atual 76", p2["saldo_atual_apos_sondagem"] == 76)

    p3 = ver["P3_eemovel_escopo"]
    check("P3: perfil_completo_1_consulta", p3["escopo"] == "perfil_completo_1_consulta")
    check("P3: custo 1 por proprietario", p3["custo_por_proprietario"] == 1)

    p4 = ver["P4_fisgar_modal"]
    check("P4: 1 modal = 1/250", p4["custo_por_modal"] == 1 and p4["modalidade"] == "cota_mensal_250")

    p5 = ver["P5_guard_rail"]
    check("P5: ativo_e_validado", p5["conclusao"] == "ativo_e_validado")
    check("P5: 1 bloqueio + 1 pago aprovado",
          p5["tentativas_bloqueadas"] == 1 and p5["eventos_pagos_aprovados"] == 3)

    # 8) aplicar -> custos_verificados.json sem pendencias
    run("aplicar")
    custos = json.loads((DIR / "custos_verificados.json").read_text(encoding="utf-8"))
    check("aplicar: eemovel custo 1", custos["sistemas"]["eemovel"]["custo_por_proprietario"] == 1)
    check("aplicar: fisgar custo 1", custos["sistemas"]["fisgar"]["custo_por_modal"] == 1)
    check("aplicar: captei limite = saldo_capcoins",
          custos["sistemas"]["captei"]["limite_mes_efetivo"] == "saldo_capcoins")
    check("aplicar: sem avisos pendentes", custos["avisos"] == [], json.dumps(custos["avisos"]))
    check("aplicar: ordem cascata", custos["ordem_cascata"] == ["eemovel", "fisgar", "captei"])

    # 9) status
    r = run("status")
    check("status: lista 7 medicoes", "Medicoes: 7" in r.stdout)

    shutil.rmtree(DIR, ignore_errors=True)
    ARQ_APROVACAO.unlink(missing_ok=True)
    print("=== RESULTADO:", "TUDO OK" if falhas == 0 else "%d FALHAS" % falhas, "===")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
