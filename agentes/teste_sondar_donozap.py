#!/usr/bin/env python3
"""Teste end-to-end da Sonda Dono do Zap (simulacao completa, sem tocar nos sistemas)."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIR = Path("/tmp/sondagem_donozap_teste")

falhas = 0


def check(nome, cond, detalhe=""):
    global falhas
    ok = bool(cond)
    falhas += 0 if ok else 1
    print("[%s] %s %s" % ("OK    " if ok else "FALHOU", nome, detalhe))


def run(*argv, expect=0):
    r = subprocess.run(
        [sys.executable, str(BASE / "sondar_donozap.py"), "--dir", str(DIR), *argv],
        capture_output=True, text=True,
    )
    check(
        "exit %d: %s" % (expect, " ".join(argv[:2])),
        r.returncode == expect,
        "" if r.returncode == expect else (r.stdout + r.stderr)[-300:],
    )
    return r


def main():
    shutil.rmtree(DIR, ignore_errors=True)

    # 0) medir sem sessao deve falhar
    run("medir", "--dominio", "com", "--numero-sufixo", "****1234", expect=1)

    # 1) iniciar
    run("iniciar", "--lote", "mar_chagall", "--operador", "agente_teste")

    # 2) sonda dominio .com: nome publico gratuito confirmado + PIX oferecido a R$ 4,90
    run("medir", "--dominio", "com", "--numero-sufixo", "****1234",
        "--nome-publico", "Paula Eleonora Cunha", "--foto-gratis", "false",
        "--pix-oferecido", "true", "--pix-valor", "4.90",
        "--tempo-segundos", "8", "--sigilo", "ui_afirma",
        "--observacao", "pesquisa gratuita retornou nome de exibicao")

    # 3) sonda dominio .com.br: sem retorno gratuito observado
    run("medir", "--dominio", "com_br", "--numero-sufixo", "****5678",
        "--nome-publico", "", "--foto-gratis", "nao_informado",
        "--pix-oferecido", "false", "--tempo-segundos", "15", "--sigilo", "nao_verificado")

    # 4) guard de privacidade: numero completo deve ser recusado
    run("medir", "--dominio", "com", "--numero-sufixo", "11949658369", expect=1)

    # 5) regra central: comparar nome do proprietario x nome publico (3 casos)
    for publico, esperado in (
        ("Paula Eleonora Cunha", "whatsapp_validado_publico"),
        ("Paula E Cunha", "ambiguo_revisao"),
        ("Ze das Couves", "nao_correspondente"),
    ):
        r = run("comparar",
                "--nome-proprietario", "PAULA ELEONORA DA CUNHA",
                "--nome-publico", publico, "--registrar")
        saida = json.loads(r.stdout)
        check("comparar %r -> %s" % (publico, esperado), saida["classificacao"] == esperado,
              "score=%s" % saida["score"])

    # 6) veredito por dominio
    run("veredito")
    ver = json.loads((DIR / "donozap_vereditos.json").read_text(encoding="utf-8"))
    vcom = ver["por_dominio"]["donodozap.com"]
    vbr = ver["por_dominio"]["donodozap.com.br"]
    check("veredito .com: nome_publico_gratis_confirmado", vcom["status"] == "nome_publico_gratis_confirmado")
    check("veredito .com: taxa 1.0", vcom["taxa_nome_publico"] == 1.0)
    check("veredito .com: pix R$ 4,90 observado", vcom["pix_valores_observados"] == [4.9])
    check("veredito .com.br: sem retorno gratuito", vbr["status"] == "sem_retorno_gratuito_revisar")
    check("veredito: recomendacao cita donodozap.com", "donodozap.com" in ver["recomendacao"])
    check("veredito: 3 comparacoes", ver["comparacoes_registradas"] == 3)
    check("veredito: distribuicao 1/1/1",
          ver["distribuicao_comparacoes"] == {
              "whatsapp_validado_publico": 1,
              "ambiguo_revisao": 1,
              "nao_correspondente": 1,
          })

    # 7) aplicar -> config da Fase 2
    run("aplicar")
    cfg = json.loads((DIR / "validacao_whatsapp_config.json").read_text(encoding="utf-8"))
    check("aplicar: dominio recomendado .com", cfg["dominio_recomendado"] == "donodozap.com")
    check("aplicar: escopo todos_os_leads", cfg["escopo_validacao"] == "todos_os_leads")
    check("aplicar: banda 0.92/0.75",
          cfg["regra_match"]["whatsapp_validado_publico"] == ">= 0.92"
          and cfg["regra_match"]["ambiguo_revisao"] == "0.75 a 0.92")
    check("aplicar: inicial de nome do meio vai para revisao",
          cfg["regra_match"]["inicial_nome_do_meio_vai_para_revisao"] is True)
    check("aplicar: 1 pendencia (com_br)", len(cfg["pendencias"]) == 1, json.dumps(cfg["pendencias"]))

    # 8) status
    r = run("status")
    check("status: 2 sondas + 3 comparacoes", "Sondas: 2 | Comparacoes: 3" in r.stdout)

    shutil.rmtree(DIR, ignore_errors=True)
    print("=== RESULTADO:", "TUDO OK" if falhas == 0 else "%d FALHAS" % falhas, "===")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
