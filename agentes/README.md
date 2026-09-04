# Sistema de Extração de Proprietários

Sistema modular para extração de dados de proprietários dos sistemas Captei e Fisgar, com persistência estruturada, manifest append-only e checkpoints para retomada.

## Estrutura do Projeto

```
agentes/
├── comum/
│   └── __init__.py          # Funções utilitárias compartilhadas
├── captei/
│   ├── __init__.py          # Agente principal Captei
│   ├── extrator.py          # Lógica de extração específica Captei
│   └── persister.py         # Persistência de dados Captei
├── fisgar/
│   ├── __init__.py          # Agente principal Fisgar
│   ├── extrator.py          # Lógica de extração específica Fisgar
│   └── persister.py         # Persistência de dados Fisgar
├── extrair_captei.py        # Script de orquestração Captei
├── extrair_fisgar.py        # Script de orquestração Fisgar
├── exemplo_dados_tabela.json # Exemplo de dados de entrada
└── exemplo_dados_modal.json # Exemplo de dados de modal
```

## Componentes

### Módulo Comum
Funções utilitárias compartilhadas:
- `canonicalizar_texto()` - Normalização para matching
- `gerar_record_key()` - Chave única composta
- `classificar_entidade()` - Classificação PF/PJ
- `criar_estrutura_lote()` - Criação de diretórios
- `salvar_json_seguro()` - Persistência JSON determinística
- `append_ndjson()` - Logs append-only
- Funções de validação e formatação

### Agente Captei
Gerencia extração do sistema Captei:
- Inventário de tabela paginada
- Classificação automática PF/PJ
- Manifest append-only
- Checkpoints para retomada
- Validação de WhatsApp
- Relatórios de reconciliação

### Agente Fisgar
Gerencia extração do sistema Fisgar:
- Inventário de tabela virtualizada
- Localização de CTA por DOM relativo
- Suporte a scroll position
- Dados específicos (CPF, RG)
- Checkpoints com posição de scroll

## Uso

### Captei

```bash
# Apenas inventariar
python3 extrair_captei.py \
  --lote teste_captei \
  --endereco "Rua Marc Chagall, 397" \
  --dados exemplo_dados_tabela.json \
  --apenas-inventario

# Inventariar e processar (com limite)
python3 extrair_captei.py \
  --lote teste_captei \
  --endereco "Rua Marc Chagall, 397" \
  --dados exemplo_dados_tabela.json \
  --limite 10
```

### Fisgar

```bash
# Apenas inventariar
python3 extrair_fisgar.py \
  --lote teste_fisgar \
  --endereco "Rua Marc Chagall, 397" \
  --dados exemplo_dados_tabela.json \
  --apenas-inventario

# Inventariar e processar (com limite)
python3 extrair_fisgar.py \
  --lote teste_fisgar \
  --endereco "Rua Marc Chagall, 397" \
  --dados exemplo_dados_tabela.json \
  --limite 10
```

## Estrutura de Saída

Cada lote gera a seguinte estrutura:

```
<nome_lote>/
├── manifest/
│   └── manifest_<lote>.ndjson      # Manifest append-only
├── checkpoints/
│   └── checkpoint_<lote>.json     # Estado para retomada
├── logs/
│   └── extraction_log_<lote>.ndjson # Log de eventos
├── raw/
│   └── *_raw.json                 # Dados brutos
└── curated/
    ├── <nome>_<key>.json          # Dados estruturados
    ├── <nome>_<key>.md            # Relatório legível
    └── consolidado_<lote>.json    # Consolidação do lote
```

## Máquina de Estados

Estados para cada registro:
- `inventariado` - Registro no manifest
- `pendente_modal` - Aguardando processamento
- `empresa_classificada` - Empresa excluída
- `resultado_persistido` - Dados salvos
- `concluido` - Processamento completo
- `revisao_manual` - Requer intervenção manual

## Integração com Browser

Para implementação real com browser automation:

1. **Captei**: Integrar com Playwright/Selenium para:
   - Navegação na interface
   - Paginação de resultados
   - Abertura de modais
   - Validação de WhatsApp
   - Extração de dados

2. **Fisgar**: Integrar com agent-browser para:
   - Navegação DOM relativo
   - Localização de CTA por linha
   - Gerenciamento de scroll
   - Extração de modal
   - Snapshot de estado

## Migração de Dados Existentes

O sistema inclui script para migrar dados extraídos anteriormente:

```bash
python3 migrar_dados_existentes.py
```

Este script:
- Lê JSONs existentes do Captei parcial
- Converte para o novo formato estruturado
- Cria manifest com estado `resultado_persistido`
- Gera arquivos individuais JSON/MD
- Preserva todos os dados originais

## Integração com Dados Anteriores

Os dados extraídos anteriormente foram migrados com sucesso:
- 20 registros do Captei parcial migrados
- Formato compatível com novo sistema
- Manifest atualizado com estado correto
- Estrutura de diretórios mantida

## Próximos Passos

1. Implementar integração real com browser automation
2. Adicionar suporte a retomada automática
3. Implementar validação de qualidade avançada
4. Adicionar cross-reference entre sistemas
5. Criar dashboards de monitoramento

## Segurança

- Não armazenar credenciais
- Logs sem dados sensíveis
- Manifest append-only (auditável)
- RAW preservado (não sobrescrito)
- Finalidade definida (LGPD)