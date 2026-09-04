#!/usr/bin/env python3
"""Sonda Dono do Zap — descoberta empirica da camada de validacao de WhatsApp.

Responde, com numeros da PROPRIA EQUIPE (nunca leads reais), o comportamento
real dos dois dominios (donodozap.com e donodozap.com.br):
  - a pesquisa gratuita retorna o NOME PUBLICO de exibicao do WhatsApp?
  - o desbloqueio PIX e oferecido? a que preco?
  - tempo por consulta; sigilo declarado na UI; limites/antibot?

E inclui o nucleo da regra central do usuario:
  COMPARAR o nome publico de exibicao daquele WhatsApp com o nome do
  proprietario em questao (via similaridade_nomes, banda 0.92/0.75).

Subcomandos:
  iniciar   : abre a sessao de sonda (lote, operador)
  medir     : registra 1 sonda em 1 dominio (observacoes da UI)
  comparar  : compara nome do proprietario x nome publico (banda 0.92/0.75)
  veredito  : agrega as sondas por dominio e recomenda
  aplicar   : gera validacao_whatsapp_config.json (entrada da Fase 2)
  status    : resumo da sessao

Privacidade: o numero de teste e armazenado SOMENTE como rotulo mascarado
(ex.: "****1234") — nunca o numero completo.

Protocolo (~15 min):
  python3 sondar_donozap.py iniciar --lote mar_chagall --operador leonardo
  # dominio .com (pesquisa gratuita)
  python3 sondar_donozap.py medir --dominio com --numero-sufixo "****1234"       --nome-publico "Paula Eleonora Cunha" --foto-gratis false --pix-oferecido true       --pix-valor 4.90 --tempo-segundos 8 --sigilo ui_afirma
  # dominio .com.br
  python3 sondar_donozap.py medir --dominio com_br --numero-sufixo "****1234"       --nome-publico "" --pix-oferecido false --tempo-segundos 15 --sigilo nao_verificado
  # regra central: o nome publico bate com o proprietario?
  python3 sondar_donozap.py comparar --nome-proprietario "PAULA ELEONORA DA CUNHA"       --nome-publico "Paula Eleonora Cunha" --registrar
  python3 sondar_donozap.py veredito
  python3 sondar_donozap.py aplicar   # -> validacao_whatsapp_config.json (Fase 2)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIR_PADRAO = BASE / "sondagem"

DOMINIOS = ("com", "com_br")
ROTULO_DOMINIO = {"com": "donodozap.com", "com_br": "donodozap.com.br"}


NOME_ARQ = {
    "sessao": "donozap_sessao.json",
    "medicoes": "donozap_medicoes.ndjson",
    "comparacoes": "donozap_comparacoes.ndjson",
    "vereditos": "donozap_vereditos.json",
    "config": "validacao_whatsapp_config.json",
}


def agora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def caminho(dir_sondagem: Path, chave: str) -> Path:
    return dir_sondagem / NOME_ARQ[chave]


def carregar_json_ou(arq: Path, padrao):
    if not arq.exists():
        return padrao
    return json.loads(arq.read_text(encoding="utf-8"))


def carregar_ndjson(arq: Path):
    if not arq.exists():
        return []
    return [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines() if l.strip()]


def salvar_ndjson(arq: Path, registro: dict) -> None:
    with arq.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def cmd_iniciar(args) -> int:
    dir_s = Path(args.dir)
    arq_sessao = caminho(dir_s, "sessao")
    if arq_sessao.exists() and not args.reiniciar:
        print("Sessao ja existe:", arq_sessao, "(use --reiniciar para descartar)")
        return 1
    dir_s.mkdir(parents=True, exist_ok=True)
    sessao = {
        "lote": args.lote,
        "operador": args.operador,
        "dominios_a_testar": ["com", "com_br"],
        "escopo_validacao": "todos_os_leads",
        "numeros": "propria_equipe_mascarados",
        "iniciada_em": agora(),
    }
    arq_sessao.write_text(json.dumps(sessao, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Sessao de sonda Dono do Zap iniciada:", arq_sessao)
    print("Protocolo: para cada dominio (com, com_br), faca 1 pesquisa gratuita com um numero da equipe e registre com 'medir'.")
    return 0


def cmd_medir(args) -> int:
    dir_s = Path(args.dir)
    if not caminho(dir_s, "sessao").exists():
        print("ERRO: nenhuma sessao ativa em", dir_s, "— rode 'iniciar' primeiro")
        return 1
    if args.numero_sufixo.count("*") < 4:
        print("ERRO: --numero-sufixo deve ser um rotulo MASCARADO (ex.: '****1234'). Nunca armazene o numero completo.")
        return 1

    medicao = {
        "ts": agora(),
        "dominio": args.dominio,
        "dominio_url": ROTULO_DOMINIO[args.dominio],
        "numero_sufixo": args.numero_sufixo,
        "nome_publico_retornado": args.nome_publico or "",
        "nome_publico_obtido": bool(args.nome_publico and args.nome_publico.strip()),
        "foto_gratis": {"true": True, "false": False, "nao_informado": None}[args.foto_gratis],
        "pix_oferecido": args.pix_oferecido == "true",
        "pix_valor": args.pix_valor,
        "tempo_segundos": args.tempo_segundos,
        "sigilo": args.sigilo,
        "limites": args.limites or "",
        "observacao": args.observacao or "",
    }
    salvar_ndjson(caminho(dir_s, "medicoes"), medicao)
    print(
        "Sonda registrada:", ROTULO_DOMINIO[args.dominio],
        "| nome_publico_obtido:", medicao["nome_publico_obtido"],
        "| pix_oferecido:", medicao["pix_oferecido"],
        "| pix_valor:", medicao["pix_valor"],
        "| tempo_s:", medicao["tempo_segundos"],
    )
    return 0


def cmd_comparar(args) -> int:
    """Regra central: nome publico de exibicao do WhatsApp x nome do proprietario."""
    dir_s = Path(args.dir)
    from comum.matching_revisao import (
        AUTO_MERGE_THRESHOLD,
        REVIEW_THRESHOLD,
        similaridade_nomes,
    )

    score = similaridade_nomes(args.nome_proprietario, args.nome_publico)
    if score >= AUTO_MERGE_THRESHOLD:
        cls = "whatsapp_validado_publico"
        leitura = "BATE — nome publico confere com o proprietario (sem gastar Capcoin)"
    elif score >= REVIEW_THRESHOLD:
        cls = "ambiguo_revisao"
        leitura = "AMBIGUO — operador decide (possivel abreviatura/apelido; foto paga opcional)"
    else:
        cls = "nao_correspondente"
        leitura = "NAO BATE — numero provavelmente nao e do proprietario em questao"

    resultado = {
        "ts": agora(),
        "nome_proprietario": args.nome_proprietario,
        "nome_publico_whatsapp": args.nome_publico,
        "score": round(score, 4),
        "banda": {"auto_merge": AUTO_MERGE_THRESHOLD, "revisao_min": REVIEW_THRESHOLD},
        "classificacao": cls,
        "leitura": leitura,
    }
    if args.registrar:
        if not caminho(dir_s, "sessao").exists():
            print("ERRO: nenhuma sessao ativa — rode 'iniciar' antes de --registrar")
            return 1
        salvar_ndjson(caminho(dir_s, "comparacoes"), resultado)
        resultado["registrado"] = True
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


def _veredito_dominio(medicoes_dominio):
    if not medicoes_dominio:
        return {"status": "sem_sonda", "sondas": 0}
    n = len(medicoes_dominio)
    obtidos = sum(1 for m in medicoes_dominio if m["nome_publico_obtido"])
    pix = [m for m in medicoes_dominio if m["pix_oferecido"]]
    pix_valores = sorted({m["pix_valor"] for m in pix if m["pix_valor"] is not None})
    tempos = [m["tempo_segundos"] for m in medicoes_dominio if m["tempo_segundos"] is not None]
    if n and obtidos == n:
        status = "nome_publico_gratis_confirmado"
    elif obtidos > 0:
        status = "nome_publico_parcial_revisar"
    else:
        status = "sem_retorno_gratuito_revisar"
    return {
        "status": status,
        "sondas": n,
        "nome_publico_obtido": obtidos,
        "taxa_nome_publico": round(obtidos / n, 2),
        "pix_oferecido": len(pix),
        "pix_valores_observados": pix_valores,
        "tempo_medio_segundos": round(sum(tempos) / len(tempos), 1) if tempos else None,
        "sigilo_claims": sorted({m["sigilo"] for m in medicoes_dominio}),
    }


def cmd_veredito(args) -> int:
    dir_s = Path(args.dir)
    medicoes = carregar_ndjson(caminho(dir_s, "medicoes"))
    if not medicoes:
        print("Nenhuma sonda registrada ainda.")
        return 1
    comparacoes = carregar_ndjson(caminho(dir_s, "comparacoes"))
    por_dominio = {d: _veredito_dominio([m for m in medicoes if m["dominio"] == d]) for d in DOMINIOS}

    viaveis = [d for d, v in por_dominio.items() if v["status"] == "nome_publico_gratis_confirmado"]
    recomendacao = (
        "usar " + ", ".join(ROTULO_DOMINIO[d] for d in viaveis) + " para validacao gratuita por nome publico"
        if viaveis else "nenhum dominio confirmou nome publico gratuito — revisar sondas/protocolo"
    )
    vereditos = {
        "gerado_em": agora(),
        "por_dominio": {ROTULO_DOMINIO[d]: v for d, v in por_dominio.items()},
        "recomendacao": recomendacao,
        "comparacoes_registradas": len(comparacoes),
        "distribuicao_comparacoes": _distribuicao_comparacoes(comparacoes),
    }
    arq = caminho(dir_s, "vereditos")
    arq.write_text(json.dumps(vereditos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(vereditos, ensure_ascii=False, indent=2))
    print("Vereditos salvos em", arq)
    return 0


def _distribuicao_comparacoes(comparacoes):
    dist = {}
    for c in comparacoes:
        dist[c["classificacao"]] = dist.get(c["classificacao"], 0) + 1
    return dist


def cmd_aplicar(args) -> int:
    dir_s = Path(args.dir)
    arq_ver = caminho(dir_s, "vereditos")
    if not arq_ver.exists():
        print("ERRO: rode 'veredito' antes de 'aplicar'.")
        return 1
    ver = carregar_json_ou(arq_ver, {})
    por_dominio = ver.get("por_dominio", {})

    dominio_recomendado = None
    for d in DOMINIOS:
        v = por_dominio.get(ROTULO_DOMINIO[d], {})
        if v.get("status") == "nome_publico_gratis_confirmado":
            dominio_recomendado = ROTULO_DOMINIO[d]
            break
    if dominio_recomendado is None:
        dominio_recomendado = "sem_confirmacao"

    pendencias = []
    for d in DOMINIOS:
        v = por_dominio.get(ROTULO_DOMINIO[d], {})
        if v.get("status") in ("sem_sonda", "sem_retorno_gratuito_revisar", "nome_publico_parcial_revisar"):
            pendencias.append("Revisar sonda do dominio %s (status: %s)" % (ROTULO_DOMINIO[d], v.get("status")))
    if ver.get("comparacoes_registradas", 0) == 0:
        pendencias.append("Registrar ao menos 1 comparacao de nome (regra central) com 'comparar --registrar'")

    config = {
        "gerado_em": agora(),
        "fonte": "sonda_donozap_empirica",
        "dominios_testados": [ROTULO_DOMINIO[d] for d in DOMINIOS],
        "dominio_recomendado": dominio_recomendado,
        "estatisticas_por_dominio": por_dominio,
        "regra_match": {
            "comparacao": "similaridade_nomes(nome_proprietario, nome_publico_whatsapp)",
            "whatsapp_validado_publico": ">= 0.92",
            "ambiguo_revisao": "0.75 a 0.92",
            "nao_correspondente": "< 0.75",
            "inicial_nome_do_meio_vai_para_revisao": True,
        },
        "escopo_validacao": "todos_os_leads",
        "economia_esperada_capcoins": "70-85 por cento das validacoes sem custo",
        "proximo_passo": "Fase 2: comum/validacao_whatsapp.py + fila CSV operavel + import no orquestrador",
        "pendencias": pendencias,
    }
    arq = caminho(dir_s, "config")
    arq.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Config de validacao WhatsApp salva em", arq)
    for pend in pendencias:
        print(" -", pend)
    return 0


def cmd_status(args) -> int:
    dir_s = Path(args.dir)
    sessao = carregar_json_ou(caminho(dir_s, "sessao"), None)
    if not sessao:
        print("Nenhuma sessao ativa em", dir_s)
        return 1
    print("Sessao:", json.dumps(sessao, ensure_ascii=False))
    medicoes = carregar_ndjson(caminho(dir_s, "medicoes"))
    comparacoes = carregar_ndjson(caminho(dir_s, "comparacoes"))
    print("Sondas:", len(medicoes), "| Comparacoes:", len(comparacoes))
    for d in DOMINIOS:
        n = sum(1 for m in medicoes if m["dominio"] == d)
        print("  %s: %d sonda(s)" % (ROTULO_DOMINIO[d], n))
    if caminho(dir_s, "vereditos").exists():
        print("Vereditos prontos — rode 'aplicar' para gerar validacao_whatsapp_config.json")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Sonda Dono do Zap — descoberta empirica da validacao de WhatsApp")
    ap.add_argument("--dir", default=str(DIR_PADRAO), help="diretorio da sessao (padrao: agentes/sondagem)")
    sub = ap.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("iniciar", help="abre a sessao de sonda")
    p.add_argument("--lote", required=True)
    p.add_argument("--operador", required=True)
    p.add_argument("--reiniciar", action="store_true")
    p.set_defaults(fn=cmd_iniciar)

    p = sub.add_parser("medir", help="registra 1 sonda em 1 dominio")
    p.add_argument("--dominio", required=True, choices=DOMINIOS)
    p.add_argument("--numero-sufixo", required=True, help="rotulo mascarado (ex.: ****1234)")
    p.add_argument("--nome-publico", default="", help="nome de exibicao retornado pela pesquisa gratuita (vazio se nada)")
    p.add_argument("--foto-gratis", default="nao_informado", choices=["true", "false", "nao_informado"])
    p.add_argument("--pix-oferecido", default="false", choices=["true", "false"])
    p.add_argument("--pix-valor", type=float, default=None)
    p.add_argument("--tempo-segundos", type=float, default=None)
    p.add_argument("--sigilo", default="nao_verificado", choices=["ui_afirma", "nao_verificado"])
    p.add_argument("--limites", default="")
    p.add_argument("--observacao", default="")
    p.set_defaults(fn=cmd_medir)

    p = sub.add_parser("comparar", help="nome do proprietario x nome publico (banda 0.92/0.75)")
    p.add_argument("--nome-proprietario", required=True)
    p.add_argument("--nome-publico", required=True)
    p.add_argument("--registrar", action="store_true", help="grava em donozap_comparacoes.ndjson")
    p.set_defaults(fn=cmd_comparar)

    p = sub.add_parser("veredito", help="agrega sondas por dominio e recomenda")
    p.set_defaults(fn=cmd_veredito)
    p = sub.add_parser("aplicar", help="gera validacao_whatsapp_config.json (Fase 2)")
    p.set_defaults(fn=cmd_aplicar)
    p = sub.add_parser("status", help="resumo da sessao")
    p.set_defaults(fn=cmd_status)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
