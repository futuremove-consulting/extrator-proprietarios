"""Políticas de merge por campo para consolidação multi-origem."""

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class MergeStrategy(str, Enum):
    """Estratégias de merge disponíveis."""
    MOST_COMPLETE = "most_complete"          # Maior string não-vazia / mais completo
    NON_NULL_PRIORITY = "non_null_priority"  # Primeiro não-nulo (ordem de prioridade)
    UNION_DEDUP = "union_dedup"              # União deduplicada
    UNION_ALL = "union_all"                  # União sem deduplicação
    SOURCE_PRIORITY = "source_priority"      # Prioridade por origem
    RECALCULATE = "recalculate"              # Recalcular no Golden Record
    MOST_RECENT = "most_recent"              # Mais recente (por timestamp)
    CAPTEI_PRIORITY = "captei_priority"      # Captei vence (WhatsApp)


# Ordem de prioridade das origens (para SOURCE_PRIORITY)
SOURCE_PRIORITY_ORDER = ['fisgar', 'captei', 'eemovel']  # Fisgar tem CPF/RG, Captei tem WhatsApp, EEmovel tem mais detalhes


@dataclass
class FieldMergePolicy:
    """Política de merge para um campo específico."""
    strategy: MergeStrategy
    source_priority: Optional[List[str]] = None
    custom_fn: Optional[Callable] = None
    description: str = ""


# Políticas de merge por campo (conforme especificação)
MERGE_POLICIES: Dict[str, FieldMergePolicy] = {
    # Identificação
    "nome_completo": FieldMergePolicy(
        strategy=MergeStrategy.MOST_COMPLETE,
        description="Maior string não-vazia (nome mais completo)"
    ),
    
    "tipo_pessoa": FieldMergePolicy(
        strategy=MergeStrategy.SOURCE_PRIORITY,
        source_priority=['fisgar', 'captei', 'eemovel'],
        description="Proprietário > Morador (Fisgar/Captei são proprietários)"
    ),
    
    "cpf": FieldMergePolicy(
        strategy=MergeStrategy.NON_NULL_PRIORITY,
        source_priority=['fisgar', 'eemovel', 'captei'],  # Fisgar e EEmovel têm CPF
        description="Primeiro CPF válido (Fisgar/EEmovel prioritários)"
    ),
    
    "rg": FieldMergePolicy(
        strategy=MergeStrategy.NON_NULL_PRIORITY,
        source_priority=['fisgar', 'captei', 'eemovel'],
        description="Primeiro RG válido (Fisgar prioritário)"
    ),
    
    # Contato
    "telefones": FieldMergePolicy(
        strategy=MergeStrategy.UNION_DEDUP,
        description="União de todos os telefones, deduplicados por dígitos"
    ),
    
    "emails": FieldMergePolicy(
        strategy=MergeStrategy.UNION_DEDUP,
        description="União de todos os emails, deduplicados por lowercase"
    ),
    
    "whatsapp_status": FieldMergePolicy(
        strategy=MergeStrategy.CAPTEI_PRIORITY,
        description="Só Captei tem validação WhatsApp"
    ),
    
    # Endereços
    "endereco_principal": FieldMergePolicy(
        strategy=MergeStrategy.MOST_COMPLETE,
        description="Endereço mais completo"
    ),
    
    "unidade": FieldMergePolicy(
        strategy=MergeStrategy.MOST_COMPLETE,
        description="Unidade mais completa/descritiva"
    ),
    
    "enderecos_adicionais": FieldMergePolicy(
        strategy=MergeStrategy.UNION_ALL,
        description="Todos os endereços adicionais (só EEmovel tem)"
    ),
    
    # Dados pessoais
    "data_nascimento": FieldMergePolicy(
        strategy=MergeStrategy.NON_NULL_PRIORITY,
        source_priority=['fisgar', 'eemovel', 'captei'],
        description="Primeira data de nascimento válida"
    ),
    
    "idade": FieldMergePolicy(
        strategy=MergeStrategy.MOST_RECENT,
        description="Idade mais recente (calculada da data de nascimento)"
    ),
    
    "obito": FieldMergePolicy(
        strategy=MergeStrategy.NON_NULL_PRIORITY,
        source_priority=['fisgar', 'eemovel', 'captei'],
        description="Informação de óbito (qualquer origem)"
    ),
    
    # Dados do imóvel
    "imovel_detalhes": FieldMergePolicy(
        strategy=MergeStrategy.MOST_COMPLETE,
        source_priority=['eemovel', 'fisgar', 'captei'],  # EEmovel tem mais detalhes
        description="EEmovel tem dados mais ricos (área, padrão, ano)"
    ),
    
    # Qualidade e metadata
    "quality": FieldMergePolicy(
        strategy=MergeStrategy.RECALCULATE,
        description="Recalcular qualidade no Golden Record combinado"
    ),
}


def merge_most_complete(values: List[Any], sources: List[str]) -> Any:
    """Retorna o valor mais completo (maior string, dict com mais chaves, etc.)."""
    non_null = [(v, s) for v, s in zip(values, sources) if v not in [None, '', [], {}]]
    if not non_null:
        return None
    
    # Para strings: maior comprimento
    if isinstance(non_null[0][0], str):
        return max(non_null, key=lambda x: len(x[0]))[0]
    
    # Para dicts: mais chaves
    if isinstance(non_null[0][0], dict):
        return max(non_null, key=lambda x: len(x[0]))[0]
    
    # Para listas: maior
    if isinstance(non_null[0][0], list):
        return max(non_null, key=lambda x: len(x[0]))[0]
    
    return non_null[0][0]


def merge_non_null_priority(values: List[Any], sources: List[str], 
                            priority_order: List[str]) -> Any:
    """Retorna o primeiro valor não-nulo seguindo ordem de prioridade das origens."""
    # Criar mapa source -> value
    source_to_value = {s: v for v, s in zip(values, sources) if v not in [None, '', [], {}]}
    
    for source in priority_order:
        if source in source_to_value:
            return source_to_value[source]
    
    # Fallback: primeiro não-nulo qualquer
    for v, s in zip(values, sources):
        if v not in [None, '', [], {}]:
            return v
    return None


def merge_union_dedup(values: List[List[Any]], sources: List[str], 
                      key_fn: Callable = lambda x: x) -> List[Any]:
    """Une listas deduplicando por função de chave."""
    seen = set()
    result = []
    for val_list, source in zip(values, sources):
        if not val_list:
            continue
        for item in val_list:
            key = key_fn(item)
            if key and key not in seen:
                seen.add(key)
                result.append(item)
    return result


def merge_union_all(values: List[List[Any]], sources: List[str]) -> List[Any]:
    """Une todas as listas sem deduplicação."""
    result = []
    for val_list in values:
        if val_list:
            result.extend(val_list)
    return result


def merge_source_priority(values: List[Any], sources: List[str],
                          priority_order: List[str]) -> Any:
    """Seleciona valor baseado na prioridade da origem."""
    source_to_value = {s: v for v, s in zip(values, sources) if v not in [None, '', [], {}]}
    
    for source in priority_order:
        if source in source_to_value:
            return source_to_value[source]
    
    return None


def merge_captei_priority(values: List[Any], sources: List[str]) -> Any:
    """Prioriza valor do Captei (para WhatsApp status)."""
    for v, s in zip(values, sources):
        if s == 'captei' and v not in [None, '', [], {}]:
            return v
    # Fallback: primeiro não-nulo
    for v in values:
        if v not in [None, '', [], {}]:
            return v
    return None


def merge_recalculate(values: List[Any], sources: List[str], 
                      context: Dict[str, Any] = None) -> Any:
    """Placeholder para recálculo no Golden Record (implementado no scoring)."""
    return None


def apply_merge_policy(field_name: str, values: List[Any], sources: List[str],
                       context: Dict[str, Any] = None) -> Any:
    """Aplica a política de merge apropriada para um campo."""
    policy = MERGE_POLICIES.get(field_name)
    
    if not policy:
        # Default: primeiro não-nulo
        for v in values:
            if v not in [None, '', [], {}]:
                return v
        return None
    
    if policy.custom_fn:
        return policy.custom_fn(values, sources, context)
    
    if policy.strategy == MergeStrategy.MOST_COMPLETE:
        return merge_most_complete(values, sources)
    
    elif policy.strategy == MergeStrategy.NON_NULL_PRIORITY:
        return merge_non_null_priority(values, sources, 
                                       policy.source_priority or SOURCE_PRIORITY_ORDER)
    
    elif policy.strategy == MergeStrategy.UNION_DEDUP:
        # Determinar key_fn baseado no campo
        if field_name == 'telefones':
            from comum import extrair_digitos_telefone
            key_fn = extrair_digitos_telefone
        elif field_name == 'emails':
            key_fn = lambda x: x.lower().strip()
        else:
            key_fn = lambda x: x
        return merge_union_dedup(values, sources, key_fn)
    
    elif policy.strategy == MergeStrategy.UNION_ALL:
        return merge_union_all(values, sources)
    
    elif policy.strategy == MergeStrategy.SOURCE_PRIORITY:
        return merge_source_priority(values, sources,
                                     policy.source_priority or SOURCE_PRIORITY_ORDER)
    
    elif policy.strategy == MergeStrategy.CAPTEI_PRIORITY:
        return merge_captei_priority(values, sources)
    
    elif policy.strategy == MergeStrategy.MOST_RECENT:
        # Assumir que valores têm timestamp ou usar fonte mais recente
        return merge_most_complete(values, sources)
    
    elif policy.strategy == MergeStrategy.RECALCULATE:
        return None  # Será calculado depois
    
    return None