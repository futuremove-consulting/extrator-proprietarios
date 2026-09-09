#!/usr/bin/env python3
"""Runner Fisgar via CLI agent-browser (Fluxo 2)."""
from __future__ import annotations
import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
sys.path.insert(0, str(Path(__file__).parent.parent))
from comum import canonicalizar_texto, classificar_entidade
from comum import classificar_tipo_unidade, criar_estrutura_lote
from comum import gerar_record_key_v2, parse_unidade
from comum import salvar_json_seguro, timestamp_iso
from comum.browser_cli import AgentBrowser
from comum.creditos import RelatorioCreditos
from fisgar.extrator import processar_modal_fisgar
from fisgar.persister import persistir_proprietario
AGENTE_DIR = Path(__file__).parent
SELECTORS_PATH = AGENTE_DIR / "selectors.json"
BASE_URL = "https://painel.fisgar.com.br"
BUSCA_URL = BASE_URL + "/proprietarios"
DFLT_AUTOCOMPLETE = "#selectedPlace"
DFLT_BUSCA = "Buscar"
DFLT_CONFIRMAR = "Confirmar Busca"
DFLT_LINHAS = "#owners-table-container tbody tr"
DFLT_CTA = "Consultar"
DFLT_VERMAIS = "VER MAIS"
def carregar_seletores():
    base = {}
    base["busca_autocomplete"] = DFLT_AUTOCOMPLETE
    base["busca_botao"] = DFLT_BUSCA
    base["confirmar_busca"] = DFLT_CONFIRMAR
    base["listagem_linhas"] = DFLT_LINHAS
    base["modal_cta"] = DFLT_CTA
    base["modal_ver_mais"] = DFLT_VERMAIS
    if SELECTORS_PATH.exists():
        fh = open(SELECTORS_PATH, encoding="utf-8")
        salvo = json.load(fh)
        fh.close()
        for k in salvo:
            if not k.startswith("_"):
                base[k] = salvo[k]
    return base
def garantir_sessao(ab):
    ab.open(BUSCA_URL)
    time.sleep(2)
    url = ab.get_url()
    if "/entrar" in url or "/login" in url:
        raise SystemExit("ERRO sessao Fisgar expirada: autentique manual")
    print("[sessao] ativa reutilizada")
def buscar_endereco(ab, sel, endereco):
    ab.open(BUSCA_URL)
    ab.wait("body")
    ab.fill(sel["busca_autocomplete"], endereco)
    time.sleep(2)
    ab.eval(
        "() => { const m = document.querySelector("
        "\"[role='listbox'] [role='option'], ul[role='listbox'] li\");"
        " if (m) { m.click(); return 'ok'; } return 'sem-opcao'; }")
    time.sleep(1)
    ab.click(sel["busca_botao"])
    time.sleep(3)
    if ab.is_visible(sel["confirmar_busca"]):
        ab.click(sel["confirmar_busca"])
        time.sleep(4)
    print("[busca] disparada")
RE_ATTR = chr(34) + chr(39)
RE_TEL = re.compile("tel:" + "[" + RE_ATTR + "]?" + "([^" + RE_ATTR + "<> ]+)")
RE_MAIL = re.compile("mailto:" + "[" + RE_ATTR + "]?" + "([^" + RE_ATTR + "<> ]+)")
RE_CPF = re.compile("[0-9]{3}[.]?[0-9]{3}[.]?[0-9]{3}[-.]?[0-9]{2}")
def extrair_listagem(ab, sel):
    cont = sel.get("listagem_container", "")
    acc = json.dumps(sel["listagem_linhas"])
    cacc = json.dumps(cont)
    js = ("() => { const cont = (" + cacc + " ? document.querySelector("
          + cacc + ") : document);"
          " const rows = [...(cont || document).querySelectorAll("
          + acc + ")];"
          " return rows.map(function (tr) { return { texto: tr.innerText"
          ".replace(/\\n/g, ' | ').trim(),"
          " cells: [...tr.querySelectorAll('td,th')]"
          ".map(function (td) { return td.innerText.trim(); }) }; })"
          ".filter(function (r) { return r.texto; }); }")
    out = ab.eval(js)
    try:
        linhas = json.loads(out)
    except (ValueError, TypeError):
        print("[listagem] eval nao retornou JSON - rode calibrate")
        return []
    unicas = {}
    for linha in linhas:
        chave = canonicalizar_texto(linha.get("texto", ""))
        unicas.setdefault(chave, linha)
    print("[listagem] inventariadas")
    return list(unicas.values())
def extrair_modal(ab, sel, linha):
    cells = linha.get("cells") or []
    nome = cells[0] if cells else ""
    acc = json.dumps(sel["listagem_linhas"])
    nacc = json.dumps(nome[:40])
    cacc = json.dumps(sel["modal_cta"])
    js = ("() => { const rows = [...document.querySelectorAll("
          + acc + ")];"
          " const alvo = rows.find(function (tr) {"
          " return (tr.innerText || '').includes(" + nacc + "); });"
          " if (!alvo) return 'sem-linha';"
          " const btn = [...alvo.querySelectorAll('button')].find("
          "function (b) { return (b.innerText || '').includes("
          + cacc + "); });"
          " if (!btn) return 'sem-cta'; btn.click(); return 'ok'; }")
    clicou = ab.eval(js)
    if "ok" not in clicou:
        print("[modal] CTA nao localizado")
        return None
    time.sleep(3)
    for _ in range(10):
        if not ab.is_visible(sel["modal_ver_mais"]):
            break
        ab.click(sel["modal_ver_mais"])
        time.sleep(1)
    html = ab.eval(
        "() => { const m = document.querySelector("
        "\"[role='dialog'], .MuiDialog-root\");"
        " return m ? m.innerHTML.slice(0, 60000) : ''; }")
    texto = ab.eval(
        "() => { const m = document.querySelector("
        "\"[role='dialog'], .MuiDialog-root\");"
        " return m ? m.innerText.slice(0, 20000) : ''; }")
    if not texto.strip():
        print("[modal] vazio")
        return None
    det = {}
    det["telefones"] = RE_TEL.findall(html)
    det["emails"] = RE_MAIL.findall(html)
    det["cpfs"] = RE_CPF.findall(texto)
    ab.eval(
        "() => { document.dispatchEvent("
        "new KeyboardEvent('keydown', {key: 'Escape'})); return 'ok'; }")
    time.sleep(1)
    return det
def montar_registro(linha, endereco, source_line):
    cells = linha.get("cells") or []
    nome_raw = cells[0] if cells else linha.get("texto", "")
    unidade_raw = cells[3] if len(cells) > 3 else ""
    unidade = parse_unidade(unidade_raw)
    name_can = canonicalizar_texto(nome_raw)
    addr_can = canonicalizar_texto(endereco)
    unit_can = unidade.get("unidade_imovel_canonical", "") or canonicalizar_texto(unidade_raw)
    vaga_can = unidade.get("unidade_vaga_canonical", "")
    rk = gerar_record_key_v2(name_can, unit_can, vaga_can, addr_can)
    reg = {}
    reg["name_raw"] = nome_raw
    reg["name_canonical"] = name_can
    reg["address_raw"] = endereco
    reg["address_canonical"] = addr_can
    reg["unit_raw"] = unidade_raw
    reg["unit_canonical"] = unit_can
    reg["unidade_vaga_canonical"] = vaga_can
    reg["tipo_unidade"] = classificar_tipo_unidade(unit_can, vaga_can)
    reg["entity_type"] = classificar_entidade(nome_raw)
    reg["source_system"] = "fisgar"
    reg["source_line"] = source_line
    reg["source_record_id"] = None
    reg["record_key"] = rk
    reg["state"] = "inventariado"
    reg["timestamp"] = timestamp_iso()
    return reg
def dados_modal(registro, detalhe):
    tels = []
    for i, t in enumerate(detalhe.get("telefones", [])):
        tels.append({"numero": t, "principal": i == 0, "tipo": ""})
    mails = []
    for i, e in enumerate(detalhe.get("emails", [])):
        mails.append({"endereco": e, "principal": i == 0, "tipo": ""})
    cpfs = detalhe.get("cpfs") or []
    cpf = cpfs[0] if cpfs else ""
    m = {}
    m["nome_completo"] = registro["name_raw"]
    m["endereco_retornado"] = registro["address_raw"]
    m["unidade"] = registro["unit_raw"]
    m["cpf"] = cpf
    m["telefones"] = tels
    m["emails"] = mails
    m["metodo_extracao"] = "browser_agent_browser"
    m["modal_completo"] = bool(tels or mails)
    return m
class Lote:
    def __init__(self, nome_lote, diretorio_base=None):
        self.nome = nome_lote
        base = diretorio_base or str(AGENTE_DIR.parent)
        self.estrutura = criar_estrutura_lote(nome_lote, base)
        self.manifest_path = self.estrutura["manifest"] / ("manifest_" + nome_lote + ".ndjson")
        self.ckpt_path = self.estrutura["checkpoints"] / "runner_checkpoint.json"
    def append_manifest(self, registro):
        fh = open(self.manifest_path, "a", encoding="utf-8")
        fh.write(json.dumps(registro, ensure_ascii=False) + chr(10))
        fh.close()
    def ler_checkpoint(self):
        if self.ckpt_path.exists():
            fh = open(self.ckpt_path, encoding="utf-8")
            d = json.load(fh)
            fh.close()
            return d
        return {"ultimo_idx": -1, "processados": []}
    def salvar_checkpoint(self, ultimo_idx, processados):
        salvar_json_seguro({"ultimo_idx": ultimo_idx, "processados": processados}, self.ckpt_path)
    def persistir(self, registro, modal):
        processado = processar_modal_fisgar(modal)
        persistir_proprietario(processado, registro, self.estrutura, self.nome)
def rodar_live(args):
    sel = carregar_seletores()
    ab = AgentBrowser(default_session="fisgar-runner")
    lote = Lote(args.lote)
    creditos = RelatorioCreditos("fisgar", args.endereco)
    garantir_sessao(ab)
    if args.calibrate:
        dump = lote.estrutura["logs"] / "calibrate_fisgar.txt"
        dump.write_text(ab.snapshot(), encoding="utf-8")
        print("[calibrate] snapshot salvo")
        return
    buscar_endereco(ab, sel, args.endereco)
    creditos.listagem("busca")
    linhas = extrair_listagem(ab, sel)
    if not linhas:
        creditos.salvar(lote.estrutura["logs"])
        raise SystemExit("Nenhuma linha: seletores, dados ou sessao")
    limite = min(args.max_consultas, len(linhas))
    ckpt = lote.ler_checkpoint()
    procs = list(ckpt.get("processados", []))
    for idx in range(ckpt["ultimo_idx"] + 1, limite):
        registro = montar_registro(linhas[idx], args.endereco, idx + 1)
        if registro["entity_type"] == "Empresa":
            registro["state"] = "empresa_classificada"
            lote.append_manifest(registro)
            lote.salvar_checkpoint(idx, procs)
            print("[emp] ignorada")
            continue
        lote.append_manifest(registro)
        detalhe = extrair_modal(ab, sel, linhas[idx])
        creditos.detalhe(registro["record_key"])
        if detalhe is None:
            print("[modal] indisponivel")
        else:
            lote.persistir(registro, dados_modal(registro, detalhe))
            procs.append(registro["record_key"])
            print("[ok] " + registro["name_raw"][:40])
        lote.salvar_checkpoint(idx, procs)
    caminho = creditos.salvar(lote.estrutura["logs"])
    print("[fim] processados=" + str(len(procs)))
    print("[fim] " + creditos.resumo())
def rodar_mock(args):
    fh = open(args.input, encoding="utf-8")
    linhas = json.load(fh)
    fh.close()
    lote = Lote(args.lote)
    procs = []
    for idx, linha in enumerate(linhas):
        endereco = linha.get("endereco", args.endereco)
        registro = montar_registro(linha, endereco, idx + 1)
        lote.append_manifest(registro)
        if registro["entity_type"] == "Empresa":
            continue
        texto = linha.get("detalhe_texto", "") or linha.get("texto", "")
        det = {}
        det["telefones"] = RE_TEL.findall(texto)
        det["emails"] = RE_MAIL.findall(texto)
        det["cpfs"] = RE_CPF.findall(texto)
        lote.persistir(registro, dados_modal(registro, det))
        procs.append(registro["record_key"])
    salvar_json_seguro({"total": len(procs)}, lote.estrutura["checkpoints"] / "mock_result.json")
    print("[mock] total=" + str(len(procs)))
def _parse_endereco(endereco):
    m = re.match(r"^(.*?)[,\s]+(\d+)" + chr(36), endereco.strip())
    if m:
        return m.group(1).strip().rstrip(","), m.group(2)
    return endereco.strip(), ""
def rodar_batch_json(args):
    sel = carregar_seletores()
    ab = AgentBrowser(default_session="fisgar-runner")
    garantir_sessao(ab)
    buscar_endereco(ab, sel, args.endereco)
    linhas = extrair_listagem(ab, sel)
    records = []
    limite = min(args.max_consultas, len(linhas))
    rua, numero = _parse_endereco(args.endereco)
    for idx, linha in enumerate(linhas):
        registro = montar_registro(linha, args.endereco, idx + 1)
        tels = []
        mails = []
        cpf = ""
        if idx < limite and registro["entity_type"] != "Empresa":
            detalhe = extrair_modal(ab, sel, linha)
            if detalhe:
                tels = detalhe.get("telefones", [])
                mails = detalhe.get("emails", [])
                cpfs = detalhe.get("cpfs") or []
                cpf = cpfs[0] if cpfs else ""
        rec = {}
        rec["nome"] = registro["name_raw"]
        rec["id"] = registro["record_key"]
        rec["telefones"] = tels
        rec["emails"] = mails
        rec["cpf"] = cpf
        rec["unidade"] = registro["unit_raw"]
        rec["endereco"] = registro["address_raw"]
        rec["street"] = rua
        rec["number"] = numero
        rec["city"] = args.cidade
        rec["tipo"] = "proprietario"
        records.append(rec)
    json.dump(records, sys.stdout, ensure_ascii=False, indent=2)
    print()
def main():
    ap = argparse.ArgumentParser(description="Runner Fisgar agent-browser")
    sub = ap.add_subparsers(dest="modo", required=True)
    p_live = sub.add_parser("live")
    p_live.add_argument("--endereco", required=True)
    p_live.add_argument("--cidade", default="")
    p_live.add_argument("--lote", default=None)
    p_live.add_argument("--max-consultas", type=int, default=5)
    p_live.add_argument("--calibrate", action="store_true")
    p_mock = sub.add_parser("mock-input")
    p_mock.add_argument("--input", required=True)
    p_mock.add_argument("--endereco", default="")
    p_mock.add_argument("--lote", default=None)
    p_batch = sub.add_parser("batch-json")
    p_batch.add_argument("--endereco", required=True)
    p_batch.add_argument("--cidade", default="")
    p_batch.add_argument("--max-consultas", type=int, default=10)
    args = ap.parse_args()
    if args.lote is None and args.modo in ("live", "mock-input"):
        slug = canonicalizar_texto(args.endereco)[:40].replace(" ", "_")
        args.lote = "runner_" + slug + "_fisgar"
    if args.modo == "live":
        rodar_live(args)
    elif args.modo == "batch-json":
        rodar_batch_json(args)
    else:
        rodar_mock(args)
if __name__ == "__main__":
    main()
