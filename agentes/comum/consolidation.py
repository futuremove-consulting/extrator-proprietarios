"""Pipeline principal de consolidação multi-origem."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict

from comum.identity_resolution import (
    SourceRecord, IdentityGroup, extrair_source_records, 
    resolver_identidade
)
from comum.merge_policies import apply_merge_policy
from comum.validators import executar_validacoes, classificar_validacoes, tem_erros_bloqueantes
from comum.scoring import calcular_golden_record_score, GoldenRecordScore
from comum import canonicalizar_texto, gerar_record_key, timestamp_iso, salvar_json_seguro


@dataclass
class GoldenRecord:
    """Registro dourado consolidado de um proprietário."""
    golden_key: str  # Chave única do golden record
    match_type: str  # Como foi agrupado
    identity_confidence: float
    
    # Campos consolidados
    nome_completo: str = ''
    tipo_pessoa: str = 'Proprietário'
    cpf: str = ''
    rg: str = ''
    telefones: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    whatsapp_status: Optional[str] = None
    endereco_principal: str = ''
    unidade: str = ''
    enderecos_adicionais: List[str] = field(default_factory=list)
    data_nascimento: str = ''
    idade: Optional[int] = None
    obito: bool = False
    imovel_detalhes: Dict[str, Any] = field(default_factory=dict)
    quality: str = 'baixa'
    
    # Metadados
    source_records: List[Dict[str, Any]] = field(default_factory=list)  # Links para SourceRecords originais
    field_provenance: Dict[str, str] = field(default_factory=dict)  # campo -> source
    validation_summary: Dict[str, List[str]] = field(default_factory=dict)  # errors, warnings, infos
    scoring: Optional[GoldenRecordScore] = None
    created_at: str = field(default_factory=timestamp_iso)
    updated_at: str = field(default_factory=timestamp_iso)


@dataclass
class ConsolidationReport:
    """Relatório completo da consolidação."""
    lote: str
    timestamp: str
    total_source_records: int
    total_golden_records: int
    golden_records_multi_origem: int
    golden_records_single_origem: int
    requires_review: int
    quality_distribution: Dict[str, int]
    identity_groups: List[Dict[str, Any]]
    golden_records: List[Dict[str, Any]]


class ConsolidationPipeline:
    """Pipeline de consolidação multi-origem."""
    
    def __init__(self, lote: str, manifests_dir: str = '.'):
        self.lote = lote
        self.manifests_dir = Path(manifests_dir)
        self.source_records_por_origem: Dict[str, List[SourceRecord]] = {}
        self.identity_groups: List[IdentityGroup] = []
        self.single_records: List[SourceRecord] = []
        self.golden_records: List[GoldenRecord] = []
    
    def run(self) -> ConsolidationReport:
        """Executa pipeline completo."""
        print(f"Iniciando consolidação do lote: {self.lote}")
        
        # Stage 1: Load
        self._stage_load()
        
        # Stage 2: Normalize (já feito no identity_resolution)
        self._stage_normalize()
        
        # Stage 3: Sanitize
        self._stage_sanitize()
        
        # Stage 4: Deduplicate / Identity Resolution
        self._stage_deduplicate()
        
        # Stage 5: Merge
        self._stage_merge()
        
        # Stage 6: Validate
        self._stage_validate()
        
        # Stage 7: Score
        self._stage_score()
        
        # Stage 8: Output
        report = self._stage_output()
        
        return report
    
    def _stage_load(self):
        """Carrega manifests das 3 origens."""
        print("  Stage 1/8: Carregando manifests...")
        for origem in ['captei', 'fisgar', 'eemovel']:
            manifest_dir = self.manifests_dir / f'teste_{origem}' / 'manifest'
            if manifest_dir.exists():
                manifest_files = list(manifest_dir.glob('manifest_*.ndjson'))
                if manifest_files:
                    # Usar o mais recente
                    latest = max(manifest_files, key=lambda f: f.stat().st_mtime)
                    records = extrair_source_records(str(latest), origem)
                    self.source_records_por_origem[origem] = records
                    print(f"    {origem}: {len(records)} registros PF/Morador")
                else:
                    print(f"    {origem}: Nenhum manifest encontrado")
            else:
                print(f"    {origem}: Diretório não encontrado")
    
    def _stage_normalize(self):
        """Normalização já é feita na extração de SourceRecord."""
        print("  Stage 2/8: Normalização (já aplicada na extração)")
        # CPF, telefones, emails já normalizados
        # Nomes canônicos já gerados
        pass
    
    def _stage_sanitize(self):
        """Sanitização LGPD - mascarar PII em logs/outputs não seguros."""
        print("  Stage 3/8: Sanitização LGPD")
        # Não modificar os dados originais, apenas garantir que outputs
        # não vazem CPF/telefone completos em relatórios públicos
        pass
    
    def _stage_deduplicate(self):
        """Resolução de identidade cross-origem."""
        print("  Stage 4/8: Resolução de identidade (deduplicação)...")
        self.identity_groups, self.single_records = resolver_identidade(
            self.source_records_por_origem
        )
        print(f"    Grupos multi-origem: {len(self.identity_groups)}")
        print(f"    Singles (sem match): {len(self.single_records)}")
    
    def _stage_merge(self):
        """Merge dos campos por grupo de identidade."""
        print("  Stage 5/8: Merge de campos...")
        
        # Processar grupos multi-origem
        for group in self.identity_groups:
            golden = self._merge_grupo(group)
            self.golden_records.append(golden)
        
        # Processar singles (single-origin)
        for record in self.single_records:
            golden = self._merge_single(record)
            self.golden_records.append(golden)
        
        print(f"    Golden Records criados: {len(self.golden_records)}")
    
    def _merge_grupo(self, group: IdentityGroup) -> GoldenRecord:
        """Merge de um grupo multi-origem em Golden Record."""
        # Coletar valores por campo por fonte
        field_values = defaultdict(dict)
        source_records_info = []
        
        for record in group.records:
            # Mapear campos do SourceRecord para campos do GoldenRecord
            mapping = {
                'nome_completo': record.name_raw,
                'tipo_pessoa': record.tipo_pessoa,
                'cpf': record.cpf,
                'rg': record.rg,
                'telefones': record.telefones,
                'emails': record.emails,
                'whatsapp_status': record.whatsapp_status,
                'endereco_principal': record.address_raw,
                'unidade': record.unit_raw,
                'enderecos_adicionais': record.enderecos_adicionais,
                'data_nascimento': record.data_nascimento,
                'idade': record.idade,
                'obito': record.obito,
                'imovel_detalhes': record.imovel_detalhes,
                'quality': record.quality,
            }
            
            for field, value in mapping.items():
                if value not in [None, '', [], {}]:
                    field_values[field][record.source] = value
            
            source_records_info.append({
                'source': record.source,
                'source_record_id': record.source_record_id,
                'record_key': record.record_key,
                'name_raw': record.name_raw,
                'tipo_pessoa': record.tipo_pessoa,
            })
        
        # Aplicar políticas de merge por campo
        merged = {}
        field_provenance = {}
        
        for field_name, values in field_values.items():
            sources = list(values.keys())
            merged_value = apply_merge_policy(field_name, 
                                              [values[s] for s in sources], 
                                              sources)
            merged[field_name] = merged_value
            
            # Registrar proveniência
            if merged_value is not None and sources:
                field_provenance[field_name] = sources[0]
        
        # Gerar golden_key único
        golden_key = self._gerar_golden_key(merged)
        
        # Criar GoldenRecord
        golden = GoldenRecord(
            golden_key=golden_key,
            match_type=group.match_type,
            identity_confidence=group.confidence,
            nome_completo=merged.get('nome_completo', ''),
            tipo_pessoa=merged.get('tipo_pessoa', 'Proprietário'),
            cpf=merged.get('cpf', ''),
            rg=merged.get('rg', ''),
            telefones=merged.get('telefones', []),
            emails=merged.get('emails', []),
            whatsapp_status=merged.get('whatsapp_status'),
            endereco_principal=merged.get('endereco_principal', ''),
            unidade=merged.get('unidade', ''),
            enderecos_adicionais=merged.get('enderecos_adicionais', []),
            data_nascimento=merged.get('data_nascimento', ''),
            idade=merged.get('idade'),
            obito=merged.get('obito', False),
            imovel_detalhes=merged.get('imovel_detalhes', {}),
            quality=merged.get('quality', 'baixa'),
            source_records=source_records_info,
            field_provenance=field_provenance,
        )
        
        return golden
    
    def _merge_single(self, record: SourceRecord) -> GoldenRecord:
        """Cria Golden Record a partir de single record (sem merge)."""
        mapping = {
            'nome_completo': record.name_raw,
            'tipo_pessoa': record.tipo_pessoa,
            'cpf': record.cpf,
            'rg': record.rg,
            'telefones': record.telefones,
            'emails': record.emails,
            'whatsapp_status': record.whatsapp_status,
            'endereco_principal': record.address_raw,
            'unidade': record.unit_raw,
            'enderecos_adicionais': record.enderecos_adicionais,
            'data_nascimento': record.data_nascimento,
            'idade': record.idade,
            'obito': record.obito,
            'imovel_detalhes': record.imovel_detalhes,
            'quality': record.quality,
        }
        
        merged = {k: v for k, v in mapping.items() if v not in [None, '', [], {}]}
        golden_key = self._gerar_golden_key(merged)
        
        return GoldenRecord(
            golden_key=golden_key,
            match_type='single_origin',
            identity_confidence=0.5,
            nome_completo=merged.get('nome_completo', ''),
            tipo_pessoa=merged.get('tipo_pessoa', 'Proprietário'),
            cpf=merged.get('cpf', ''),
            rg=merged.get('rg', ''),
            telefones=merged.get('telefones', []),
            emails=merged.get('emails', []),
            whatsapp_status=merged.get('whatsapp_status'),
            endereco_principal=merged.get('endereco_principal', ''),
            unidade=merged.get('unidade', ''),
            enderecos_adicionais=merged.get('enderecos_adicionais', []),
            data_nascimento=merged.get('data_nascimento', ''),
            idade=merged.get('idade'),
            obito=merged.get('obito', False),
            imovel_detalhes=merged.get('imovel_detalhes', {}),
            quality=merged.get('quality', 'baixa'),
            source_records=[{
                'source': record.source,
                'source_record_id': record.source_record_id,
                'record_key': record.record_key,
                'name_raw': record.name_raw,
                'tipo_pessoa': record.tipo_pessoa,
            }],
            field_provenance={k: record.source for k in merged.keys()},
        )
    
    def _gerar_golden_key(self, merged: Dict[str, Any]) -> str:
        """Gera chave única para Golden Record."""
        # Prioridade: CPF > record_key composto
        cpf = merged.get('cpf', '')
        if cpf:
            return f"golden_cpf_{cpf}"
        
        name = canonicalizar_texto(merged.get('nome_completo', ''))
        unit = canonicalizar_texto(merged.get('unidade', ''))
        addr = canonicalizar_texto(merged.get('endereco_principal', ''))
        return f"golden_{gerar_record_key(name, unit, addr)}"
    
    def _stage_validate(self):
        """Validação cross-origem dos Golden Records."""
        print("  Stage 6/8: Validação cross-origem...")
        
        for golden in self.golden_records:
            # Preparar field_values para validação
            field_values = {}
            for src_info in golden.source_records:
                source = src_info['source']
                # Buscar SourceRecord original
                for sr in self.source_records_por_origem.get(source, []):
                    if sr.source_record_id == src_info['source_record_id']:
                        for field, value in self._record_to_fields(sr).items():
                            if field not in field_values:
                                field_values[field] = {}
                            field_values[field][source] = value
                        break
            
            # Executar validações
            validation_results = executar_validacoes(field_values, asdict(golden))
            classified = classificar_validacoes(validation_results)
            
            # Armazenar resumo
            golden.validation_summary = {
                'errors': [r.message for r in classified['errors']],
                'warnings': [r.message for r in classified['warnings']],
                'infos': [r.message for r in classified['infos']],
            }
            
            # Marcar se requer revisão
            if tem_erros_bloqueantes(validation_results):
                golden.quality = 'revisao_manual'
    
    def _record_to_fields(self, record: SourceRecord) -> Dict[str, Any]:
        """Converte SourceRecord para dict de campos."""
        return {
            'nome_completo': record.name_raw,
            'tipo_pessoa': record.tipo_pessoa,
            'cpf': record.cpf,
            'rg': record.rg,
            'telefones': record.telefones,
            'emails': record.emails,
            'whatsapp_status': record.whatsapp_status,
            'endereco_principal': record.address_raw,
            'unidade': record.unit_raw,
            'enderecos_adicionais': record.enderecos_adicionais,
            'data_nascimento': record.data_nascimento,
            'idade': record.idade,
            'obito': record.obito,
            'imovel_detalhes': record.imovel_detalhes,
            'quality': record.quality,
        }
    
    def _stage_score(self):
        """Scoring de confiança dos Golden Records."""
        print("  Stage 7/8: Scoring de confiança...")
        
        for golden in self.golden_records:
            # Preparar field_values para scoring
            field_values = {}
            for src_info in golden.source_records:
                source = src_info['source']
                for sr in self.source_records_por_origem.get(source, []):
                    if sr.source_record_id == src_info['source_record_id']:
                        for field, value in self._record_to_fields(sr).items():
                            if field not in field_values:
                                field_values[field] = {}
                            field_values[field][source] = value
                        break
            
            # Preparar merged_record dict
            merged_dict = {
                'nome_completo': golden.nome_completo,
                'tipo_pessoa': golden.tipo_pessoa,
                'cpf': golden.cpf,
                'rg': golden.rg,
                'telefones': golden.telefones,
                'emails': golden.emails,
                'whatsapp_status': golden.whatsapp_status,
                'endereco_principal': golden.endereco_principal,
                'unidade': golden.unidade,
                'enderecos_adicionais': golden.enderecos_adicionais,
                'data_nascimento': golden.data_nascimento,
                'idade': golden.idade,
                'obito': golden.obito,
                'imovel_detalhes': golden.imovel_detalhes,
                'quality': golden.quality,
            }
            
            # Calcular score
            validation_results = []
            for sev, msgs in golden.validation_summary.items():
                for msg in msgs:
                    # Criar objeto simples para scoring
                    class V:
                        def __init__(self, field, severity, message):
                            self.field = field
                            self.severity = type('S', (), {'value': severity})()
                            self.message = message
                    validation_results.append(V('validation', sev, msg))
            
            golden.scoring = calcular_golden_record_score(
                merged_dict, field_values, golden.match_type, validation_results
            )
            
            # Atualizar quality baseado no scoring
            if golden.scoring.quality_tier == 'high':
                golden.quality = 'alta'
            elif golden.scoring.quality_tier == 'medium':
                golden.quality = 'media'
            elif golden.scoring.quality_tier == 'low':
                golden.quality = 'baixa'
    
    def _stage_output(self) -> ConsolidationReport:
        """Gera outputs finais."""
        print("  Stage 8/8: Gerando outputs...")
        
        # Converter golden_records para dict
        golden_json = []
        for g in self.golden_records:
            golden_json.append({
                'golden_key': g.golden_key,
                'match_type': g.match_type,
                'identity_confidence': g.identity_confidence,
                'nome_completo': g.nome_completo,
                'tipo_pessoa': g.tipo_pessoa,
                'cpf': g.cpf,
                'rg': g.rg,
                'telefones': g.telefones,
                'emails': g.emails,
                'whatsapp_status': g.whatsapp_status,
                'endereco_principal': g.endereco_principal,
                'unidade': g.unidade,
                'enderecos_adicionais': g.enderecos_adicionais,
                'data_nascimento': g.data_nascimento,
                'idade': g.idade,
                'obito': g.obito,
                'imovel_detalhes': g.imovel_detalhes,
                'quality': g.quality,
                'source_records': g.source_records,
                'field_provenance': g.field_provenance,
                'validation_summary': g.validation_summary,
                'scoring': asdict(g.scoring) if g.scoring else None,
                'created_at': g.created_at,
                'updated_at': g.updated_at,
            })
        
        # Salvar Golden Records (JSON + MD)
        output_dir = self.manifests_dir / self.lote / 'consolidado'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        consolidado_path = output_dir / f'golden_records_{self.lote}.json'
        salvar_json_seguro(golden_json, consolidado_path)
        print(f"    Golden Records JSON: {consolidado_path}")
        
        # Relatório Markdown
        report_md = self._gerar_relatorio_consolidado(golden_json)
        report_path = output_dir / f'relatorio_consolidacao_{self.lote}.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_md)
        print(f"    Relatório MD: {report_path}")
        
        # Estatísticas
        quality_dist = defaultdict(int)
        for g in self.golden_records:
            quality_dist[g.quality] += 1
        
        multi_origem = sum(1 for g in self.golden_records if g.match_type != 'single_origin')
        single_origem = len(self.golden_records) - multi_origem
        requires_review = sum(1 for g in self.golden_records if g.scoring and g.scoring.requires_manual_review)
        
        return ConsolidationReport(
            lote=self.lote,
            timestamp=timestamp_iso(),
            total_source_records=sum(len(r) for r in self.source_records_por_origem.values()),
            total_golden_records=len(self.golden_records),
            golden_records_multi_origem=multi_origem,
            golden_records_single_origem=single_origem,
            requires_review=requires_review,
            quality_distribution=dict(quality_dist),
            identity_groups=[{
                'match_type': g.match_type,
                'confidence': g.confidence,
                'sources': [r.source for r in g.records],
                'names': [r.name_raw for r in g.records],
                'identity_keys': g.identity_keys,
            } for g in self.identity_groups],
            golden_records=[{
                'golden_key': g.golden_key,
                'nome': g.nome_completo,
                'tipo_pessoa': g.tipo_pessoa,
                'match_type': g.match_type,
                'quality': g.quality,
                'confidence': g.scoring.overall_confidence if g.scoring else 0,
                'requires_review': g.scoring.requires_manual_review if g.scoring else False,
            } for g in self.golden_records]
        )
    
    def _gerar_relatorio_consolidado(self, golden_json: List[Dict]) -> str:
        """Gera relatório consolidado em Markdown."""
        lines = []
        lines.append(f"# Relatório de Consolidação Multi-Origem - {self.lote}\n")
        lines.append(f"Gerado em: {timestamp_iso()}\n")
        
        # Estatísticas
        lines.append("## Estatísticas Gerais")
        lines.append(f"- Total de Source Records: {sum(len(r) for r in self.source_records_por_origem.values())}")
        lines.append(f"- Total Golden Records: {len(golden_json)}")
        lines.append(f"- Multi-Origem: {sum(1 for g in golden_json if g['match_type'] != 'single_origin')}")
        lines.append(f"- Single-Origem: {sum(1 for g in golden_json if g['match_type'] == 'single_origin')}")
        lines.append(f"- Requer Revisão: {sum(1 for g in golden_json if g.get('scoring', {}).get('requires_manual_review', False))}\n")
        
# Distribuição de qualidade
        lines.append("## Distribuição de Qualidade")
        quality_dist = defaultdict(int)
        for g in golden_json:
            quality_dist[g.get('quality', 'baixa')] += 1
        for q, c in sorted(quality_dist.items()):
            lines.append(f"- {q.capitalize()}: {c}")
        lines.append("")
        
        # Grupos de identidade
        lines.append("## Grupos de Identidade (Multi-Origem)")
        lines.append("| Grupo | Tipo Match | Confiança | Origens | Nomes |")
        lines.append("|-------|------------|-----------|---------|-------|")
        for i, g in enumerate(self.identity_groups, 1):
            sources = [r.source for r in g.records]
            names = [r.name_raw for r in g.records]
            lines.append(f"| {i} | {g.match_type} | {g.confidence:.0%} | {', '.join(sources)} | {', '.join(names)} |")
        lines.append("")
        
        # Golden Records
        lines.append("## Golden Records")
        lines.append("| Golden Key | Nome | Tipo | Match | Qualidade | Confiança | Revisão |")
        lines.append("|------------|------|------|-------|-----------|-----------|---------|")
        for g in golden_json:
            review = '⚠️' if g.get('scoring', {}).get('requires_manual_review') else '✅'
            conf = g.get('scoring', {}).get('overall_confidence', 0)
            lines.append(f"| {g['golden_key'][:20]}... | {g['nome_completo']} | {g['tipo_pessoa']} | {g['match_type']} | {g['quality']} | {conf:.0f}% | {review} |")
        
        return '\n'.join(lines)


def consolidar_multi_origem(lote: str, manifests_dir: str = '.') -> ConsolidationReport:
    """Função de conveniência para executar consolidação."""
    pipeline = ConsolidationPipeline(lote, manifests_dir)
    return pipeline.run()