"""Módulo de scoring de confiança para Golden Records."""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from collections import defaultdict

from comum.merge_policies import MERGE_POLICIES, MergeStrategy


@dataclass
class FieldScore:
    """Score de confiança para um campo específico."""
    field: str
    value: Any
    confidence: float  # 0-1
    sources: List[str]
    provenance: Dict[str, str]  # field -> source que forneceu
    validation_flags: List[str] = field(default_factory=list)


@dataclass
class GoldenRecordScore:
    """Score completo do Golden Record."""
    overall_confidence: float  # 0-100
    field_scores: Dict[str, FieldScore]
    completeness: float  # 0-1 (% campos preenchidos)
    cross_source_agreement: float  # 0-1 (concordância entre origens)
    quality_tier: str  # 'high', 'medium', 'low', 'review_required'
    requires_manual_review: bool
    review_reasons: List[str] = field(default_factory=list)


# Pesos por campo para overall confidence
FIELD_WEIGHTS = {
    # Identidade forte
    'cpf': 0.20,
    'nome_completo': 0.15,
    'data_nascimento': 0.10,
    'rg': 0.05,
    
    # Contato
    'telefones': 0.10,
    'emails': 0.05,
    'whatsapp_status': 0.03,
    
    # Endereço/Imóvel
    'endereco_principal': 0.08,
    'unidade': 0.05,
    'enderecos_adicionais': 0.03,
    'imovel_detalhes': 0.05,
    
    # Tipo
    'tipo_pessoa': 0.05,
    'obito': 0.02,
    
    # Qualidade
    'quality': 0.04,
}


# Bonus/penalty por match type
MATCH_TYPE_BONUS = {
    'cpf_strong': 0.15,
    'record_key_exact': 0.10,
    'tel_name': 0.05,
    'fuzzy': -0.10,
}


def calcular_field_score(field_name: str, 
                         values: Dict[str, Any],  # source -> value
                         merged_value: Any,
                         match_type: str,
                         validation_flags: List[str]) -> FieldScore:
    """Calcula score de confiança para um campo específico."""
    
    sources = list(values.keys())
    num_sources = len([v for v in values.values() if v not in [None, '', [], {}]])
    
    # Base confidence por número de fontes concordantes
    if num_sources >= 3:
        base_conf = 0.95
    elif num_sources == 2:
        base_conf = 0.85
    elif num_sources == 1:
        base_conf = 0.60
    else:
        base_conf = 0.0
    
    # Bonus por tipo de match
    match_bonus = MATCH_TYPE_BONUS.get(match_type, 0)
    
    # Penalty por flags de validação
    validation_penalty = len(validation_flags) * 0.05
    
    # Bonus por qualidade da fonte (se campo tem policy de prioridade)
    policy = MERGE_POLICIES.get(field_name)
    source_quality_bonus = 0
    if policy and policy.strategy == MergeStrategy.SOURCE_PRIORITY and policy.source_priority:
        # Se o valor veio da fonte de maior prioridade
        if sources and sources[0] == policy.source_priority[0]:
            source_quality_bonus = 0.05
    
    confidence = min(1.0, max(0.0, base_conf + match_bonus - validation_penalty + source_quality_bonus))
    
    # Proveniência: qual source forneceu o valor final
    provenance = {}
    if merged_value is not None:
        # Encontrar qual source tem o valor mais similar ao merged
        for source, value in values.items():
            if value == merged_value or (isinstance(value, str) and value in str(merged_value)):
                provenance[field_name] = source
                break
        if field_name not in provenance and sources:
            provenance[field_name] = sources[0]
    
    return FieldScore(
        field=field_name,
        value=merged_value,
        confidence=confidence,
        sources=sources,
        provenance=provenance,
        validation_flags=validation_flags
    )


def calcular_golden_record_score(merged_record: Dict[str, Any],
                                  field_values: Dict[str, Dict[str, Any]],  # field -> {source: value}
                                  match_type: str,
                                  validation_results: List[Any]) -> GoldenRecordScore:
    """Calcula score completo do Golden Record."""
    
    # Agrupar validation flags por campo
    validation_by_field = defaultdict(list)
    for v in validation_results:
        validation_by_field[v.field].append(v.message)
    
    # Calcular score por campo
    field_scores = {}
    weighted_sum = 0.0
    total_weight = 0.0
    
    for field_name, weight in FIELD_WEIGHTS.items():
        if field_name in merged_record:
            values = field_values.get(field_name, {})
            merged_val = merged_record.get(field_name)
            flags = validation_by_field.get(field_name, [])
            
            fs = calcular_field_score(field_name, values, merged_val, match_type, flags)
            field_scores[field_name] = fs
            
            weighted_sum += fs.confidence * weight
            total_weight += weight
    
    # Overall confidence (0-100)
    overall_confidence = (weighted_sum / total_weight * 100) if total_weight > 0 else 0
    
    # Completeness: % de campos com valor
    fields_com_marca = sum(1 for v in merged_record.values() if v not in [None, '', [], {}])
    completeness = fields_com_marca / len(FIELD_WEIGHTS) if FIELD_WEIGHTS else 0
    
    # Cross-source agreement: média de concordância por campo
    agreement_scores = []
    for field_name, values in field_values.items():
        non_null = [v for v in values.values() if v not in [None, '', [], {}]]
        if len(non_null) >= 2:
            # Se todos iguais = 1.0, se diferentes = 0.5
            if len(set(str(v) for v in non_null)) == 1:
                agreement_scores.append(1.0)
            else:
                agreement_scores.append(0.5)
        elif len(non_null) == 1:
            agreement_scores.append(0.7)
        else:
            agreement_scores.append(0.0)
    
    cross_source_agreement = sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0
    
    # Quality tier
    requires_review = False
    review_reasons = []
    
    # Verificar validações de erro
    for v in validation_results:
        if hasattr(v, 'severity') and v.severity.value == 'error':
            requires_review = True
            review_reasons.append(f"Erro: {v.message}")
        elif hasattr(v, 'severity') and v.severity.value == 'warning' and 'consistency' in v.field:
            requires_review = True
            review_reasons.append(f"Aviso: {v.message}")
    
    if overall_confidence < 70:
        quality_tier = 'low'
        requires_review = True
        review_reasons.append(f"Confiança geral baixa: {overall_confidence:.0f}%")
    elif overall_confidence < 85:
        quality_tier = 'medium'
    elif overall_confidence >= 95 and completeness > 0.8:
        quality_tier = 'high'
    else:
        quality_tier = 'medium'
    
    if cross_source_agreement < 0.6:
        requires_review = True
        review_reasons.append(f"Baixa concordância cross-origem: {cross_source_agreement:.0%}")
    
    return GoldenRecordScore(
        overall_confidence=overall_confidence,
        field_scores=field_scores,
        completeness=completeness,
        cross_source_agreement=cross_source_agreement,
        quality_tier=quality_tier,
        requires_manual_review=requires_review,
        review_reasons=review_reasons
    )


def gerar_relatorio_scoring(score: GoldenRecordScore) -> str:
    """Gera relatório de scoring em markdown."""
    lines = []
    lines.append(f"# Scoring do Golden Record\n")
    lines.append(f"**Confiança Geral:** {score.overall_confidence:.1f}%")
    lines.append(f"**Completude:** {score.completeness:.1%}")
    lines.append(f"**Concordância Cross-Origem:** {score.cross_source_agreement:.1%}")
    lines.append(f"**Tier de Qualidade:** {score.quality_tier.upper()}")
    lines.append(f"**Revisão Manual:** {'SIM' if score.requires_manual_review else 'NÃO'}\n")
    
    if score.review_reasons:
        lines.append("## Motivos para Revisão")
        for r in score.review_reasons:
            lines.append(f"- {r}")
        lines.append("")
    
    lines.append("## Scores por Campo")
    lines.append("| Campo | Valor | Confiança | Fontes | Proveniência | Flags |")
    lines.append("|-------|-------|-----------|--------|--------------|-------|")
    
    for field_name, fs in sorted(score.field_scores.items(), key=lambda x: -x[1].confidence):
        val_str = str(fs.value)[:50] if fs.value else 'N/A'
        prov = fs.provenance.get(field_name, 'N/A')
        flags = ', '.join(fs.validation_flags) if fs.validation_flags else '—'
        lines.append(f"| {field_name} | {val_str} | {fs.confidence:.0%} | {', '.join(fs.sources) or '—'} | {prov} | {flags} |")
    
    return '\n'.join(lines)