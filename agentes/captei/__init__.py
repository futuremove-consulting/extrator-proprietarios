"""Agente Captei para extração de proprietários."""

from pathlib import Path
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

from comum import (
    criar_estrutura_lote,
    canonicalizar_texto,
    gerar_record_key,
    classificar_entidade,
    normalizar_unidade,
    salvar_json_seguro,
    carregar_json,
    append_ndjson,
    timestamp_iso
)


class AgenteCaptei:
    """Agente para extração de proprietários do sistema Captei."""
    
    def __init__(self, diretorio_base: str, nome_lote: str):
        self.diretorio_base = Path(diretorio_base)
        self.nome_lote = nome_lote
        self.estrutura = criar_estrutura_lote(nome_lote, diretorio_base)
        
        # Caminhos dos arquivos principais
        self.manifest_path = self.estrutura['manifest'] / f'manifest_{nome_lote}.ndjson'
        self.checkpoint_path = self.estrutura['checkpoints'] / f'checkpoint_{nome_lote}.json'
        self.log_path = self.estrutura['logs'] / f'extraction_log_{nome_lote}.ndjson'
        
        # Estado inicial
        self.checkpoint_atual = self._carregar_ou_criar_checkpoint()
        self.manifest = self._carregar_manifest()
        
    def _carregar_ou_criar_checkpoint(self) -> Dict[str, Any]:
        """Carrega checkpoint existente ou cria novo."""
        if self.checkpoint_path.exists():
            return carregar_json(self.checkpoint_path)
        
        checkpoint = {
            'lote': self.nome_lote,
            'state': 'inicializado',
            'address_canonical': None,
            'address_raw': None,
            'counts': {
                'manifest_total': 0,
                'pessoa_fisica_pending': 0,
                'pessoa_fisica_completed': 0,
                'companies_excluded': 0,
                'revisao_manual': 0
            },
            'last_completed_key': None,
            'next_record_key': None,
            'saldo_capcoins': None,
            'timestamp': timestamp_iso(),
            'errors': []
        }
        salvar_json_seguro(checkpoint, self.checkpoint_path)
        return checkpoint
    
    def _carregar_manifest(self) -> List[Dict[str, Any]]:
        """Carrega manifest existente ou retorna lista vazia."""
        if not self.manifest_path.exists():
            return []
        
        manifest = []
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            for linha in f:
                if linha.strip():
                    manifest.append(json.loads(linha))
        return manifest
    
    def _atualizar_contagem_estado(self, estado: str, delta: int = 1):
        """Atualiza contagem de um estado específico."""
        if estado == 'pendente_modal':
            self.checkpoint_atual['counts']['pessoa_fisica_pending'] += delta
        elif estado in ['resultado_persistido', 'concluido']:
            self.checkpoint_atual['counts']['pessoa_fisica_completed'] += delta
        elif estado == 'empresa_classificada':
            self.checkpoint_atual['counts']['companies_excluded'] += delta
        elif estado == 'revisao_manual':
            self.checkpoint_atual['counts']['revisao_manual'] += delta
        
        self.checkpoint_atual['counts']['manifest_total'] = (
            self.checkpoint_atual['counts']['pessoa_fisica_pending'] +
            self.checkpoint_atual['counts']['pessoa_fisica_completed'] +
            self.checkpoint_atual['counts']['companies_excluded'] +
            self.checkpoint_atual['counts']['revisao_manual']
        )
    
    def processar_linha_tabela(self, linha: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processa uma linha da tabela do Captei e retorna registro estruturado."""
        nome = linha.get('nome', '').strip()
        unidade = linha.get('unidade', '').strip()
        endereco = linha.get('endereco', '').strip()
        
        if not nome:
            return None
        
        # Classificar entidade
        entity_type = classificar_entidade(nome)
        
        # Normalizar para matching
        name_canonical = canonicalizar_texto(nome)
        unit_canonical = normalizar_unidade(unidade)
        address_canonical = canonicalizar_texto(endereco)
        
        # Gerar chave única
        record_key = gerar_record_key(name_canonical, unit_canonical, address_canonical)
        
        registro = {
            'record_key': record_key,
            'name_raw': nome,
            'name_canonical': name_canonical,
            'unit_raw': unidade,
            'unit_canonical': unit_canonical,
            'address_raw': endereco,
            'address_canonical': address_canonical,
            'entity_type': entity_type,
            'state': 'inventariado',
            'telefones': [],
            'emails': [],
            'data_nascimento': None,
            'idade': None,
            'inscricao': None,
            'papel': None,
            'timestamp': timestamp_iso(),
            'source_line': linha.get('source_line'),
            'source_record_id': linha.get('source_record_id')
        }
        
        return registro
    
    def adicionar_ao_manifest(self, registro: Dict[str, Any]) -> None:
        """Adiciona registro ao manifest append-only."""
        append_ndjson(registro, self.manifest_path)
        self.manifest.append(registro)
        
        # Atualizar estado inicial
        estado = registro.get('state', 'inventariado')
        if estado == 'pendente_modal':
            registro['state'] = 'pendente_modal'
            self._atualizar_contagem_estado('pendente_modal')
        elif registro.get('entity_type') == 'Empresa':
            registro['state'] = 'empresa_classificada'
            self._atualizar_contagem_estado('empresa_classificada')
        
        self.checkpoint_atual['timestamp'] = timestamp_iso()
        salvar_json_seguro(self.checkpoint_atual, self.checkpoint_path)
    
    def obter_proximo_pendente(self) -> Optional[Dict[str, Any]]:
        """Retorna o próximo registro pendente de processamento."""
        for registro in self.manifest:
            if registro.get('state') == 'pendente_modal':
                return registro
        return None
    
    def atualizar_estado_registro(self, record_key: str, novo_estado: str, 
                                   dados_adicionais: Optional[Dict[str, Any]] = None) -> None:
        """Atualiza estado de um registro específico no manifest."""
        for i, registro in enumerate(self.manifest):
            if registro.get('record_key') == record_key:
                # Atualizar estado
                self.manifest[i]['state'] = novo_estado
                self.manifest[i]['state_timestamp'] = timestamp_iso()
                
                # Adicionar dados adicionais se fornecidos
                if dados_adicionais:
                    self.manifest[i].update(dados_adicionais)
                
                # Reescrever manifest (append-only não permite update direto)
                self._reescrever_manifest()
                
                # Atualizar checkpoint
                if novo_estado in ['resultado_persistido', 'concluido']:
                    self.checkpoint_atual['last_completed_key'] = record_key
                    self._atualizar_contagem_estado('resultado_persistido', -1)
                    self._atualizar_contagem_estado('concluido')
                
                self.checkpoint_atual['timestamp'] = timestamp_iso()
                salvar_json_seguro(self.checkpoint_atual, self.checkpoint_path)
                return
        
        raise ValueError(f"Registro com key {record_key} não encontrado no manifest")
    
    def _reescrever_manifest(self) -> None:
        """Reescreve o manifest completo (usar com cautela)."""
        backup_path = self.manifest_path.with_suffix('.ndjson.backup')
        if self.manifest_path.exists():
            self.manifest_path.rename(backup_path)
        
        for registro in self.manifest:
            append_ndjson(registro, self.manifest_path)
    
    def salvar_checkpoint(self) -> None:
        """Salva estado atual do checkpoint."""
        self.checkpoint_atual['timestamp'] = timestamp_iso()
        salvar_json_seguro(self.checkpoint_atual, self.checkpoint_path)
    
    def registrar_log(self, evento: str, dados: Dict[str, Any]) -> None:
        """Registra evento no log de extração."""
        log_entry = {
            'timestamp': timestamp_iso(),
            'evento': evento,
            'dados': dados
        }
        append_ndjson(log_entry, self.log_path)
    
    def gerar_relatorio_reconciliacao(self) -> str:
        """Gera relatório de reconciliação em markdown."""
        counts = self.checkpoint_atual['counts']
        
        relatorio = f"""# Relatório de Reconciliação - {self.nome_lote}

Gerado em: {timestamp_iso()}

## Estatísticas

| Indicador | Quantidade |
|-----------|------------|
| Total no manifest | {counts['manifest_total']} |
| Pessoa física pendente | {counts['pessoa_fisica_pending']} |
| Pessoa física concluída | {counts['pessoa_fisica_completed']} |
| Empresas excluídas | {counts['companies_excluded']} |
| Revisão manual | {counts['revisao_manual']} |

## Estado Atual

- Estado: {self.checkpoint_atual['state']}
- Último concluído: {self.checkpoint_atual['last_completed_key'] or 'Nenhum'}
- Próximo pendente: {self.checkpoint_atual['next_record_key'] or 'Nenhum'}
- Saldo Capcoins: {self.checkpoint_atual['saldo_capcoins'] or 'Não registrado'}

## Erros

"""
        
        if self.checkpoint_atual['errors']:
            for erro in self.checkpoint_atual['errors']:
                relatorio += f"- {erro}\n"
        else:
            relatorio += "Nenhum erro registrado.\n"
        
        return relatorio