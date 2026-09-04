#!/usr/bin/env python3
"""Orquestrador Inteligente — Extração em 3 Estágios com Ordem Otimizada.

ESTÁGIO 1: Inventário (custo: 1 crédito por listagem por sistema — retorna a lista completa de possíveis PROPRIETÁRIOS e possíveis MORADORES; fica salvo no manifest — retomada não repaga)
ESTÁGIO 2: Extração em Cascata (EEmovel → Fisgar → Captei) 
ESTÁGIO 3: Merge & Enriquecimento
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, str(Path(__file__).parent))

from comum import (
    criar_estrutura_lote,
    canonicalizar_texto,
    gerar_record_key,
    gerar_record_key_v2,
    classificar_entidade,
    normalizar_unidade,
    parse_unidade,
    classificar_tipo_unidade,
    salvar_json_seguro,
    carregar_json,
    append_ndjson,
    timestamp_iso
)
from comum.process_logger import ProcessLearningLogger, generate_learning_report


# Ordem otimizada: menor custo/consulta primeiro
ORDEM_EXTRACAO = [
    {"sistema": "eemovel", "custo_estimado": 0.81, "limite_mes": 500, "prioridade": 1},
    {"sistema": "fisgar", "custo_estimado": 1.03, "limite_mes": 250, "prioridade": 2},
    {"sistema": "captei", "custo_estimado": 1.57, "limite_mes": 200, "prioridade": 3},
]

SISTEMAS_DISPONIVEIS = {s["sistema"]: s for s in ORDEM_EXTRACAO}


def carregar_agente(sistema: str, diretorio_base: str, nome_lote: str):
    """Carrega agente dinamicamente."""
    if sistema == "captei":
        from captei import AgenteCaptei
        return AgenteCaptei(diretorio_base, nome_lote)
    elif sistema == "fisgar":
        from fisgar import AgenteFisgar
        return AgenteFisgar(diretorio_base, nome_lote)
    elif sistema == "eemovel":
        from eemovel import AgenteEEmovel
        return AgenteEEmovel(diretorio_base, nome_lote)
    raise ValueError(f"Sistema desconhecido: {sistema}")


def carregar_modulo_extrator(sistema: str):
    """Carrega módulo extrator do sistema."""
    if sistema == "captei":
        from captei.extrator import processar_modal_captei, validar_dados_modal
        return processar_modal_captei, validar_dados_modal
    elif sistema == "fisgar":
        from fisgar.extrator import processar_modal_fisgar, validar_dados_modal_fisgar
        return processar_modal_fisgar, validar_dados_modal_fisgar
    elif sistema == "eemovel":
        from eemovel.extrator import processar_modal_eemovel, validar_dados_modal_eemovel
        return processar_modal_eemovel, validar_dados_modal_eemovel
    raise ValueError(f"Extrator desconhecido: {sistema}")


def carregar_persister(sistema: str):
    """Carrega persister do sistema."""
    if sistema == "captei":
        from captei.persister import persistir_proprietario
        return persistir_proprietario
    elif sistema == "fisgar":
        from fisgar.persister import persistir_proprietario
        return persistir_proprietario
    elif sistema == "eemovel":
        from eemovel.persister import persistir_proprietario
        return persistir_proprietario
    raise ValueError(f"Persister desconhecido: {sistema}")


def normalizar_linha_tabela(linha: Dict[str, Any], endereco: str, sistema: str) -> Dict[str, Any]:
    """Normaliza linha de tabela para formato unificado com parse de unidade estruturado."""
    nome = linha.get('nome', '').strip()
    endereco_linha = linha.get('endereco', endereco).strip()
    
    # Suportar ambos formatos: antigo (unidade) e novo (unidade_imovel, unidade_vaga)
    if 'unidade_imovel' in linha or 'unidade_vaga' in linha:
        unidade_imovel = linha.get('unidade_imovel', '').strip()
        unidade_vaga = linha.get('unidade_vaga', '').strip()
        # Compatibilidade: se veio unidade antiga, parsear
        if not unidade_imovel and not unidade_vaga:
            unidade_legado = linha.get('unidade', '').strip()
            parsed = parse_unidade(unidade_legado)
            unidade_imovel = parsed['unidade_imovel']
            unidade_vaga = parsed['unidade_vaga']
    else:
        # Formato legado
        unidade_legado = linha.get('unidade', '').strip()
        parsed = parse_unidade(unidade_legado)
        unidade_imovel = parsed['unidade_imovel']
        unidade_vaga = parsed['unidade_vaga']
    
    if not nome:
        return None
    
    entity_type = classificar_entidade(nome)
    name_canonical = canonicalizar_texto(nome)
    address_canonical = canonicalizar_texto(endereco_linha)
    
    # Normalizar componentes da unidade
    unidade_imovel_canonical = canonicalizar_texto(unidade_imovel)
    unidade_vaga_canonical = canonicalizar_texto(unidade_vaga)
    
    # Gerar record_key v2 com componentes separados
    record_key = gerar_record_key_v2(name_canonical, unidade_imovel_canonical, unidade_vaga_canonical, address_canonical)
    
    # Para compatibilidade com código legado
    unidade_raw = f"{unidade_imovel}; {unidade_vaga}".strip(' ;')
    unit_canonical = f"{unidade_imovel_canonical}; {unidade_vaga_canonical}".strip(' ;')
    
    # Classificar tipo de unidade
    tipo_unidade = classificar_tipo_unidade(unidade_imovel, unidade_vaga)
    
    return {
        "record_key": record_key,
        "name_raw": nome,
        "name_canonical": name_canonical,
        "unit_raw": unidade_raw,
        "unit_canonical": unit_canonical,
        "unidade_imovel_raw": unidade_imovel,
        "unidade_imovel_canonical": unidade_imovel_canonical,
        "unidade_vaga_raw": unidade_vaga,
        "unidade_vaga_canonical": unidade_vaga_canonical,
        "tipo_unidade": tipo_unidade,
        "address_raw": endereco_linha,
        "address_canonical": address_canonical,
        "entity_type": entity_type,
        "tipo_pessoa": linha.get('tipo_pessoa', 'Proprietário'),
        "state": "inventariado",
        "source_system": sistema,
        "source_line": linha.get('source_line'),
        "source_record_id": linha.get('source_record_id'),
        "timestamp": timestamp_iso()
    }


def stage1_inventario(
    logger: ProcessLearningLogger,
    endereco: str,
    sistemas_ativos: List[str],
    dados_por_sistema: Dict[str, List[Dict]]
) -> Dict[str, Any]:
    """ESTÁGIO 1: Inventário — consome 1 crédito por listagem por sistema; sem abrir modais/fichas. A lista fica salva no manifest (retomada não repaga a listagem)."""
    
    with logger.stage("inventory", metadata={"endereco": endereco, "sistemas": sistemas_ativos}) as stage_id:
        inventario = {
            "endereco": endereco,
            "timestamp": timestamp_iso(),
            "sistemas": {},
            "consolidado": {"proprietarios": [], "moradores": []},
            "estatisticas": {}
        }
        
        todas_chaves = set()
        
        for sistema in sistemas_ativos:
            logger.log_decision(
                stage="inventory",
                decision=f"consultar_listagem_{sistema}",
                rationale=f"Verificar se {sistema} tem dados para {endereco}",
                data={"sistema": sistema}
            )
            
            with logger.action("query_listing", sistema, "inventory", 
                             {"endereco": endereco, "sistema": sistema}) as action:
                
                dados = dados_por_sistema.get(sistema, [])
                action.add_output("raw_count", len(dados))
                
                # Normalizar e classificar
                proprietarios = []
                moradores = []
                chaves_sistema = set()
                
                for i, linha in enumerate(dados):
                    reg = normalizar_linha_tabela(linha, endereco, sistema)
                    if not reg:
                        continue
                    
                    reg["source_line"] = i + 1
                    chaves_sistema.add(reg["record_key"])
                    todas_chaves.add(reg["record_key"])
                    
                    if reg["tipo_pessoa"] in ["Possível morador", "Morador"]:
                        moradores.append(reg)
                    else:
                        proprietarios.append(reg)
                
                action.add_output("proprietarios", len(proprietarios))
                action.add_output("moradores", len(moradores))
                action.add_output("chaves_unicas", len(chaves_sistema))
                
                inventario["sistemas"][sistema] = {
                    "total_bruto": len(dados),
                    "proprietarios": proprietarios,
                    "moradores": moradores,
                    "chaves_unicas": list(chaves_sistema)
                }
                
                logger.log_extraction_result(sistema, "inventory", {
                    "total": len(dados),
                    "proprietarios": len(proprietarios),
                    "moradores": len(moradores)
                })
        
        # Consolidar: deduplicar por record_key
        todos_props = []
        todos_moradores = []
        chaves_vistas_props = set()
        chaves_vistas_mor = set()
        
        for sistema in sistemas_ativos:
            for reg in inventario["sistemas"][sistema]["proprietarios"]:
                if reg["record_key"] not in chaves_vistas_props:
                    chaves_vistas_props.add(reg["record_key"])
                    todos_props.append(reg)
            
            for reg in inventario["sistemas"][sistema]["moradores"]:
                if reg["record_key"] not in chaves_vistas_mor:
                    chaves_vistas_mor.add(reg["record_key"])
                    todos_moradores.append(reg)
        
        inventario["consolidado"]["proprietarios"] = todos_props
        inventario["consolidado"]["moradores"] = todos_moradores
        
        inventario["estatisticas"] = {
            "total_chaves_unicas": len(todas_chaves),
            "proprietarios_unicos": len(todos_props),
            "moradores_unicos": len(todos_moradores),
            "sistemas_com_dados": len([s for s in sistemas_ativos if inventario["sistemas"][s]["total_bruto"] > 0])
        }
        
        logger.log_decision(
            stage="inventory",
            decision="consolidar_listas",
            rationale=f"Dedup por record_key: {len(todas_chaves)} chaves → {len(todos_props)} props + {len(todos_moradores)} moradores",
            data=inventario["estatisticas"]
        )
        
        return inventario


def stage2_extracao_cascata(
    logger: ProcessLearningLogger,
    inventario: Dict[str, Any],
    sistemas_ordenados: List[Dict],
    limite_por_sistema: Optional[int] = None
) -> Dict[str, Any]:
    """ESTÁGIO 2: Extração em cascata - EEmovel → Fisgar → Captei."""
    
    with logger.stage("extraction_cascade", metadata={"ordem": [s["sistema"] for s in sistemas_ordenados]}) as stage_id:
        
        # Chaves já extraídas (para pular em sistemas subsequentes)
        chaves_extraidas = set()
        resultados_por_sistema = {}
        
        # Filtrar apenas sistemas ativos e ordenar por prioridade
        sistemas_ativos_ordenados = [
            s for s in sistemas_ordenados 
            if s["sistema"] in inventario["sistemas"] and inventario["sistemas"][s["sistema"]]["total_bruto"] > 0
        ]
        
        for idx, sistema_info in enumerate(sistemas_ativos_ordenados):
            sistema = sistema_info["sistema"]
            dados_sistema = inventario["sistemas"][sistema]
            
            # Combinar proprietários + moradores para extração
            todos_registros = dados_sistema["proprietarios"] + dados_sistema["moradores"]
            
            # Filtrar apenas os que NÃO foram extraídos ainda
            pendentes = [r for r in todos_registros if r["record_key"] not in chaves_extraidas]
            
            if not pendentes:
                logger.log_decision(
                    stage="extraction_cascade",
                    decision=f"pular_{sistema}",
                    rationale=f"Todos {len(todos_registros)} registros já extraídos em sistemas anteriores",
                    data={"sistema": sistema, "ja_extraidos": len(todos_registros)}
                )
                resultados_por_sistema[sistema] = {"processados": 0, "pulados": len(todos_registros), "novos": 0}
                continue
            
            if limite_por_sistema:
                pendentes = pendentes[:limite_por_sistema]
            
            logger.log_decision(
                stage="extraction_cascade",
                decision=f"extrair_{sistema}",
                rationale=f"{len(pendentes)} registros pendentes (ordem {idx+1}: custo R${sistema_info['custo_estimado']}/consulta)",
                data={"sistema": sistema, "pendentes": len(pendentes), "ordem": idx + 1}
            )
            
            # Carregar agente e módulos
            agente = carregar_agente(sistema, ".", f"orquestrado_{sistema}")
            processar_modal, validar_modal = carregar_modulo_extrator(sistema)
            persister = carregar_persister(sistema)
            
            # Criar manifest local no agente para compatibilidade
            # O agente espera que o registro esteja no manifest para atualizar estado
            for registro in pendentes:
                agente.adicionar_ao_manifest(registro)
            
            processados = 0
            erros = 0
            
            for registro in pendentes:
                with logger.action("extract_detail", sistema, "extraction_cascade",
                                 {"record_key": registro["record_key"], "nome": registro["name_raw"]}) as action:
                    
                    try:
                        # Simular extração de modal/detalhe
                        # Na versão real, aqui chamaria browser automation
                        dados_modal_simulados = _simular_modal(sistema, registro)
                        
                        # Processar
                        dados_processados = processar_modal(dados_modal_simulados)
                        
                        # Validar
                        if not validar_modal(dados_modal_simulados, registro):
                            logger.log_decision(
                                stage="extraction_cascade",
                                decision="modal_inconsistente",
                                rationale=f"Dados do modal não conferem com manifest para {registro['name_raw']}",
                                data={"record_key": registro["record_key"], "sistema": sistema}
                            )
                            agente.atualizar_estado_registro(registro["record_key"], "wrong_modal_prevented")
                            erros += 1
                            action.add_output("status", "inconsistent")
                            continue
                        
                        # Persistir
                        caminhos = persister(dados_processados, registro, agente.estrutura, agente.nome_lote)
                        
                        # Atualizar estado
                        agente.atualizar_estado_registro(registro["record_key"], "resultado_persistido", dados_processados)
                        
                        chaves_extraidas.add(registro["record_key"])
                        processados += 1
                        
                        action.add_output("status", "success")
                        action.add_output("arquivo", caminhos["json"].name)
                        action.add_cost(queries=1)
                        
                    except Exception as e:
                        erros += 1
                        action.add_output("status", "error")
                        action.add_output("error", str(e))
                        raise
            
            resultados_por_sistema[sistema] = {
                "processados": processados,
                "erros": erros,
                "novos": processados,
                "total_disponivel": len(todos_registros)
            }
            
            logger.log_extraction_result(sistema, "extraction_cascade", resultados_por_sistema[sistema])
            logger.log_cost_snapshot(sistema, {
                "queries_usadas": processados,
                "custo_estimado_total": processados * sistema_info["custo_estimado"]
            })
        
        return {
            "chaves_extraidas": list(chaves_extraidas),
            "resultados_por_sistema": resultados_por_sistema,
            "ordem_usada": [s["sistema"] for s in sistemas_ativos_ordenados]
        }


def _simular_modal(sistema: str, registro: Dict[str, Any]) -> Dict[str, Any]:
    """Simula dados de modal/detalhe por sistema."""
    base = {
        "nome_completo": registro["name_raw"],
        "papel": registro.get("tipo_pessoa", "Proprietário"),
        "endereco_retornado": registro["address_raw"],
        "unidade": registro["unit_raw"],
        "inscricao": "",
        "idade": None,
        "data_nascimento": None,
        "data_nascimento_ausente": True,
        "metodo_extracao": "simulado_orquestrado",
        "modal_completo": True
    }
    
    if sistema == "captei":
        base.update({
            "telefones": [{"numero": "(11) 99999-9999", "tipo": "Celular", "whatsapp_status": "nao_validado"}],
            "emails": [{"endereco": "exemplo@email.com", "tipo": "Principal"}]
        })
    elif sistema == "fisgar":
        base.update({
            "cpf": "",
            "rg": "",
            "telefones": [{"numero": "(11) 99999-9999", "tipo": "Celular", "principal": True}],
            "emails": [{"endereco": "exemplo@email.com", "tipo": "Principal", "principal": True}]
        })
    elif sistema == "eemovel":
        base.update({
            "cpf": "***.***.***-**",
            "telefones": ["(11) 99999-9999"],
            "emails": ["exemplo@email.com"],
            "enderecos_adicionais": [],
            "imovel_detalhes": {}
        })
    
    return base


def stage3_merge_enriquecimento(
    logger: ProcessLearningLogger,
    inventario: Dict[str, Any],
    resultado_extracao: Dict[str, Any],
    manifests_dir: str
) -> Dict[str, Any]:
    """ESTÁGIO 3: Merge & Enriquecimento usando pipeline de consolidação."""
    
    with logger.stage("merge_enrichment", metadata={"manifests_dir": manifests_dir}) as stage_id:
        from comum.consolidation import consolidar_multi_origem
        
        # Executar consolidação multi-origem
        logger.log_decision(
            stage="merge_enrichment",
            decision="executar_consolidacao",
            rationale="Pipeline 8 stages: load → normalize → sanitize → dedup → merge → validate → score → output",
            data={"manifests_dir": manifests_dir}
        )
        
        with logger.action("consolidate", "pipeline", "merge_enrichment", 
                         {"manifests_dir": manifests_dir}) as action:
            
            report = consolidar_multi_origem("orquestrado_consolidado", manifests_dir)
            
            action.add_output("golden_records", report.total_golden_records)
            action.add_output("multi_origem", report.golden_records_multi_origem)
            action.add_output("requires_review", report.requires_review)
        
        logger.log_extraction_result("pipeline", "merge_enrichment", {
            "golden_records": report.total_golden_records,
            "multi_origem": report.golden_records_multi_origem,
            "single_origem": report.golden_records_single_origem,
            "requires_review": report.requires_review,
            "quality_distribution": report.quality_distribution
        })
        
        return {
            "consolidation_report": {
                "total_golden_records": report.total_golden_records,
                "multi_origem": report.golden_records_multi_origem,
                "single_origem": report.golden_records_single_origem,
                "requires_review": report.requires_review,
                "quality_distribution": report.quality_distribution
            },
            "golden_records_path": f"{manifests_dir}/orquestrado_consolidado/consolidado/golden_records_orquestrado_consolidado.json",
            "relatorio_path": f"{manifests_dir}/orquestrado_consolidado/consolidado/relatorio_consolidacao_orquestrado_consolidado.md"
        }


def main():
    parser = argparse.ArgumentParser(description='Orquestrador Inteligente de Extração Multi-Origem')
    parser.add_argument('--endereco', required=True, help='Endereço para busca')
    parser.add_argument('--sistemas', nargs='+', choices=['captei', 'fisgar', 'eemovel'], 
                       default=['eemovel', 'fisgar', 'captei'], help='Sistemas a consultar (ordem será otimizada)')
    parser.add_argument('--dados-dir', default='.', help='Diretório com arquivos de dados de tabela')
    parser.add_argument('--manifests-dir', default='.', help='Diretório dos manifests para consolidação')
    parser.add_argument('--limite', type=int, help='Limite de registros por sistema')
    parser.add_argument('--apenas-inventario', action='store_true', help='Apenas Estágio 1')
    parser.add_argument('--pular-extracao', action='store_true', help='Pular Estágio 2 (usar manifests existentes)')
    parser.add_argument('--log-dir', default='logs_orquestrado', help='Diretório para logs de processo')
    
    args = parser.parse_args()
    
    # Inicializar logger de processo
    logger = ProcessLearningLogger(args.log_dir, "orquestrado")
    
    try:
        # Carregar dados de tabela por sistema
        dados_por_sistema = {}
        for sistema in args.sistemas:
            arquivo_dados = Path(args.dados_dir) / f"exemplo_dados_tabela_{sistema}.json"
            if arquivo_dados.exists():
                with open(arquivo_dados, 'r', encoding='utf-8') as f:
                    dados_por_sistema[sistema] = json.load(f)
            else:
                # Fallback: usar arquivo genérico
                arquivo_generico = Path(args.dados_dir) / "exemplo_dados_tabela.json"
                if arquivo_generico.exists():
                    with open(arquivo_generico, 'r', encoding='utf-8') as f:
                        dados_por_sistema[sistema] = json.load(f)
                else:
                    dados_por_sistema[sistema] = []
        
        logger.log_decision(
            stage="init",
            decision="configurar_sistemas",
            rationale=f"Sistemas solicitados: {args.sistemas}. Ordem de extração: EEmovel → Fisgar → Captei",
            data={"sistemas": args.sistemas, "ordem_otimizada": [s["sistema"] for s in ORDEM_EXTRACAO]}
        )
        
        # Filtrar sistemas com dados
        sistemas_com_dados = [s for s in args.sistemas if dados_por_sistema.get(s)]
        
        if not sistemas_com_dados:
            logger.log_decision("init", "abortar", "Nenhum sistema tem dados de entrada", {})
            logger.finalize("aborted", {"reason": "no_data"})
            return
        
        # ===== ESTÁGIO 1: INVENTÁRIO =====
        print(f"\n{'='*60}")
        print(f"ESTÁGIO 1: INVENTÁRIO - {args.endereco}")
        print(f"{'='*60}")
        
        inventario = stage1_inventario(logger, args.endereco, sistemas_com_dados, dados_por_sistema)
        
        # Salvar inventário
        inv_path = Path(args.manifests_dir) / f"inventario_{args.endereco.replace(' ', '_').replace(',', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        salvar_json_seguro(inventario, inv_path)
        print(f"Inventário salvo: {inv_path}")
        print(f"  Proprietários únicos: {inventario['estatisticas']['proprietarios_unicos']}")
        print(f"  Moradores únicos: {inventario['estatisticas']['moradores_unicos']}")
        print(f"  Sistemas com dados: {inventario['estatisticas']['sistemas_com_dados']}")
        
        if args.apenas_inventario:
            logger.finalize("completed", {"stage": "inventory_only", "inventario": str(inv_path)})
            return
        
        # ===== ESTÁGIO 2: EXTRAÇÃO EM CASCATA =====
        if not args.pular_extracao:
            print(f"\n{'='*60}")
            print(f"ESTÁGIO 2: EXTRAÇÃO EM CASCATA")
            print(f"Ordem: EEmovel (R$0.81) → Fisgar (R$1.03) → Captei (R$1.57)")
            print(f"{'='*60}")
            
            resultado_extracao = stage2_extracao_cascata(
                logger, inventario, ORDEM_EXTRACAO, args.limite
            )
            
            print(f"Extração concluída:")
            for sistema, res in resultado_extracao["resultados_por_sistema"].items():
                print(f"  {sistema}: {res['novos']} novos, {res['processados']} processados, {res.get('pulados', 0)} pulados")
        else:
            print(f"\n{'='*60}")
            print(f"ESTÁGIO 2: PULADO (usando manifests existentes)")
            print(f"{'='*60}")
            resultado_extracao = {"chaves_extraidas": [], "resultados_por_sistema": {}}
        
        # ===== ESTÁGIO 3: MERGE & ENRIQUECIMENTO =====
        print(f"\n{'='*60}")
        print(f"ESTÁGIO 3: MERGE & ENRIQUECIMENTO")
        print(f"{'='*60}")
        
        resultado_merge = stage3_merge_enriquecimento(
            logger, inventario, resultado_extracao, args.manifests_dir
        )
        
        print(f"Consolidação concluída:")
        cr = resultado_merge["consolidation_report"]
        print(f"  Golden Records: {cr['total_golden_records']}")
        print(f"  Multi-Origem: {cr['multi_origem']}")
        print(f"  Single-Origem: {cr['single_origem']}")
        print(f"  Requer Revisão: {cr['requires_review']}")
        print(f"  Qualidade: {cr['quality_distribution']}")
        
        # ===== FINALIZAR =====
        log_path = logger.finalize("completed", {
            "endereco": args.endereco,
            "inventario": str(inv_path),
            "estagio1_stats": inventario["estatisticas"],
            "estagio2_resultados": resultado_extracao["resultados_por_sistema"],
            "estagio3_consolidacao": resultado_merge["consolidation_report"]
        })
        
        # Gerar relatório de aprendizado
        report_md = generate_learning_report(log_path)
        report_path = Path(log_path).with_suffix('.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_md)
        
        print(f"\n{'='*60}")
        print(f"CONCLUÍDO COM SUCESSO")
        print(f"{'='*60}")
        print(f"Log de processo: {log_path}")
        print(f"Relatório de aprendizado: {report_path}")
        print(f"Golden Records: {resultado_merge['golden_records_path']}")
        print(f"Relatório consolidação: {resultado_merge['relatorio_path']}")
        
    except Exception as e:
        logger.finalize("failed", {"error": str(e)})
        raise


if __name__ == '__main__':
    main()