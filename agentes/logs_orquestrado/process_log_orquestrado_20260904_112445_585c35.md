# Process Learning Report
**Run ID:** orquestrado_20260904_112445_585c35
**Início:** 2026-09-04T11:24:45.531002
**Fim:** 2026-09-04T11:24:45.633177
**Status:** completed
**Total Ações:** 12
**Total Erros:** 0

## Por Sistema
| Sistema | Ações | Tempo Total (ms) | Queries | Capcoins | Créditos | Erros |
|---------|-------|------------------|---------|----------|----------|-------|
| eemovel | 4 | 8 | 3 | 0 | 0 | 0 |
| fisgar | 4 | 4 | 3 | 0 | 0 | 0 |
| captei | 3 | 4 | 2 | 0 | 0 | 0 |
| pipeline | 1 | 28 | 0 | 0 | 0 | 0 |

## Funil de Estágios
| Estágio | Execuções | Tempo Total (ms) | Tempo Médio (ms) |
|---------|-----------|------------------|------------------|
| inventory | 1 | 4 | 4 |
| extraction_cascade | 1 | 45 | 45 |
| merge_enrichment | 1 | 48 | 48 |

## Decisões de Fluxo
- **init**: configurar_sistemas — *Sistemas solicitados: ['eemovel', 'fisgar', 'captei']. Ordem de extração: EEmovel → Fisgar → Captei*
- **inventory**: consultar_listagem_eemovel — *Verificar se eemovel tem dados para Rua Marc Chagall, 397*
- **inventory**: consultar_listagem_fisgar — *Verificar se fisgar tem dados para Rua Marc Chagall, 397*
- **inventory**: consultar_listagem_captei — *Verificar se captei tem dados para Rua Marc Chagall, 397*
- **inventory**: consolidar_listas — *Dedup por record_key: 29 chaves → 24 props + 5 moradores*
- **extraction_cascade**: extrair_eemovel — *3 registros pendentes (ordem 1: custo R$0.81/consulta)*
- **extraction_cascade**: extrair_fisgar — *3 registros pendentes (ordem 2: custo R$1.03/consulta)*
- **extraction_cascade**: extrair_captei — *2 registros pendentes (ordem 3: custo R$1.57/consulta)*
- **merge_enrichment**: executar_consolidacao — *Pipeline 8 stages: load → normalize → sanitize → dedup → merge → validate → score → output*

## Resumos de Extração
- **eemovel** (inventory): {'total': 25, 'proprietarios': 20, 'moradores': 5}
- **fisgar** (inventory): {'total': 5, 'proprietarios': 5, 'moradores': 0}
- **captei** (inventory): {'total': 5, 'proprietarios': 5, 'moradores': 0}
- **eemovel** (extraction_cascade): {'processados': 3, 'erros': 0, 'novos': 3, 'total_disponivel': 25}
- **fisgar** (extraction_cascade): {'processados': 3, 'erros': 0, 'novos': 3, 'total_disponivel': 5}
- **captei** (extraction_cascade): {'processados': 2, 'erros': 0, 'novos': 2, 'total_disponivel': 5}
- **pipeline** (merge_enrichment): {'golden_records': 27, 'multi_origem': 4, 'single_origem': 23, 'requires_review': 27, 'quality_distribution': {'baixa': 27}}
