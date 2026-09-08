#!/usr/bin/env python3
"""Runner EEmóvel — extração determinística via CLI agent-browser.

Fluxo: login -> busca por endereço -> listagem (manifest NDJSON) ->
detalhe por registro -> processar_modal_eemovel -> persistir_proprietario.

Modos:
    python3 runner.py live --endereco "Rua X, 100" [--cidade "..."] [--max-consultas 5]
    python3 runner.py calibrate --endereco "Rua X, 100"     # dump snapshot p/ calibrar seletores
    python3 runner.py mock-input --input arquivo.json       # pipeline sem browser (testes)

Credenciais: env EEMOVEL_EMAIL / EEMOVEL_SENHA.
Sessão: env AGENT_BROWSER_SESSION (default: eemovel-runner).
Seletores: agentes/eemovel/selectors.json (calibrável sem tocar no código).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from comum import (
    canonicalizar_texto,
    classificar_entidade,
    classificar_tipo_unidade,
    criar_estrutura_lote,
    gerar_record_key_v2,
    parse_unidade,
    salvar_json_seguro,
    timestamp_iso,
)
from eemovel.extrator import processar_modal_eemovel
from eemovel.persister import persistir_proprietario

AGENTE_DIR = Path(__file__).parent
SELECTORS_PATH = AGENTE_DIR / "selectors.json"
BASE_URL = "https://brokers.eemovel.com.br"
LOGIN_URL = f"{BASE_URL}/login"
CONSULTA_URL = f"{BASE_URL}/consulta"

DEFAULT_SELECTORS = {
    "login_email": "input[type='email'], input[name='email'], #email",
    "login_senha": "input[type='password'], input[name='senha'], #senha",
    "login_botao": "button[type='submit'], button:has-text('Entrar')",
    "busca_cidade": "input[name='cidade'], #cidade",
    "busca_endereco": "input[name='endereco'], #endereco, input[placeholder*='ndere']",
    "busca_numero_inicial": "input[name='numeroInicial'], #numeroInicial",
    "busca_numero_final": "input[name='numeroFinal'], #numeroFinal",
    "busca_botao": "button:has-text('Buscar'), input[type='submit']",
    "listagem_tabela": "table tbody tr",
    "detalhe_abrir": "a:has-text('Ver mais'), button:has-text('Ver mais')",
}


def carregar_seletores() -> dict[str, str]:
    if SELECTORS_PATH.exists():
        with open(SELECTORS_PATH, encoding="utf-8") as f:
            salvo = json.load(f)
        return {**DEFAULT_SELECTORS, **salvo}
    return dict(DEFAULT_SELECTORS)


class AgentBrowser:
    """Wrapper subprocess da CLI agent-browser (sessão nomeada persistente)."""

    def __init__(self, session: str | None = None, timeout: int = 60):
        self.session = session or os.environ.get("AGENT_BROWSER_SESSION", "eemovel-runner")
        self.timeout = timeout
        self._bin = os.environ.get("AGENT_BROWSER_BIN", "agent-browser")

    def run(self, *args: str, timeout: int | None = None) -> str:
        cmd = [self._bin, "--session", self.session, *args]
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout or self.timeout,
            env={**os.environ, "PATH": os.environ.get("AB_PATH_OVERRIDE", os.environ["PATH"])},
        )
        if proc.returncode != 0:
            raise RuntimeError(f"agent-browser {' '.join(args[:2])} falhou (exit {proc.returncode}): {proc.stderr.strip()[:300]}")
        return proc.stdout

    # --- atalhos de alto nível ---
    def open(self, url: str) -> str:
        return self.run("open", url)

    def get_url(self) -> str:
        return self.run("get", "url").strip()

    def fill(self, sel: str, texto: str) -> str:
        return self.run("fill", sel, texto)

    def click(self, sel: str) -> str:
        return self.run("click", sel)

    def wait(self, alvo: str) -> str:
        return self.run("wait", alvo)

    def read(self) -> str:
        return self.run("read")

    def snapshot(self) -> str:
        return self.run("snapshot")

    def eval(self, js: str) -> str:
        return self.run("eval", js)

    def is_visible(self, sel: str) -> bool:
        proc = subprocess.run(
            [self._bin, "--session", self.session, "is", "visible", sel],
            capture_output=True, text=True, timeout=self.timeout,
        )
        return proc.returncode == 0 and "true" in proc.stdout.lower()


# ---------------------------------------------------------------------------
# Login e busca
# ---------------------------------------------------------------------------

def garantir_login(ab: AgentBrowser, sel: dict[str, str]) -> None:
    """Garante sessão logada: se cair no /login, autentica com env creds."""
    ab.open(CONSULTA_URL)
    time.sleep(2)
    if "/login" not in ab.get_url():
        print("[login] sessão ativa reutilizada")
        return

    email = os.environ.get("EEMOVEL_EMAIL")
    senha = os.environ.get("EEMOVEL_SENHA")
    if not email or not senha:
        raise SystemExit("ERRO: EEMOVEL_EMAIL/EEMOVEL_SENHA não definidas no ambiente.")

    print("[login] autenticando no EEmóvel...")
    ab.open(LOGIN_URL)
    ab.wait("body")
    ab.fill(sel["login_email"], email)
    ab.fill(sel["login_senha"], senha)
    ab.click(sel["login_botao"])
    time.sleep(3)
    if "/login" in ab.get_url():
        raise SystemExit("ERRO: login falhou — verifique credenciais/seletores.")
    print("[login] ok")


def buscar_endereco(ab: AgentBrowser, sel: dict[str, str], endereco: str,
                    cidade: str, num_inicial: int, num_final: int) -> None:
    """Preenche o formulário de consulta e dispara a busca (consome 1 crédito)."""
    ab.open(CONSULTA_URL)
    ab.wait("body")
    if cidade:
        ab.fill(sel["busca_cidade"], cidade)
    ab.fill(sel["busca_endereco"], endereco)
    ab.fill(sel["busca_numero_inicial"], str(num_inicial))
    ab.fill(sel["busca_numero_final"], str(num_final))
    ab.click(sel["busca_botao"])
    time.sleep(5)
    print(f"[busca] disparada para '{endereco}' ({num_inicial}-{num_final})")


RE_TELEFONE2 = re.compile(r"\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}")
RE_EMAIL2 = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
RE_CPF2 = re.compile(r"\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}")


def parse_texto_livre(texto: str) -> dict[str, list[str]]:
    """Parse de telefones/emails/CPFs a partir de texto livre da página."""
    return {
        "telefones": RE_TELEFONE2.findall(texto),
        "emails": RE_EMAIL2.findall(texto),
        "cpfs": RE_CPF2.findall(texto),
    }


def extrair_listagem(ab: AgentBrowser, sel: dict[str, str]) -> list[dict[str, Any]]:
    """Extrai linhas da listagem via eval JS (determinístico)."""
    js = (
        "() => { const rows = [...document.querySelectorAll("
        + json.dumps(sel["listagem_tabela"]) + ")];"
        " return rows.map(tr => ({ texto: tr.innerText.replace(/\\n/g, ' | ').trim(),"
        " cells: [...tr.querySelectorAll('td,th')].map(td => td.innerText.trim()) }))"
        " .filter(r => r.texto); }"
    )
    out = ab.eval(js)
    try:
        linhas = json.loads(out)
    except json.JSONDecodeError:
        print("[listagem] eval não retornou JSON — rode `calibrate` para ajustar seletores")
        return []
    print(f"[listagem] {len(linhas)} linhas extraídas")
    return linhas


def extrair_detalhe(ab: AgentBrowser, sel: dict[str, str],
                    idx: int) -> dict[str, Any] | None:
    """Abre o detalhe do registro idx e extrai contatos (consome 1 crédito)."""
    seletor_linha = json.dumps(sel["listagem_tabela"])
    try:
        ab.eval(f"(els => els[{idx}] && els[{idx}].click())([...document.querySelectorAll({seletor_linha})])")
    except RuntimeError as exc:
        print(f"[detalhe {idx}] falhou ao abrir: {exc}")
        return None
    time.sleep(3)
    conteudo = ab.read()
    achados = parse_texto_livre(conteudo)
    ab.run("back")
    time.sleep(2)
    return {**achados, "conteudo_bruto": conteudo[:5000]}


def montar_registro_manifest(linha: dict[str, Any], endereco: str,
                             source_line: int) -> dict[str, Any]:
    """Linha da listagem -> registro de manifest no contrato do pipeline."""
    texto = linha.get("texto", "")
    partes = [p.strip() for p in texto.split("|") if p.strip()]
    nome_raw = partes[0] if partes else ""
    unidade_raw = partes[1] if len(partes) > 1 else ""
    tipo_pessoa = "Morador" if "morador" in texto.lower() else "Proprietário"

    unidade = parse_unidade(unidade_raw)
    name_canonical = canonicalizar_texto(nome_raw)
    address_canonical = canonicalizar_texto(endereco)
    unit_canonical = unidade.get("unidade_imovel_canonical", canonicalizar_texto(unidade_raw))
    vaga_canonical = unidade.get("unidade_vaga_canonical", "")

    return {
        "name_raw": nome_raw,
        "name_canonical": name_canonical,
        "address_raw": endereco,
        "address_canonical": address_canonical,
        "unit_raw": unidade_raw,
        "unit_canonical": unit_canonical,
        "unidade_vaga_raw": unidade.get("unidade_vaga_raw", ""),
        "unidade_vaga_canonical": vaga_canonical,
        "tipo_unidade": classificar_tipo_unidade(unit_canonical, vaga_canonical),
        "tipo_pessoa": tipo_pessoa,
        "entity_type": classificar_entidade(nome_raw),
        "source_system": "eemovel",
        "source_line": source_line,
        "source_record_id": None,
        "record_key": gerar_record_key_v2(
            name_canonical, unit_canonical, vaga_canonical, address_canonical
        ),
        "state": "inventariado",
        "timestamp": timestamp_iso(),
    }


def dados_modal_do_detalhe(registro: dict[str, Any], detalhe: dict[str, Any]) -> dict[str, Any]:
    """Monta o `dados_modal` esperado por processar_modal_eemovel."""
    telefones = [
        {"numero": t, "principal": i == 0, "tipo": ""}
        for i, t in enumerate(detalhe.get("telefones", []))
    ]
    emails = [
        {"endereco": e, "principal": i == 0, "tipo": ""}
        for i, e in enumerate(detalhe.get("emails", []))
    ]
    cpf = (detalhe.get("cpfs") or [""])[0]
    return {
        "nome_completo": registro["name_raw"],
        "tipo_pessoa": registro["tipo_pessoa"],
        "endereco_principal": registro["address_raw"],
        "unidade": registro["unit_raw"],
        "inscricao": "",
        "idade": None,
        "data_nascimento": None,
        "cpf": cpf,
        "rg": "",
        "obito": False,
        "telefones": telefones,
        "emails": emails,
        "enderecos_adicionais": [],
        "imovel_detalhes": {},
        "metadata": {
            "metodo_extracao": "browser_agent_browser",
            "modal_completo": bool(telefones or emails or cpf),
            "timestamp_extracao": timestamp_iso(),
        },
    }


class Lote:
    """Lote com manifest NDJSON append-only + checkpoint retomável."""

    def __init__(self, nome_lote: str, diretorio_base: str | None = None):
        self.nome = nome_lote
        base = diretorio_base or str(AGENTE_DIR.parent)
        self.estrutura = criar_estrutura_lote(nome_lote, base)
        self.manifest_path = self.estrutura["manifest"] / f"manifest_{nome_lote}.ndjson"
        self.checkpoint_path = self.estrutura["checkpoints"] / "runner_checkpoint.json"

    def append_manifest(self, registro: dict[str, Any]) -> None:
        with open(self.manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

    def ler_checkpoint(self) -> dict[str, Any]:
        if self.checkpoint_path.exists():
            with open(self.checkpoint_path, encoding="utf-8") as f:
                return json.load(f)
        return {"ultimo_idx": -1, "processados": []}

    def salvar_checkpoint(self, ultimo_idx: int, processados: list[str]) -> None:
        salvar_json_seguro(
            {"ultimo_idx": ultimo_idx, "processados": processados,
             "atualizado_em": timestamp_iso()},
            self.checkpoint_path,
        )

    def persistir(self, registro: dict[str, Any], dados_modal: dict[str, Any]) -> None:
        processado = processar_modal_eemovel(dados_modal)
        persistir_proprietario(processado, registro, self.estrutura, self.nome)


# ---------------------------------------------------------------------------
# Modos de execução
# ---------------------------------------------------------------------------

def rodar_live(args: argparse.Namespace) -> None:
    sel = carregar_seletores()
    ab = AgentBrowser()
    lote = Lote(args.lote)

    garantir_login(ab, sel)
    if args.calibrate:
        snapshot = ab.snapshot()
        dump = lote.estrutura["logs"] / f"calibrate_{timestamp_iso().replace(':', '')}.txt"
        dump.write_text(snapshot, encoding="utf-8")
        print(f"[calibrate] snapshot salvo em {dump} — ajuste selectors.json se necessário")
        return

    buscar_endereco(ab, sel, args.endereco, args.cidade, args.num_inicial, args.num_final)
    linhas = extrair_listagem(ab, sel)
    if not linhas:
        raise SystemExit("Nenhuma linha extraída — rode `calibrate`.")

    limite = min(args.max_consultas, len(linhas))
    ckpt = lote.ler_checkpoint()
    processados: list[str] = list(ckpt.get("processados", []))

    for idx in range(ckpt["ultimo_idx"] + 1, limite):
        registro = montar_registro_manifest(linhas[idx], args.endereco, idx + 1)
        lote.append_manifest(registro)

        detalhe = extrair_detalhe(ab, sel, idx)
        if detalhe is None:
            print(f"[{idx}] detalhe indisponível — registro fica 'inventariado'")
        else:
            dados_modal = dados_modal_do_detalhe(registro, detalhe)
            lote.persistir(registro, dados_modal)
            registro["state"] = "extraido"
            processados.append(registro["record_key"])
            print(f"[{idx}] {registro['name_raw']}: "
                  f"{len(dados_modal['telefones'])} tel, {len(dados_modal['emails'])} emails")

        lote.salvar_checkpoint(idx, processados)

    print(f"[fim] lote={args.lote} manifest={lote.manifest_path} processados={len(processados)}")


def rodar_mock(args: argparse.Namespace) -> None:
    """Pipeline completo sem browser: input JSON com linhas de listagem."""
    with open(args.input, encoding="utf-8") as f:
        linhas = json.load(f)
    lote = Lote(args.lote)
    processados = []
    for idx, linha in enumerate(linhas):
        endereco = linha.get("endereco", args.endereco)
        registro = montar_registro_manifest(linha, endereco, idx + 1)
        lote.append_manifest(registro)
        detalhe = parse_texto_livre(linha.get("detalhe_texto", "") or linha.get("texto", ""))
        dados_modal = dados_modal_do_detalhe(registro, detalhe)
        lote.persistir(registro, dados_modal)
        registro["state"] = "extraido"
        processados.append(registro["record_key"])
    salvar_json_seguro(
        {"processados": processados, "total": len(processados)},
        lote.estrutura["checkpoints"] / "mock_result.json",
    )
    print(f"[mock] {len(processados)} registros processados em {lote.estrutura['base']}")


def _parse_endereco(endereco: str) -> tuple[str, str]:
    """Divide 'Rua X, 100' em (street, number)."""
    m = re.match(r"^(.*?)[,\s]+(\d+)\s*$", endereco.strip())
    if m:
        return m.group(1).strip().rstrip(","), m.group(2)
    return endereco.strip(), ""


def rodar_batch_json(args: argparse.Namespace) -> None:
    """Modo para o ExtractorService (API): imprime JSON no contrato do agente.

    login -> busca -> listagem -> detalhe (limitado) -> JSON array:
    [{"nome", "id" (record_key), "telefones": [str], "emails": [str],
      "unidade", "endereco", "tipo"}]
    """
    sel = carregar_seletores()
    ab = AgentBrowser()
    garantir_login(ab, sel)
    buscar_endereco(ab, sel, args.endereco, args.cidade, args.num_inicial, args.num_final)
    linhas = extrair_listagem(ab, sel)

    records: list[dict[str, Any]] = []
    limite = min(args.max_consultas, len(linhas))
    rua, numero = _parse_endereco(args.endereco)
    for idx, linha in enumerate(linhas):
        registro = montar_registro_manifest(linha, args.endereco, idx + 1)
        telefones: list[str] = []
        emails: list[str] = []
        if idx < limite:
            detalhe = extrair_detalhe(ab, sel, idx)
            if detalhe:
                telefones = detalhe.get("telefones", [])
                emails = detalhe.get("emails", [])
        records.append({
            "nome": registro["name_raw"],
            "id": registro["record_key"],
            "telefones": telefones,
            "emails": emails,
            "unidade": registro["unit_raw"],
            "endereco": registro["address_raw"],
            "street": rua,
            "number": numero,
            "city": args.cidade,
            "tipo": "morador" if registro["tipo_pessoa"] == "Morador" else "proprietario",
        })

    json.dump(records, sys.stdout, ensure_ascii=False, indent=2)
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="Runner EEmóvel via agent-browser")
    sub = ap.add_subparsers(dest="modo", required=True)

    p_live = sub.add_parser("live", help="extração real via agent-browser")
    p_live.add_argument("--endereco", required=True)
    p_live.add_argument("--cidade", default="")
    p_live.add_argument("--num-inicial", type=int, default=1)
    p_live.add_argument("--num-final", type=int, default=200)
    p_live.add_argument("--lote", default=None)
    p_live.add_argument("--max-consultas", type=int, default=5)
    p_live.add_argument("--calibrate", action="store_true",
                        help="só faz login e salva snapshot para calibrar seletores")

    p_mock = sub.add_parser("mock-input", help="pipeline sem browser (testes)")
    p_mock.add_argument("--input", required=True)
    p_mock.add_argument("--endereco", default="")
    p_mock.add_argument("--lote", default=None)

    p_batch = sub.add_parser("batch-json", help="JSON no contrato do EEmovelAgent (API)")
    p_batch.add_argument("--endereco", required=True)
    p_batch.add_argument("--cidade", default="")
    p_batch.add_argument("--num-inicial", type=int, default=1)
    p_batch.add_argument("--num-final", type=int, default=200)
    p_batch.add_argument("--max-consultas", type=int, default=10)

    args = ap.parse_args()
    if args.lote is None and args.modo == "live":
        slug = canonicalizar_texto(args.endereco)[:40].replace(" ", "_")
        args.lote = f"runner_{slug}_eemovel"

    if args.modo == "live":
        rodar_live(args)
    elif args.modo == "batch-json":
        rodar_batch_json(args)
    else:
        rodar_mock(args)


if __name__ == "__main__":
    main()
