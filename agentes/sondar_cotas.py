#!/usr/bin/env python3
"""Sondador de Cotas — verificacao empirica das regras de custo (Captei, Fisgar, EEmovel).

Transforma as 5 perguntas abertas da Estrategia de Cascata em um PROTOCOLO DE
MEDICAO antes/depois com veredito automatico e guard-rail de aprovacao humana.

Perguntas respondidas com evidencia:
  P1  A listagem por endereco consome credito? (premissa do usuario: SIM, 1 credito por busca por sistema)
  P2  Captei: a cota real e o saldo de capcoins ou renovacao mensal (500/mes)?
  P3  EEmovel: 1 consulta cobre o perfil completo (moradores inclusos)?
  P4  Fisgar: cada modal 'Consultar' custa 1 das 250/mes?
  P5  Guard-rail: nenhum evento pago acontece sem aprovacao humana?

Uso tipico (protocolo manual assistido, ~15 min por sistema):
  python3 sondar_cotas.py iniciar --lote mar_chagall --operador leonardo
  # P1: busque o endereco SEM abrir consulta (premissa: consome 1 credito); informe saldo/contador antes e depois
  python3 sondar_cotas.py medir --pergunta P1 --sistema captei --evento busca_listagem       --tipo-saldo capcoins --saldo-antes 77 --saldo-depois 76       --contador-antes 0 --contador-depois 0
  # P2/P3/P4: abra 1 consulta por sistema (COM aprovacao registrada)
  python3 sondar_cotas.py medir --pergunta P2 --sistema captei --evento consulta_detalhe       --tipo-saldo capcoins --saldo-antes 77 --saldo-depois 76       --contador-antes 3 --contador-depois 3 --pago --aprovacao aprovacao.json
  python3 sondar_cotas.py veredito
  python3 sondar_cotas.py aplicar   # gera custos_verificados.json para o orquestrador

Guard-rail (P5): todo evento --pago exige --aprovacao arquivo.json com
  {"aprovado": true, "por": "nome", "escopo": "lote"}. Sem aprovacao valida o
  evento e BLOQUEADO e a tentativa fica registrada como evidencia de auditoria.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIR_PADRAO = BASE / "sondagem"

PERGUNTAS = {
    "P1": "Listagem por endereco consome credito? Quanto por sistema? (usuario: 1 credito por busca)",
    "P2": "Captei: cota real = saldo de capcoins ou renovacao mensal (500/mes)?",
    "P3": "EEmovel: 1 consulta cobre perfil completo (moradores inclusos)?",
    "P4": "Fisgar: cada modal Consultar custa 1 das 250/mes?",
    "P5": "Guard-rail: aprovacao humana obrigatoria antes de lote pago?",
}
EVENTOS_VALIDOS = {"busca_listagem", "consulta_detalhe", "consulta_modal", "validar_whatsapp"}
SISTEMAS_VALIDOS = ("captei", "fisgar", "eemovel")
MORADORES_MAP = {"true": True, "false": False, "nao_sei": None, "nao_informado": None}


def agora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def caminho(dir_sondagem: Path, nome: str) -> Path:
    return dir_sondagem / nome


def carregar_json_ou(arq: Path, padrao):
    if not arq.exists():
        return padrao
    return json.loads(arq.read_text(encoding="utf-8"))


def carregar_medicoes(dir_sondagem: Path):
    arq = caminho(dir_sondagem, "medicoes.ndjson")
    if not arq.exists():
        return []
    return [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines() if l.strip()]


def salvar_medicao(dir_sondagem: Path, medicao: dict) -> None:
    arq = caminho(dir_sondagem, "medicoes.ndjson")
    with arq.open("a", encoding="utf-8") as f:
        f.write(json.dumps(medicao, ensure_ascii=False) + "\n")


def cmd_iniciar(args) -> int:
    dir_s = Path(args.dir)
    arq_sessao = caminho(dir_s, "sessao.json")
    if arq_sessao.exists() and not args.reiniciar:
        print("Sessao ja existe:", arq_sessao, "(use --reiniciar para descartar)")
        return 1
    dir_s.mkdir(parents=True, exist_ok=True)
    sessao = {"lote": args.lote, "operador": args.operador, "iniciada_em": agora()}
    arq_sessao.write_text(json.dumps(sessao, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Sessao de sondagem iniciada:", arq_sessao)
    print("Protocolo: P1 listagem -> P2/P3/P4 uma consulta por sistema (com aprovacao) -> P5 teste negativo de bloqueio.")
    return 0


def _validar_aprovacao(caminho_arq):
    """Retorna (aprovacao|None, motivo)."""
    if not caminho_arq:
        return None, "arquivo de aprovacao nao informado"
    arq = Path(caminho_arq)
    if not arq.exists():
        return None, "arquivo de aprovacao inexistente: %s" % caminho_arq
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, "JSON invalido: %s" % e
    if not dados.get("aprovado"):
        return None, "campo 'aprovado' != true"
    if not dados.get("por"):
        return None, "campo 'por' ausente"
    if not dados.get("escopo"):
        return None, "campo 'escopo' ausente"
    return {"por": dados["por"], "escopo": dados["escopo"]}, "ok"


def cmd_medir(args) -> int:
    dir_s = Path(args.dir)
    if not caminho(dir_s, "sessao.json").exists():
        print("ERRO: nenhuma sessao ativa em", dir_s, "— rode 'iniciar' primeiro")
        return 1

    aprovacao, motivo = (None, "evento nao pago")
    bloqueado = False
    if args.pago:
        aprovacao, motivo = _validar_aprovacao(args.aprovacao)
        if aprovacao is None:
            bloqueado = True

    delta_saldo = (args.saldo_depois - args.saldo_antes)         if (args.saldo_antes is not None and args.saldo_depois is not None) else None
    delta_contador = (args.contador_depois - args.contador_antes)         if (args.contador_antes is not None and args.contador_depois is not None) else None

    medicao = {
        "ts": agora(),
        "pergunta": args.pergunta,
        "sistema": args.sistema,
        "evento": args.evento,
        "tipo_saldo": args.tipo_saldo or "",
        "saldo_antes": args.saldo_antes,
        "saldo_depois": args.saldo_depois,
        "delta_saldo": delta_saldo,
        "contador_antes": args.contador_antes,
        "contador_depois": args.contador_depois,
        "delta_contador": delta_contador,
        "moradores_inclusos": MORADORES_MAP.get(args.moradores_inclusos),
        "pago": args.pago,
        "bloqueado": bloqueado,
        "bloqueio_motivo": motivo if bloqueado else "",
        "aprovacao": aprovacao,
        "observacao": args.observacao or "",
    }
    salvar_medicao(dir_s, medicao)
    if bloqueado:
        print("BLOQUEADO (guard-rail P5): evento pago sem aprovacao valida — motivo:", motivo)
        print("Evidencia registrada para auditoria em medicoes.ndjson")
        return 2
    print("Medicao registrada:", args.pergunta, args.sistema, args.evento,
          "| delta_saldo:", delta_saldo, "| delta_contador:", delta_contador)
    return 0


def _veredito_p1(medicoes):
    """P1: listagem gratuita? Compara saldo/contador antes-depois do evento busca_listagem."""
    por_sistema = {}
    for sistema in SISTEMAS_VALIDOS:
        evs = [m for m in medicoes if m["pergunta"] == "P1" and m["sistema"] == sistema and not m["bloqueado"]]
        if not evs:
            por_sistema[sistema] = "sem_medicao"
            continue
        gratuita = all(
            (m["delta_saldo"] in (0, None)) and (m["delta_contador"] in (0, None))
            for m in evs
        )
        por_sistema[sistema] = "gratuita" if gratuita else "consome_credito"
    return por_sistema


def _veredito_p2(medicoes):
    """P2: Captei drena capcoins, contador mensal, ambos ou nada?"""
    evs = [m for m in medicoes if m["pergunta"] == "P2" and m["sistema"] == "captei" and not m["bloqueado"]]
    if not evs:
        return {"modalidade": "sem_medicao"}
    saldo_drenado = any((m["delta_saldo"] or 0) < 0 for m in evs)
    contador_drenado = any((m["delta_contador"] or 0) > 0 for m in evs)
    if saldo_drenado and contador_drenado:
        modalidade = "hibrido_capcoins_e_cota_mensal"
    elif saldo_drenado:
        modalidade = "pre_pago_capcoins"
    elif contador_drenado:
        modalidade = "cota_mensal"
    else:
        modalidade = "sem_custo_detectado"
    saida = {"modalidade": modalidade, "evidencias": len(evs)}
    if modalidade == "pre_pago_capcoins":
        saldos = [m["saldo_depois"] for m in evs if m["saldo_depois"] is not None]
        saida["saldo_atual_apos_sondagem"] = saldos[-1] if saldos else None
        saida["cota_real"] = "saldo de capcoins (pre-pago)"
        saida["plano_500_mes_valido_para_consultas"] = False
        saida["recomendacao"] = "tratar capcoins como budget; recarga (pacote 50 = R$ 49,90) apenas com aprovacao"
    elif modalidade == "cota_mensal":
        saida["cota_real"] = "contador mensal de consultas"
    return saida


def _veredito_p3(medicoes):
    """P3: 1 consulta EEmovel cobre perfil completo (moradores inclusos)?"""
    evs = [m for m in medicoes if m["pergunta"] == "P3" and m["sistema"] == "eemovel" and not m["bloqueado"]]
    if not evs:
        return {"escopo": "sem_medicao"}
    com_moradores = [m for m in evs if m["moradores_inclusos"] is not None]
    if not com_moradores:
        return {"escopo": "sem_medicao", "evidencias": len(evs), "motivo": "moradores_inclusos nao observado"}
    ultimo = com_moradores[-1]
    delta = ultimo["delta_contador"]
    if ultimo["moradores_inclusos"] is True and delta == 1:
        escopo = "perfil_completo_1_consulta"
    elif ultimo["moradores_inclusos"] is False and delta == 1:
        escopo = "moradores_consulta_separada"
    elif delta in (0, None):
        escopo = "sem_custo_detectado"
    else:
        escopo = "irregular_revisar"
    custo = {"perfil_completo_1_consulta": 1, "moradores_consulta_separada": 2}.get(escopo)
    return {"escopo": escopo, "custo_por_proprietario": custo, "evidencias": len(evs)}


def _veredito_p4(medicoes):
    """P4: cada modal Fisgar custa 1 das 250/mes?"""
    evs = [m for m in medicoes if m["pergunta"] == "P4" and m["sistema"] == "fisgar" and not m["bloqueado"]]
    if not evs:
        return {"custo_por_modal": "sem_medicao"}
    deltas = [m["delta_contador"] for m in evs]
    if all(d == 1 for d in deltas):
        return {"custo_por_modal": 1, "modalidade": "cota_mensal_250", "evidencias": len(evs)}
    if all(d == 0 for d in deltas):
        return {"custo_por_modal": 0, "modalidade": "modal_gratuito", "evidencias": len(evs)}
    return {"custo_por_modal": "irregular_revisar", "deltas": deltas, "evidencias": len(evs)}


def _veredito_p5(medicoes):
    """P5: guard-rail bloqueou pagamento sem aprovacao e aceitou com aprovacao?"""
    bloqueadas = [m for m in medicoes if m["bloqueado"]]
    pagos_ok = [m for m in medicoes if m["pago"] and not m["bloqueado"]]
    if bloqueadas and pagos_ok:
        conclusao = "ativo_e_validado"
    elif bloqueadas:
        conclusao = "ativo_falta_validar_fluxo_aprovado"
    elif pagos_ok:
        conclusao = "nao_testado_falta_tentativa_negativa"
    else:
        conclusao = "nao_testado"
    return {
        "conclusao": conclusao,
        "tentativas_bloqueadas": len(bloqueadas),
        "eventos_pagos_aprovados": len(pagos_ok),
    }


def cmd_veredito(args) -> int:
    dir_s = Path(args.dir)
    medicoes = carregar_medicoes(dir_s)
    if not medicoes:
        print("Nenhuma medicao registrada ainda.")
        return 1
    vereditos = {
        "gerado_em": agora(),
        "P1_listagem_gratuita": _veredito_p1(medicoes),
        "P2_captei_modalidade": _veredito_p2(medicoes),
        "P3_eemovel_escopo": _veredito_p3(medicoes),
        "P4_fisgar_modal": _veredito_p4(medicoes),
        "P5_guard_rail": _veredito_p5(medicoes),
    }
    arq = caminho(dir_s, "vereditos.json")
    arq.write_text(json.dumps(vereditos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(vereditos, ensure_ascii=False, indent=2))
    print("Vereditos salvos em", arq)
    return 0


def cmd_aplicar(args) -> int:
    dir_s = Path(args.dir)
    arq_ver = caminho(dir_s, "vereditos.json")
    if not arq_ver.exists():
        print("ERRO: rode 'veredito' antes de 'aplicar'.")
        return 1
    ver = carregar_json_ou(arq_ver, {})
    p1 = ver.get("P1_listagem_gratuita", {})
    p2 = ver.get("P2_captei_modalidade", {})
    p3 = ver.get("P3_eemovel_escopo", {})
    p4 = ver.get("P4_fisgar_modal", {})
    p5 = ver.get("P5_guard_rail", {})

    avisos = []
    for sistema in SISTEMAS_VALIDOS:
        if p1.get(sistema) == "consome_credito":
            avisos.append("ATENCAO: listagem de %s consumiu credito — inventario NAO e gratuito" % sistema)
        elif p1.get(sistema) == "sem_medicao":
            avisos.append("PENDENTE: medir P1 para %s" % sistema)
    if p2.get("modalidade") == "sem_medicao":
        avisos.append("PENDENTE: medir P2 (modalidade Captei)")
    if p3.get("escopo") in ("sem_medicao", None):
        avisos.append("PENDENTE: medir P3 (escopo EEmovel)")
    if p4.get("custo_por_modal") == "sem_medicao":
        avisos.append("PENDENTE: medir P4 (modal Fisgar)")
    if str(p5.get("conclusao", "")).startswith("nao_testado"):
        avisos.append("PENDENTE: validar guard-rail com tentativa negativa (P5)")

    custo_fisgar = p4.get("custo_por_modal")
    if not isinstance(custo_fisgar, (int, float)):
        custo_fisgar = None
    custos = {
        "gerado_em": agora(),
        "fonte": "sondagem_empirica",
        "sistemas": {
            "eemovel": {
                "limite_mes": 500,
                "custo_por_proprietario": p3.get("custo_por_proprietario"),
                "escopo_consulta": p3.get("escopo"),
            },
            "fisgar": {
                "limite_mes": 250,
                "custo_por_modal": custo_fisgar,
            },
            "captei": {
                "modalidade": p2.get("modalidade"),
                "cota_real": p2.get("cota_real", "sem_medicao"),
                "saldo_capcoins_atual": p2.get("saldo_atual_apos_sondagem"),
                "limite_mes_efetivo": "saldo_capcoins" if p2.get("modalidade") == "pre_pago_capcoins" else "sem_medicao",
            },
        },
        "guard_rail": {
            "aprovacao_humana_obrigatoria": True,
            "status": p5.get("conclusao"),
        },
        "ordem_cascata": ["eemovel", "fisgar", "captei"],
        "avisos": avisos,
    }
    arq = caminho(dir_s, "custos_verificados.json")
    arq.write_text(json.dumps(custos, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Custos verificados salvos em", arq)
    for av in avisos:
        print(" -", av)
    return 0


def cmd_status(args) -> int:
    dir_s = Path(args.dir)
    sessao = carregar_json_ou(caminho(dir_s, "sessao.json"), None)
    if not sessao:
        print("Nenhuma sessao ativa em", dir_s)
        return 1
    print("Sessao:", json.dumps(sessao, ensure_ascii=False))
    medicoes = carregar_medicoes(dir_s)
    print("Medicoes:", len(medicoes))
    for p in sorted(PERGUNTAS):
        total = sum(1 for m in medicoes if m["pergunta"] == p)
        bloq = sum(1 for m in medicoes if m["pergunta"] == p and m["bloqueado"])
        print("  %s: %d medicoes (%d bloqueadas) — %s" % (p, total, bloq, PERGUNTAS[p]))
    if caminho(dir_s, "vereditos.json").exists():
        print("Vereditos prontos — rode 'aplicar' para gerar custos_verificados.json")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Sondador de Cotas — verificacao empirica das regras de custo")
    ap.add_argument("--dir", default=str(DIR_PADRAO), help="diretorio da sessao (padrao: agentes/sondagem)")
    sub = ap.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("iniciar", help="abre sessao de sondagem")
    p.add_argument("--lote", required=True)
    p.add_argument("--operador", required=True)
    p.add_argument("--reiniciar", action="store_true")
    p.set_defaults(fn=cmd_iniciar)

    p = sub.add_parser("medir", help="registra uma medicao antes/depois")
    p.add_argument("--pergunta", required=True, choices=sorted(PERGUNTAS))
    p.add_argument("--sistema", required=True, choices=SISTEMAS_VALIDOS)
    p.add_argument("--evento", required=True, choices=sorted(EVENTOS_VALIDOS))
    p.add_argument("--tipo-saldo", default="", choices=["", "capcoins", "consultas"])
    p.add_argument("--saldo-antes", type=float, default=None)
    p.add_argument("--saldo-depois", type=float, default=None)
    p.add_argument("--contador-antes", type=int, default=None)
    p.add_argument("--contador-depois", type=int, default=None)
    p.add_argument("--moradores-inclusos", default="nao_informado",
                   choices=["true", "false", "nao_sei", "nao_informado"])
    p.add_argument("--pago", action="store_true")
    p.add_argument("--aprovacao", default=None, help="JSON: {aprovado: true, por, escopo}")
    p.add_argument("--observacao", default="")
    p.set_defaults(fn=cmd_medir)

    p = sub.add_parser("veredito", help="analisa medicoes e emite vereditos")
    p.set_defaults(fn=cmd_veredito)
    p = sub.add_parser("status", help="resumo da sessao")
    p.set_defaults(fn=cmd_status)
    p = sub.add_parser("aplicar", help="gera custos_verificados.json para o orquestrador")
    p.set_defaults(fn=cmd_aplicar)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
