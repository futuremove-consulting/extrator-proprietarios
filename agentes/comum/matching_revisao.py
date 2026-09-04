"""Matching fuzzy com banda de revisao (Estrategia de Cascata - item 1).

Melhorias sobre o fuzzy original (identity_resolution.agrupar_por_fuzzy):
- Nome por tokens com tolerancia a abreviatura por prefixo (AP x APARECIDA = 0.8).
- Unidade ESTRUTURAL: o numero do imovel domina; AP 10 x AP 20 nunca casa automatico.
- Banda: auto_merge >= 0.92; revisao 0.75-0.92; nao_merge < 0.75.
- A banda de revisao NAO e mesclada automaticamente: gera pares para decisao humana.
"""

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

from comum import parse_unidade
from comum.identity_resolution import IdentityGroup, SourceRecord, similaridade_strings

AUTO_MERGE_THRESHOLD = 0.92
REVIEW_THRESHOLD = 0.75

PESO_NOME = 0.55
PESO_UNIDADE = 0.30
PESO_ENDERECO = 0.15

TOKENS_IGNORADOS = {"de", "da", "do", "das", "dos", "e", "sr", "sra", "srta", "dr", "dra"}

TIPO_CANON = {
    "apartamento": "ap", "apto": "ap", "apt": "ap", "ap": "ap",
    "vaga": "vg", "garagem": "vg", "box": "vg", "vg": "vg",
    "bloco": "bl", "bl": "bl",
    "cobertura": "cob", "cob": "cob",
    "terreo": "ter", "ter": "ter",
    "fundos": "fund", "fund": "fund",
    "casa": "casa", "sala": "sala", "loja": "loja",
    "garden": "garden", "torre": "torre",
    "cj": "cj", "conjunto": "cj",
    "lt": "lt", "lote": "lt", "qd": "qd", "quadra": "qd",
}
TIPOS_CONHECIDOS = set(TIPO_CANON.values())

UNIT_TOKENS_IGNORADOS = {"e", "com", "and"}


def _canon(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower().strip()


def tokens_nome(nome: str) -> List[str]:
    toks = [t for t in re.split(r"[^a-z0-9]+", _canon(nome)) if t]
    return [t for t in toks if t not in TOKENS_IGNORADOS]


def _similar_token(t1: str, t2: str) -> float:
    if t1 == t2:
        return 1.0
    if len(t1) >= 2 and len(t2) >= 2 and (t1.startswith(t2) or t2.startswith(t1)):
        return 0.8
    ratio = SequenceMatcher(None, t1, t2).ratio()
    if ratio >= 0.85:
        return ratio * 0.9
    return 0.0


def similaridade_nomes(nome_a: str, nome_b: str) -> float:
    """Nome por tokens (abreviatura tolerada) + SequenceMatcher nos tokens ordenados."""
    ta, tb = tokens_nome(nome_a), tokens_nome(nome_b)
    if not ta or not tb:
        return 0.0
    if ta == tb:
        return 1.0

    def direcao(x: List[str], y: List[str]) -> float:
        total = 0.0
        for tx in x:
            total += max(_similar_token(tx, ty) for ty in y)
        return total / len(x)

    por_token = (direcao(ta, tb) + direcao(tb, ta)) / 2.0
    seq = SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    return 0.7 * por_token + 0.3 * seq


def _canon_parte(parte: str) -> str:
    out = []
    for t in re.split(r"[^a-z0-9]+", _canon(parte)):
        if not t or t in UNIT_TOKENS_IGNORADOS:
            continue
        t = TIPO_CANON.get(t, t)
        if t.isdigit():
            t = t.lstrip("0") or "0"
        out.append(t)
    return " ".join(out)


def _partes_unidade(unidade_raw: str) -> List[str]:
    partes = re.split(r",\s*|\s+\+\s+|\s{2,}|\s+e\s+|\s+com\s+", _canon(unidade_raw or ""))
    return [p.strip() for p in partes if p.strip()]


def _componentes_unidade(unidade_raw: str) -> List[Dict]:
    comps = []
    for parte in _partes_unidade(unidade_raw):
        parsed = parse_unidade(parte)
        for campo in ("unidade_imovel", "unidade_vaga"):
            bruto = (parsed.get(campo) or "").strip()
            if not bruto:
                continue
            for parte2 in re.split(r";\s*", bruto):
                if not parte2.strip():
                    continue
                canon = _canon_parte(parte2)
                if not canon:
                    continue
                toks = canon.split()
                numeros = {t for t in toks if t.isdigit()}
                tipos = {t for t in toks if not t.isdigit()}
                letras = {t for t in tipos if len(t) == 1 and t not in TIPOS_CONHECIDOS}
                comps.append({
                    "campo": campo,
                    "canon": canon,
                    "numeros": numeros,
                    "tipos_puros": tipos - letras,
                    "letras": letras,
                })
    return comps


def _similar_componente(a: Dict, b: Dict) -> float:
    if a["canon"] == b["canon"]:
        return 1.0
    na, nb = a["numeros"], b["numeros"]
    if na and nb:
        base = 1.0 if (na & nb) else 0.1
    elif not na and not nb:
        base = 0.6
    else:
        base = 0.4
    ta, tb = a["tipos_puros"], b["tipos_puros"]
    if ta and tb and not (ta & tb):
        base *= 0.6
    la, lb = a["letras"], b["letras"]
    if la and lb and not (la & lb):
        base *= 0.5
    elif (la or lb) and not (la & lb):
        base *= 0.8
    return base


def _similar_grupos(ga: List[Dict], gb: List[Dict], neutro_um_vazio: float) -> float:
    if not ga and not gb:
        return 1.0
    if not ga or not gb:
        return neutro_um_vazio

    def media(x, y):
        return sum(max(_similar_componente(a, c) for c in y) for a in x) / len(x)

    return (media(ga, gb) + media(gb, ga)) / 2.0


def similaridade_unidades(unidade_a: str, unidade_b: str) -> float:
    """Unidade estrutural: imovel pesa 0.75, vaga 0.25; numero divergente derruba o imovel."""
    if not unidade_a or not unidade_b:
        return 0.5
    ca, cb = _componentes_unidade(unidade_a), _componentes_unidade(unidade_b)
    if not ca or not cb:
        return similaridade_strings(unidade_a, unidade_b)
    im_a = [c for c in ca if c["campo"] == "unidade_imovel"]
    im_b = [c for c in cb if c["campo"] == "unidade_imovel"]
    vg_a = [c for c in ca if c["campo"] == "unidade_vaga"]
    vg_b = [c for c in cb if c["campo"] == "unidade_vaga"]
    sim_im = _similar_grupos(im_a, im_b, 0.5)
    sim_vg = _similar_grupos(vg_a, vg_b, 0.8)
    return 0.75 * sim_im + 0.25 * sim_vg


@dataclass
class AvaliacaoPar:
    pair_id: str
    r1: SourceRecord
    r2: SourceRecord
    sim_nome: float
    sim_unidade: float
    sim_endereco: float
    score: float
    classificacao: str  # 'auto_merge' | 'revisao' | 'nao_merge'


def gerar_pair_id(key_a: str, key_b: str) -> str:
    par = "|".join(sorted([key_a or "", key_b or ""]))
    return hashlib.sha1(par.encode("utf-8")).hexdigest()[:16]


def avaliar_par(r1: SourceRecord, r2: SourceRecord) -> AvaliacaoPar:
    nome_a = r1.name_raw or r1.name_canonical
    nome_b = r2.name_raw or r2.name_canonical
    un_a = r1.unit_raw or r1.unit_canonical
    un_b = r2.unit_raw or r2.unit_canonical
    en_a = r1.address_raw or r1.address_canonical
    en_b = r2.address_raw or r2.address_canonical
    sim_nome = similaridade_nomes(nome_a, nome_b)
    sim_un = similaridade_unidades(un_a, un_b)
    sim_end = similaridade_strings(en_a, en_b)
    score = PESO_NOME * sim_nome + PESO_UNIDADE * sim_un + PESO_ENDERECO * sim_end
    if score >= AUTO_MERGE_THRESHOLD:
        cls = "auto_merge"
    elif score >= REVIEW_THRESHOLD:
        cls = "revisao"
    else:
        cls = "nao_merge"
    return AvaliacaoPar(
        pair_id=gerar_pair_id(r1.record_key, r2.record_key),
        r1=r1, r2=r2,
        sim_nome=sim_nome, sim_unidade=sim_un, sim_endereco=sim_end,
        score=score, classificacao=cls,
    )


def listar_pares(records: List[SourceRecord]) -> Tuple[List[AvaliacaoPar], List[AvaliacaoPar]]:
    """Compara pares cross-origem (mesmo tipo_pessoa), pulando os ja casados por chave/CPF."""
    auto: List[AvaliacaoPar] = []
    revisao: List[AvaliacaoPar] = []
    n = len(records)
    for i in range(n):
        r1 = records[i]
        for j in range(i + 1, n):
            r2 = records[j]
            if r1.source == r2.source:
                continue
            if r1.tipo_pessoa != r2.tipo_pessoa:
                continue
            if r1.record_key and r1.record_key == r2.record_key:
                continue
            if r1.cpf and r1.cpf == r2.cpf:
                continue
            aval = avaliar_par(r1, r2)
            if aval.classificacao == "auto_merge":
                auto.append(aval)
            elif aval.classificacao == "revisao":
                revisao.append(aval)
    auto.sort(key=lambda p: -p.score)
    revisao.sort(key=lambda p: -p.score)
    return auto, revisao


def _union_find_aplicar(pares: List[AvaliacaoPar]) -> Dict[int, List[SourceRecord]]:
    parent: Dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for p in pares:
        union(id(p.r1), id(p.r2))
    grupos: Dict[int, List[SourceRecord]] = {}
    for p in pares:
        for r in (p.r1, p.r2):
            raiz = find(id(r))
            if all(id(m) != id(r) for m in grupos.get(raiz, [])):
                grupos.setdefault(raiz, []).append(r)
    return grupos


def agrupar_por_fuzzy_v2(records: List[SourceRecord]) -> Tuple[List[IdentityGroup], List[AvaliacaoPar]]:
    """Substituto do agrupar_por_fuzzy: so auto-mergea >= 0.92; devolve banda de revisao separada."""
    auto, revisao = listar_pares(records)
    grupos = _union_find_aplicar(auto)
    saida = [
        IdentityGroup(
            records=membros,
            identity_keys={"fuzzy_v2": sorted(set(m.source for m in membros))},
            confidence=0.93,
            match_type="fuzzy_v2",
        )
        for membros in grupos.values()
        if len(membros) > 1
    ]
    saida.sort(key=lambda g: -len(g.records))
    return saida, revisao


def aplicar_decisoes(
    revisao: List[AvaliacaoPar],
    decisoes: Dict[str, str],
    auto: List[AvaliacaoPar] = None,
) -> Tuple[List[IdentityGroup], Dict]:
    """Aplica decisoes humanas ({pair_id: 'aceito'|'rejeitado'}) sobre a banda de revisao."""
    auto = auto or []
    aceitos = [p for p in revisao if decisoes.get(p.pair_id) == "aceito"]
    rejeitados = [p for p in revisao if decisoes.get(p.pair_id) == "rejeitado"]
    pendentes = [p for p in revisao if p.pair_id not in decisoes]
    grupos = _union_find_aplicar(list(auto) + aceitos)
    saida = [
        IdentityGroup(
            records=membros,
            identity_keys={"membros": len(membros)},
            confidence=0.9,
            match_type="fuzzy_v2_revisado",
        )
        for membros in grupos.values()
        if len(membros) > 1
    ]
    resumo = {
        "pares_auto": len(auto),
        "pares_aceitos": len(aceitos),
        "pares_rejeitados": len(rejeitados),
        "pares_pendentes": len(pendentes),
        "grupos_finais": len(saida),
    }
    return saida, resumo
