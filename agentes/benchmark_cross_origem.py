#!/usr/bin/env python3
"""Benchmark script para analisar overlap cross-origem entre Captei, Fisgar e EEmovel."""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Set, Tuple
from difflib import SequenceMatcher

# Adicionar path dos agentes
sys.path.insert(0, str(Path(__file__).parent))

from comum import canonicalizar_texto, gerar_record_key, extrair_digitos_telefone


def carregar_manifest(caminho: Path) -> List[Dict[str, Any]]:
    """Carrega manifest NDJSON."""
    if not caminho.exists():
        return []
    registros = []
    with open(caminho, 'r', encoding='utf-8') as f:
        for linha in f:
            if linha.strip():
                registros.append(json.loads(linha))
    return registros


def extrair_campos_chave(registro: Dict[str, Any]) -> Dict[str, Any]:
    """Extrai campos relevantes para comparação cross-origem."""
    return {
        'record_key': registro.get('record_key'),
        'name_raw': registro.get('name_raw', ''),
        'name_canonical': registro.get('name_canonical', ''),
        'unit_raw': registro.get('unit_raw', ''),
        'unit_canonical': registro.get('unit_canonical', ''),
        'address_raw': registro.get('address_raw', ''),
        'address_canonical': registro.get('address_canonical', ''),
        'entity_type': registro.get('entity_type', ''),
        'tipo_pessoa': registro.get('tipo_pessoa', 'Proprietário'),
        'cpf': registro.get('cpf', ''),
        'telefones': [extrair_digitos_telefone(t.get('numero_raw', t.get('numero', ''))) 
                      for t in registro.get('telefones', []) if t.get('numero_raw') or t.get('numero')],
        'emails': [e.get('endereco_raw', e.get('endereco', '')).lower().strip() 
                   for e in registro.get('emails', []) if e.get('endereco_raw') or e.get('endereco')],
        'source': 'unknown'  # Será preenchido pelo caller
    }


def similaridade_nomes(nome1: str, nome2: str) -> float:
    """Calcula similaridade entre dois nomes (0-1)."""
    return SequenceMatcher(None, nome1.upper(), nome2.upper()).ratio()


def analisar_overlap(registros_por_origem: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """Analisa overlap entre as 3 origens."""
    
    # Preparar dados normalizados
    dados_norm = {}
    for origem, regs in registros_por_origem.items():
        dados_norm[origem] = [extrair_campos_chave(r) for r in regs]
        for d in dados_norm[origem]:
            d['source'] = origem
    
    # Todas as chaves únicas por origem
    keys_por_origem = {origem: set(d['record_key'] for d in dados) for origem, dados in dados_norm.items()}
    
    # Overlap por record_key exato
    todas_keys = set().union(*keys_por_origem.values())
    
    overlap_exato = {}
    for key in todas_keys:
        origens_com_key = [origem for origem, keys in keys_por_origem.items() if key in keys]
        if len(origens_com_key) > 1:
            overlap_exato[key] = origens_com_key
    
    # Overlap por CPF (quando disponível)
    cpf_por_origem = defaultdict(dict)
    for origem, dados in dados_norm.items():
        for d in dados:
            cpf_raw = d.get('cpf') or ''
            cpf = cpf_raw.replace('.', '').replace('-', '').strip()
            if cpf and cpf != '***':
                cpf_por_origem[cpf][origem] = d
    
    overlap_cpf = {cpf: list(origens.keys()) for cpf, origens in cpf_por_origem.items() if len(origens) > 1}
    
    # Overlap por telefone
    tel_por_origem = defaultdict(dict)
    for origem, dados in dados_norm.items():
        for d in dados:
            for tel in d.get('telefones', []):
                if tel:
                    tel_por_origem[tel][origem] = d
    
    overlap_tel = {tel: list(origens.keys()) for tel, origens in tel_por_origem.items() if len(origens) > 1}
    
    # Overlap por email
    email_por_origem = defaultdict(dict)
    for origem, dados in dados_norm.items():
        for d in dados:
            for email in d.get('emails', []):
                if email:
                    email_por_origem[email][origem] = d
    
    overlap_email = {email: list(origens.keys()) for email, origens in email_por_origem.items() if len(origens) > 1}
    
    # Fuzzy match por nome + endereço (para pegar variações)
    fuzzy_matches = []
    origens_lista = list(dados_norm.keys())
    for i, orig1 in enumerate(origens_lista):
        for orig2 in origens_lista[i+1:]:
            for d1 in dados_norm[orig1]:
                for d2 in dados_norm[orig2]:
                    # Só comparar PF com PF
                    if d1['entity_type'] != 'Pessoa Fisica' or d2['entity_type'] != 'Pessoa Fisica':
                        continue
                    sim_nome = similaridade_nomes(d1['name_raw'], d2['name_raw'])
                    sim_end = similaridade_nomes(d1['address_raw'], d2['address_raw'])
                    if sim_nome > 0.85 and sim_end > 0.8:
                        fuzzy_matches.append({
                            'origem_1': orig1,
                            'origem_2': orig2,
                            'nome_1': d1['name_raw'],
                            'nome_2': d2['name_raw'],
                            'sim_nome': round(sim_nome, 3),
                            'sim_end': round(sim_end, 3),
                            'record_key_1': d1['record_key'],
                            'record_key_2': d2['record_key']
                        })
    
    # Estatísticas por origem
    stats = {}
    for origem, dados in dados_norm.items():
        pf = [d for d in dados if d['entity_type'] == 'Pessoa Fisica']
        emp = [d for d in dados if d['entity_type'] == 'Empresa']
        moradores = [d for d in dados if d.get('tipo_pessoa') == 'Possível morador']
        stats[origem] = {
            'total': len(dados),
            'pessoa_fisica': len(pf),
            'empresa': len(emp),
            'moradores': len(moradores),
            'com_cpf': len([d for d in pf if d.get('cpf') and d['cpf'] != '***']),
            'com_telefone': len([d for d in pf if d.get('telefones')]),
            'com_email': len([d for d in pf if d.get('emails')]),
            'keys_unicas': len(keys_por_origem[origem])
        }
    
    return {
        'stats_por_origem': stats,
        'overlap_record_key_exato': overlap_exato,
        'overlap_cpf': overlap_cpf,
        'overlap_telefone': overlap_tel,
        'overlap_email': overlap_email,
        'fuzzy_matches': fuzzy_matches,
        'total_registros_unicos_estimado': len(todas_keys) - len(overlap_exato) + sum(len(v) for v in overlap_exato.values()) / 2
    }


def gerar_relatorio_benchmark(resultado: Dict[str, Any]) -> str:
    """Gera relatório de benchmark em markdown."""
    md = """# Benchmark Cross-Origem — Captei, Fisgar, EEmovel

## 1. Estatísticas por Origem

| Origem | Total | PF | Empresa | Moradores | c/ CPF | c/ Telefone | c/ Email | Keys Únicas |
|--------|-------|-----|---------|-----------|--------|-------------|----------|-------------|
"""
    for origem, s in resultado['stats_por_origem'].items():
        md += f"| {origem.capitalize()} | {s['total']} | {s['pessoa_fisica']} | {s['empresa']} | {s['moradores']} | {s['com_cpf']} | {s['com_telefone']} | {s['com_email']} | {s['keys_unicas']} |\n"
    
    md += f"""
## 2. Overlap por Record Key (Exato)

Total de chaves únicas estimadas: **{int(resultado['total_registros_unicos_estimado'])}**

Overlaps encontrados: **{len(resultado['overlap_record_key_exato'])}**

| Record Key | Origens |
|------------|---------|
"""
    for key, origens in sorted(resultado['overlap_record_key_exato'].items()):
        md += f"| {key} | {', '.join(origens)} |\n"
    
    md += f"""
## 3. Overlap por CPF

Overlaps encontrados: **{len(resultado['overlap_cpf'])}**

| CPF (mascarado) | Origens |
|-----------------|---------|
"""
    for cpf, origens in sorted(resultado['overlap_cpf'].items()):
        cpf_mask = cpf[:3] + '***' + cpf[-2:] if len(cpf) > 5 else '***'
        md += f"| {cpf_mask} | {', '.join(origens)} |\n"
    
    md += f"""
## 4. Overlap por Telefone

Overlaps encontrados: **{len(resultado['overlap_telefone'])}**

| Telefone (dígitos) | Origens |
|--------------------|---------|
"""
    for tel, origens in sorted(resultado['overlap_telefone'].items()):
        tel_fmt = f"({tel[:2]}) {tel[2:7]}-{tel[7:]}" if len(tel) == 11 else tel
        md += f"| {tel_fmt} | {', '.join(origens)} |\n"
    
    md += f"""
## 5. Overlap por Email

Overlaps encontrados: **{len(resultado['overlap_email'])}**

| Email | Origens |
|-------|---------|
"""
    for email, origens in sorted(resultado['overlap_email'].items()):
        md += f"| {email} | {', '.join(origens)} |\n"
    
    md += f"""
## 6. Fuzzy Matches (Nome + Endereço similar)

Matches encontrados: **{len(resultado['fuzzy_matches'])}**

| Origem 1 | Origem 2 | Nome 1 | Nome 2 | Sim. Nome | Sim. End | Key 1 | Key 2 |
|----------|----------|--------|--------|-----------|----------|-------|-------|
"""
    for m in resultado['fuzzy_matches'][:20]:  # Top 20
        md += f"| {m['origem_1']} | {m['origem_2']} | {m['nome_1']} | {m['nome_2']} | {m['sim_nome']} | {m['sim_end']} | {m['record_key_1'][:8]}... | {m['record_key_2'][:8]}... |\n"
    
    if len(resultado['fuzzy_matches']) > 20:
        md += f"\n... e mais {len(resultado['fuzzy_matches']) - 20} matches.\n"
    
    md += """
## 7. Análise de Qualidade do record_key Atual

"""
    # Analisar falsos positivos/negativos potenciais
    total_overlaps = len(resultado['overlap_record_key_exato'])
    total_cpf_overlaps = len(resultado['overlap_cpf'])
    total_tel_overlaps = len(resultado['overlap_telefone'])
    total_email_overlaps = len(resultado['overlap_email'])
    total_fuzzy = len(resultado['fuzzy_matches'])
    
    md += f"""
- Overlaps por record_key exato: **{total_overlaps}**
- Overlaps por CPF (forte): **{total_cpf_overlaps}**
- Overlaps por telefone: **{total_tel_overlaps}**
- Overlaps por email: **{total_email_overlaps}**
- Fuzzy matches (>0.85 nome, >0.8 end): **{total_fuzzy}**

**Recomendações:**
1. **CPF deve ser fator primário** de identidade quando disponível em ≥2 origens
2. **record_key atual (name|unit|address)** funciona para matching exato, mas falha em variações de unidade
3. **Telefone + Nome** é boa chave secundária para deduplicação
4. **Fuzzy match** necessário para capturar variações de digitação/abreviação de unidade
5. **Moradores EEmovel** não devem ser dedupados com proprietários (tipo_pessoa diferente)
"""
    
    return md


def main():
    base = Path('/home/rochagus/projetos-linux/extrator-proprietarios/agentes')
    
    # Carregar manifests dos 3 agentes
    manifests = {}
    for agente in ['captei', 'fisgar', 'eemovel']:
        # Tentar encontrar o manifest mais recente
        manifest_dir = base / f'teste_{agente}' / 'manifest'
        if manifest_dir.exists():
            manifest_files = list(manifest_dir.glob('manifest_*.ndjson'))
            if manifest_files:
                manifests[agente] = carregar_manifest(manifest_files[0])
                print(f"Carregado {agente}: {len(manifests[agente])} registros")
            else:
                print(f"AVISO: Manifest não encontrado para {agente}")
        else:
            print(f"AVISO: Diretório não encontrado para {agente}")
    
    if len(manifests) < 2:
        print("ERRO: Necessário pelo menos 2 manifests para benchmark")
        return
    
    # Analisar overlap
    print("\nAnalisando overlap cross-origem...")
    resultado = analisar_overlap(manifests)
    
    # Gerar relatório
    relatorio = gerar_relatorio_benchmark(resultado)
    
    # Salvar
    output_path = base / 'benchmark_cross_origem.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(relatorio)
    
    print(f"\nRelatório salvo em: {output_path}")
    print(relatorio)


if __name__ == '__main__':
    main()