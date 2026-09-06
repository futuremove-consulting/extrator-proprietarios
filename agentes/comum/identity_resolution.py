"""Módulo de resolução de identidade cross-origem para consolidação multi-origem."""

from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re

from comum import extrair_digitos_telefone


@dataclass
class SourceRecord:
    """Registro de uma origem específica (imutável, auditável)."""
    record_key: str
    source: str  # 'captei', 'fisgar', 'eemovel'
    source_record_id: str
    name_raw: str
    name_canonical: str
    unit_raw: str
    unit_canonical: str
    address_raw: str
    address_canonical: str
    entity_type: str
    tipo_pessoa: str  # 'Proprietário', 'Possível morador'
    cpf: str
    rg: str
    telefones: List[str]  # Apenas dígitos
    emails: List[str]  # Lowercase
    enderecos_adicionais: List[str]
    data_nascimento: str
    idade: Optional[int]
    obito: bool
    imovel_detalhes: Dict[str, Any]
    whatsapp_status: Optional[str]
    quality: str
    raw_payload: Dict[str, Any]
    provenance: Dict[str, Any] = field(default_factory=dict)  # field-level origin tracking


@dataclass
class IdentityGroup:
    """Grupo de SourceRecords que representam a mesma entidade real."""
    records: List[SourceRecord]
    identity_keys: Dict[str, Any]  # Chaves que determinaram o agrupamento
    confidence: float  # 0-1
    match_type: str  # 'cpf_strong', 'record_key_exact', 'tel_name', 'fuzzy', 'manual'


def normalizar_cpf(cpf: str) -> str:
    """Normaliza CPF para apenas dígitos."""
    if not cpf:
        return ''
    return re.sub(r'\D', '', cpf)


def normalizar_telefone(tel: str) -> str:
    """Normaliza telefone para apenas dígitos."""
    return extrair_digitos_telefone(tel)


def normalizar_email(email: str) -> str:
    """Normaliza email para lowercase."""
    return email.lower().strip() if email else ''


def similaridade_strings(s1: str, s2: str) -> float:
    """Calcula similaridade entre duas strings (0-1)."""
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1.upper(), s2.upper()).ratio()


def extrair_source_records(manifest_path: str, source: str) -> List[SourceRecord]:
    """Extrai SourceRecords de um manifest NDJSON."""
    import json
    records = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        for linha in f:
            if linha.strip():
                reg = json.loads(linha)
                # Só processar PF e moradores (não empresas)
                if reg.get('entity_type') not in ['Pessoa Fisica', 'Pessoa Física']:
                    continue
                
                # Extrair telefones como dígitos
                tels = []
                for t in reg.get('telefones', []):
                    num = t.get('numero_raw') or t.get('numero', '')
                    if num:
                        tels.append(normalizar_telefone(num))
                
                # Extrair emails
                emails = []
                for e in reg.get('emails', []):
                    end = e.get('endereco_raw') or e.get('endereco', '')
                    if end:
                        emails.append(normalizar_email(end))
                
                # CPF normalizado
                cpf_raw = reg.get('cpf', '') or reg.get('dados_extraidos', {}).get('detalhes', {}).get('cpf', '')
                cpf = normalizar_cpf(cpf_raw)
                
                # RG normalizado
                rg_raw = reg.get('rg', '') or reg.get('dados_extraidos', {}).get('detalhes', {}).get('rg', '')
                rg = normalizar_cpf(rg_raw)  # RG também usa só dígitos
                
                # Óbito
                obito = reg.get('obito', False) or reg.get('dados_extraidos', {}).get('detalhes', {}).get('obito', False)
                
                record = SourceRecord(
                    record_key=reg.get('record_key', ''),
                    source=source,
                    source_record_id=reg.get('source_record_id', reg.get('record_key', '')),
                    name_raw=reg.get('name_raw', ''),
                    name_canonical=reg.get('name_canonical', ''),
                    unit_raw=reg.get('unit_raw', ''),
                    unit_canonical=reg.get('unit_canonical', ''),
                    address_raw=reg.get('address_raw', ''),
                    address_canonical=reg.get('address_canonical', ''),
                    entity_type=reg.get('entity_type', ''),
                    tipo_pessoa=reg.get('tipo_pessoa', 'Proprietário'),
                    cpf=cpf,
                    rg=rg,
                    telefones=tels,
                    emails=emails,
                    enderecos_adicionais=reg.get('enderecos_adicionais', 
                        reg.get('dados_extraidos', {}).get('enderecos_adicionais', [])),
                    data_nascimento=reg.get('data_nascimento', '') or 
                        reg.get('dados_extraidos', {}).get('detalhes', {}).get('data_nascimento', ''),
                    idade=reg.get('idade') or reg.get('dados_extraidos', {}).get('detalhes', {}).get('idade'),
                    obito=obito,
                    imovel_detalhes=reg.get('imovel_detalhes', 
                        reg.get('dados_extraidos', {}).get('imovel_detalhes', {})),
                    whatsapp_status=None,
                    quality=reg.get('quality') or 
                        reg.get('dados_extraidos', {}).get('metadata', {}).get('qualidade', 'baixa'),
                    raw_payload=reg
                )
                records.append(record)
    return records


def agrupar_por_cpf(records: List[SourceRecord]) -> Dict[str, List[SourceRecord]]:
    """Agrupa records por CPF normalizado (chave forte)."""
    grupos = defaultdict(list)
    for r in records:
        if r.cpf and len(r.cpf) >= 11:
            grupos[r.cpf].append(r)
    return {cpf: grp for cpf, grp in grupos.items() if len(grp) > 1}


def agrupar_por_record_key(records: List[SourceRecord]) -> Dict[str, List[SourceRecord]]:
    """Agrupa records por record_key exato (chave média)."""
    grupos = defaultdict(list)
    for r in records:
        if r.record_key:
            grupos[r.record_key].append(r)
    return {key: grp for key, grp in grupos.items() if len(grp) > 1}


def agrupar_por_telefone_nome(records: List[SourceRecord]) -> Dict[Tuple[str, str], List[SourceRecord]]:
    """Agrupa por telefone + nome canônico (chave fraca)."""
    grupos = defaultdict(list)
    for r in records:
        if r.telefones and r.name_canonical:
            # Usar o primeiro telefone como chave primária
            key = (r.telefones[0], r.name_canonical)
            grupos[key].append(r)
    return {key: grp for key, grp in grupos.items() if len(grp) > 1}


def agrupar_por_fuzzy(records: List[SourceRecord], 
                       threshold_nome: float = 0.90, 
                       threshold_end: float = 0.75) -> List[IdentityGroup]:
    """Agrupa por fuzzy matching de nome + endereço."""
    grupos = []
    usados = set()
    
    for i, r1 in enumerate(records):
        if id(r1) in usados:
            continue
        
        grupo = [r1]
        usados.add(id(r1))
        
        for j, r2 in enumerate(records[i+1:], i+1):
            if id(r2) in usados:
                continue
            
            # Só comparar mesmo tipo de pessoa
            if r1.tipo_pessoa != r2.tipo_pessoa:
                continue
            
            # Ignorar se mesma origem (já deduplicado)
            if r1.source == r2.source:
                continue
            
            sim_nome = similaridade_strings(r1.name_raw, r2.name_raw)
            sim_end = similaridade_strings(r1.address_raw, r2.address_raw)
            
            # Também verificar similaridade de nome canônico
            sim_nome_canon = similaridade_strings(r1.name_canonical, r2.name_canonical)
            
            # Match se nome muito similar E endereço similar
            # Ou nome canônico idêntico + endereço similar
            match = False
            if sim_nome >= threshold_nome and sim_end >= threshold_end:
                match = True
            elif sim_nome_canon >= 0.95 and sim_end >= 0.7:
                match = True
            
            if match:
                grupo.append(r2)
                usados.add(id(r2))
        
        if len(grupo) > 1:
            confidence = sum(
                similaridade_strings(g.name_raw, r1.name_raw) * 0.5 + 
                similaridade_strings(g.address_raw, r1.address_raw) * 0.3 +
                similaridade_strings(g.name_canonical, r1.name_canonical) * 0.2
                for g in grupo
            ) / len(grupo)
            grupos.append(IdentityGroup(
                records=grupo,
                identity_keys={'fuzzy_nome': r1.name_raw, 'fuzzy_end': r1.address_raw},
                confidence=confidence,
                match_type='fuzzy'
            ))
    
    return grupos


def resolver_identidade(records_por_origem: Dict[str, List[SourceRecord]]) -> Tuple[List[IdentityGroup], List[SourceRecord]]:
    """
    Resolve identidade cross-origem usando hierarquia de chaves:
    1. CPF (forte) - quando disponível em ≥2 origens
    2. record_key exato (médio) 
    3. telefone + nome canônico (fraco)
    4. fuzzy match (revisão manual)
    
    Returns:
        (grupos_multi_origem, records_sem_grupo)
    """
    # --- PRE-PROCESS: Deduplicar dentro de cada origem ---
    records_dedup_por_origem = {}
    for source, records in records_por_origem.items():
        # Deduplicar por record_key dentro da mesma origem
        seen_keys = set()
        dedup = []
        for r in records:
            if r.record_key not in seen_keys:
                seen_keys.add(r.record_key)
                dedup.append(r)
        records_dedup_por_origem[source] = dedup
        print(f"    {source}: {len(records)} -> {len(dedup)} (dedup intra-origem)")
    
    # Consolidar todos os records deduplicados
    todos_records = []
    for source, recs in records_dedup_por_origem.items():
        todos_records.extend(recs)
    
    # Rastrear quais records já foram agrupados
    grouped_ids = set()
    grupos_finais = []
    
    # --- NÍVEL 1: CPF Forte ---
    cpf_groups = agrupar_por_cpf(todos_records)
    for cpf, grp in cpf_groups.items():
        if len(set(r.source for r in grp)) >= 2:  # Pelo menos 2 origens
            grupo_id = IdentityGroup(
                records=grp,
                identity_keys={'cpf': cpf},
                confidence=0.95,
                match_type='cpf_strong'
            )
            grupos_finais.append(grupo_id)
            for r in grp:
                grouped_ids.add(id(r))
    
    # --- NÍVEL 2: Record Key Exato ---
    key_groups = agrupar_por_record_key([r for r in todos_records if id(r) not in grouped_ids])
    for key, grp in key_groups.items():
        if len(set(r.source for r in grp)) >= 2:
            grupo_id = IdentityGroup(
                records=grp,
                identity_keys={'record_key': key},
                confidence=0.85,
                match_type='record_key_exact'
            )
            grupos_finais.append(grupo_id)
            for r in grp:
                grouped_ids.add(id(r))
    
    # --- NÍVEL 3: Telefone + Nome ---
    tel_groups = agrupar_por_telefone_nome([r for r in todos_records if id(r) not in grouped_ids])
    for (tel, nome), grp in tel_groups.items():
        if len(set(r.source for r in grp)) >= 2:
            grupo_id = IdentityGroup(
                records=grp,
                identity_keys={'telefone': tel, 'nome_canonical': nome},
                confidence=0.75,
                match_type='tel_name'
            )
            grupos_finais.append(grupo_id)
            for r in grp:
                grouped_ids.add(id(r))
    
    # --- NÍVEL 4: Fuzzy Match (para revisão manual) ---
    remaining = [r for r in todos_records if id(r) not in grouped_ids]
    fuzzy_groups = agrupar_por_fuzzy(remaining)
    for g in fuzzy_groups:
        if len(set(r.source for r in g.records)) >= 2:
            g.confidence = min(g.confidence, 0.65)  # Cap confidence for fuzzy
            grupos_finais.append(g)
            for r in g.records:
                grouped_ids.add(id(r))
    
    # Records sem grupo (single-origin ou sem match)
    singles = [r for r in todos_records if id(r) not in grouped_ids]
    
    return grupos_finais, singles


def gerar_relatorio_grupos(grupos: List[IdentityGroup], singles: List[SourceRecord]) -> str:
    """Gera relatório de grupos de identidade."""
    lines = []
    lines.append("# Relatório de Resolução de Identidade Cross-Origem\n")
    
    lines.append("## Resumo")
    lines.append(f"- Grupos multi-origem: {len(grupos)}")
    lines.append(f"- Registros singles (sem match): {len(singles)}")
    lines.append(f"- Total registros processados: {len(grupos) * 2 + len(singles)} (aprox)\n")
    
    # Por tipo de match
    por_tipo = defaultdict(int)
    for g in grupos:
        por_tipo[g.match_type] += 1
    
    lines.append("## Grupos por Tipo de Match")
    for tipo, count in sorted(por_tipo.items()):
        lines.append(f"- {tipo}: {count}")
    lines.append("")
    
    # Detalhes dos grupos
    lines.append("## Detalhes dos Grupos")
    for i, g in enumerate(grupos, 1):
        lines.append(f"### Grupo {i} [{g.match_type}] (confidence: {g.confidence:.2f})")
        lines.append(f"- Chaves: {g.identity_keys}")
        for r in g.records:
            lines.append(f"  - {r.source}: {r.name_raw} | {r.unit_raw} | CPF: {r.cpf or 'N/A'} | Tel: {r.telefones[0] if r.telefones else 'N/A'}")
        lines.append("")
    
    return '\n'.join(lines)