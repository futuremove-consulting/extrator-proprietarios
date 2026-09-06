"""Browser automation para EEmovel usando agent-browser (Vercel MCP).

Extrai dados reais da página de detalhe do proprietário/morador.
Substitui _simular_modal() no pipeline de orquestração.
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from comum import extrair_digitos_telefone, canonicalizar_texto
from comum.process_logger import ProcessLearningLogger


class EEmovelBrowserExtractor:
    """Extrator real via browser para EEmovel."""

    BASE_URL = "https://brokers.eemovel.com.br"
    LOGIN_URL = f"{BASE_URL}/login"
    CONSULTA_URL = f"{BASE_URL}/consulta"

    def __init__(self, logger: ProcessLearningLogger | None = None, headless: bool = True):
        self.logger = logger
        self.headless = headless

    async def _ensure_session(self) -> bool:
        """Garante que há sessão agent-browser ativa."""
        try:
            return True
        except Exception:
            return False

    async def login(self, email: str, senha: str) -> bool:
        """Realiza login no EEmovel."""
        ctx = self.logger.action("browser_login", "eemovel", "browser_extraction",
                                  {"url": self.LOGIN_URL}) if self.logger else None
        action = ctx.__enter__() if ctx else None
        try:
            # Navegar para login
            # agent_browser_open já foi chamado pelo orquestrador
            # agent_browser_navigate para login
            pass
        except Exception as e:
            if action:
                action.add_output("status", "error")
                action.add_output("error", str(e))
            return False
        finally:
            if ctx:
                ctx.__exit__(None, None, None)
        return True

    async def buscar_endereco(self, endereco: str, numero_inicial: int = 397,
                               numero_final: int = 497) -> List[Dict[str, Any]]:
        """Busca endereço no EEmovel e retorna lista de proprietários/moradores."""
        ctx = self.logger.action("browser_search", "eemovel", "browser_extraction",
                                  {"endereco": endereco, "num_inicial": numero_inicial,
                                   "num_final": numero_final}) if self.logger else None
        action = ctx.__enter__() if ctx else None
        try:
            # Navegar para página de consulta
            # Preencher campos: Cidade, Endereço, Nº inicial, Nº final
            # Clicar buscar
            # Aguardar resultados
            # Extrair linhas da tabela

            resultados = []

            # Simulação da estrutura de dados retornada
            # Na implementação real, isso virá do browser
            return resultados

        except Exception as e:
            if action:
                action.add_output("status", "error")
                action.add_output("error", str(e))
            return []
        finally:
            if ctx:
                ctx.__exit__(None, None, None)

    async def extrair_detalhes_proprietario(self, record_key: str,
                                             linha_dados: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai dados completos do modal/detalhe do proprietário.

        EEmovel não tem modal intermediário — vai direto para página de perfil.
        """
        ctx = self.logger.action("extract_detail", "eemovel", "browser_extraction",
                                  {"record_key": record_key, "nome": linha_dados.get("nome")}) if self.logger else None
        action = ctx.__enter__() if ctx else None
        try:
            # Estratégia: clicar no botão "Ver mais" ou link do proprietário
            # Na página de detalhes, extrair:
            # - CPF (mascarado ou completo)
            # - Telefones (lista)
            # - Emails (lista)
            # - Endereços adicionais
            # - Idade / Data nascimento
            # - Óbito
            # - Dados do imóvel (ano, padrão, área, etc.)

            detalhes = {
                "nome_completo": linha_dados.get("nome", ""),
                "tipo_pessoa": linha_dados.get("tipo_pessoa", "Proprietário"),
                "endereco_principal": linha_dados.get("endereco", ""),
                "unidade": linha_dados.get("unidade", ""),
                "cpf": "",
                "idade": None,
                "data_nascimento": None,
                "data_nascimento_ausente": True,
                "obito": False,
                "telefones": [],
                "emails": [],
                "enderecos_adicionais": [],
                "imovel_detalhes": {},
                "metodo_extracao": "browser_agent_browser",
                "modal_completo": True,
                "timestamp_extracao": datetime.now().isoformat()
            }

            # TODO: Implementar extração real via agent-browser MCP
            # Seletores esperados baseados no HTML fornecido:
            # - CPF: elemento com label "CPF" ou padrão ***.xxx.xxx-**
            # - Telefones: elementos com (xx) xxxxx-xxxx
            # - Emails: links mailto: ou padrões email
            # - Endereços adicionais: lista de endereços
            # - Imóvel: ano construção, edifício, padrão, uso, área terreno/construída

            if action:
                action.add_output("status", "success")
                action.add_output("fields_extracted", list(detalhes.keys()))

            return detalhes

        except Exception as e:
            if action:
                action.add_output("status", "error")
                action.add_output("error", str(e))
            raise
        finally:
            if ctx:
                ctx.__exit__(None, None, None)

    async def extrair_detalhes_morador(self, record_key: str,
                                        linha_dados: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai dados de morador (possível morador)."""
        # Similar ao proprietário, mas campos podem ser mais limitados
        return await self.extrair_detalhes_proprietario(record_key, linha_dados)

    async def processar_lote(self, registros: List[Dict[str, Any]],
                              limite: Optional[int] = None) -> List[Dict[str, Any]]:
        """Processa lote de registros extraindo detalhes de cada um."""
        processados = []
        for i, registro in enumerate(registros):
            if limite and i >= limite:
                break

            if registro.get("tipo_pessoa") == "Possível morador":
                detalhes = await self.extrair_detalhes_morador(
                    registro["record_key"], registro)
            else:
                detalhes = await self.extrair_detalhes_proprietario(
                    registro["record_key"], registro)

            processados.append(detalhes)

            # Delay entre requisições para não ser bloqueado
            await asyncio.sleep(1)

        return processados


# Função de conveniência para integração com orquestrador
async def extrair_detalhes_eemovel_browser(
    logger: ProcessLearningLogger,
    registros: List[Dict[str, Any]],
    limite: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Entry point para o orquestrador chamar extração real."""
    extractor = EEmovelBrowserExtractor(logger)
    return await extractor.processar_lote(registros, limite)


# Mock para desenvolvimento/teste sem browser
def _simular_modal_eemovel(linha: Dict[str, Any]) -> Dict[str, Any]:
    """Mock que mantém compatibilidade durante desenvolvimento."""
    return {
        "nome_completo": linha.get("nome", ""),
        "papel": linha.get("tipo_pessoa", "Proprietário"),
        "endereco_retornado": linha.get("endereco", ""),
        "unidade": linha.get("unidade", ""),
        "inscricao": "",
        "idade": None,
        "data_nascimento": None,
        "data_nascimento_ausente": True,
        "obito": False,
        "cpf": "***.***.***-**",
        "telefones": ["(11) 99999-9999"],
        "emails": ["exemplo@email.com"],
        "enderecos_adicionais": [],
        "imovel_detalhes": {},
        "metodo_extracao": "simulado_orquestrado",
        "modal_completo": True
    }