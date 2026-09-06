"""Agente EEmovel para extração de proprietários e moradores."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from comum import (
    append_ndjson,
    canonicalizar_texto,
    carregar_json,
    classificar_entidade,
    criar_estrutura_lote,
    gerar_record_key,
    normalizar_unidade,
    salvar_json_seguro,
    timestamp_iso,
)


class AgenteEEmovel:
    """Agente para extração de proprietários e moradores do sistema EEmovel."""

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

    def _carregar_ou_criar_checkpoint(self) -> dict[str, Any]:
        """Carrega checkpoint existente ou cria novo."""
        if self.checkpoint_path.exists():
            return carregar_json(self.checkpoint_path)

        checkpoint = {
            'lote': self.nome_lote,
            'state': 'inicializado',
            'address_canonical': None,
            'address_raw': None,
            'number_from': None,
            'number_to': None,
            'counts': {
                'manifest_total': 0,
                'pessoa_fisica_pending': 0,
                'pessoa_fisica_completed': 0,
                'empresas_excluidas': 0,
                'revisao_manual': 0,
                'moradores': 0
            },
            'last_completed_key': None,
            'next_record_key': None,
            'scroll_position': None,
            'creditos_disponiveis': None,
            'timestamp': timestamp_iso(),
            'errors': []
        }
        salvar_json_seguro(checkpoint, self.checkpoint_path)
        return checkpoint

    def _carregar_manifest(self) -> list[dict[str, Any]]:
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
            self.checkpoint_atual['counts']['empresas_excluidas'] += delta
        elif estado == 'revisao_manual':
            self.checkpoint_atual['counts']['revisao_manual'] += delta
        elif estado == 'morador':
            self.checkpoint_atual['counts']['moradores'] += delta

        self.checkpoint_atual['counts']['manifest_total'] = (
            self.checkpoint_atual['counts']['pessoa_fisica_pending'] +
            self.checkpoint_atual['counts']['pessoa_fisica_completed'] +
            self.checkpoint_atual['counts']['empresas_excluidas'] +
            self.checkpoint_atual['counts']['revisao_manual'] +
            self.checkpoint_atual['counts']['moradores']
        )

    def processar_linha_tabela(self, linha: dict[str, Any]) -> dict[str, Any] | None:
        """Processa uma linha da tabela do EEmovel e retorna registro estruturado."""
        nome = linha.get('nome', '').strip()
        unidade = linha.get('unidade', '').strip()
        endereco = linha.get('endereco', '').strip()
        tipo_pessoa = linha.get('tipo_pessoa', '').strip()  # "Proprietário" ou "Possível morador"

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

        # Determinar estado inicial baseado no tipo
        if tipo_pessoa == 'Possível morador':
            estado_inicial = 'morador'
        elif entity_type == 'Pessoa Fisica':
            estado_inicial = 'pendente_modal'
        else:
            estado_inicial = 'empresa_classificada'

        registro = {
            'record_key': record_key,
            'name_raw': nome,
            'name_canonical': name_canonical,
            'unit_raw': unidade,
            'unit_canonical': unit_canonical,
            'address_raw': endereco,
            'address_canonical': address_canonical,
            'entity_type': entity_type,
            'tipo_pessoa': tipo_pessoa,  # "Proprietário" ou "Possível morador"
            'state': estado_inicial,
            'telefones': [],
            'emails': [],
            'enderecos_adicionais': [],  # Específico EEmovel: múltiplos endereços
            'data_nascimento': None,
            'idade': None,
            'cpf': None,
            'rg': None,
            'obito': False,
            'inscricao': None,
            'papel': None,
            'imovel_detalhes': {},  # Específico EEmovel: ano, padrão, área, etc.
            'timestamp': timestamp_iso(),
            'source_line': linha.get('source_line'),
            'source_record_id': linha.get('source_record_id'),
            'dom_reference': linha.get('dom_reference')
        }

        return registro

    def adicionar_ao_manifest(self, registro: dict[str, Any]) -> None:
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
        elif estado == 'morador':
            registro['state'] = 'morador'
            self._atualizar_contagem_estado('morador')

        self.checkpoint_atual['timestamp'] = timestamp_iso()
        salvar_json_seguro(self.checkpoint_atual, self.checkpoint_path)

    def obter_proximo_pendente(self) -> dict[str, Any] | None:
        """Retorna o próximo registro pendente de processamento (proprietários)."""
        for registro in self.manifest:
            if registro.get('state') == 'pendente_modal':
                return registro
        return None

    def obter_proximo_morador(self) -> dict[str, Any] | None:
        """Retorna o próximo morador para processamento opcional."""
        for registro in self.manifest:
            if registro.get('state') == 'morador':
                return registro
        return None

    def atualizar_estado_registro(self, record_key: str, novo_estado: str,
                                     dados_adicionais: dict[str, Any] | None = None) -> None:
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

    def salvar_checkpoint_com_scroll(self, scroll_position: int | None = None,
                                      creditos: int | None = None) -> None:
        """Salva checkpoint incluindo posição de scroll e créditos."""
        if scroll_position is not None:
            self.checkpoint_atual['scroll_position'] = scroll_position
        if creditos is not None:
            self.checkpoint_atual['creditos_disponiveis'] = creditos
        self.checkpoint_atual['timestamp'] = timestamp_iso()
        salvar_json_seguro(self.checkpoint_atual, self.checkpoint_path)

    def registrar_log(self, evento: str, dados: dict[str, Any]) -> None:
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

        relatorio = f"""# Relatório de Reconciliação - {self.nome_lote} (EEmovel)

Gerado em: {timestamp_iso()}

## Estatísticas

| Indicador | Quantidade |
|-----------|------------|
| Total no manifest | {counts['manifest_total']} |
| Proprietários PF pendentes | {counts['pessoa_fisica_pending']} |
| Proprietários PF concluídos | {counts['pessoa_fisica_completed']} |
| Empresas excluídas | {counts['empresas_excluidas']} |
| Revisão manual | {counts['revisao_manual']} |
| Moradores (Possível morador) | {counts['moradores']} |

## Estado Atual

- Estado: {self.checkpoint_atual['state']}
- Último concluído: {self.checkpoint_atual['last_completed_key'] or 'Nenhum'}
- Próximo pendente: {self.checkpoint_atual['next_record_key'] or 'Nenhum'}
- Posição scroll: {self.checkpoint_atual['scroll_position'] or 'Não registrado'}
- Créditos disponíveis: {self.checkpoint_atual['creditos_disponiveis'] or 'Não registrado'}

## Erros

"""

        if self.checkpoint_atual['errors']:
            for erro in self.checkpoint_atual['errors']:
                relatorio += f"- {erro}\n"
        else:
            relatorio += "Nenhum erro registrado.\n"

        return relatorio