# Extrator de Proprietários

Sistema modular para extração de dados de proprietários dos sistemas Captei e Fisgar, com persistência estruturada, manifest append-only e checkpoints para retomada.

## 🎯 Objetivo

Transformar bases fragmentadas de proprietários, moradores, imóveis e empreendimentos em uma estrutura normalizada, segregada, auditável e enriquecida.

## 🏗️ Arquitetura

### Estrutura do Projeto

```
extrator-proprietarios/
├── agentes/                    # Sistema de extração modular
│   ├── comum/                # Utilitários + consolidação multi-origem
│   ├── captei/               # Agente específico para Captei
│   ├── fisgar/               # Agente específico para Fisgar
│   ├── eemovel/              # Agente específico para EEmovel
│   ├── extrair_captei.py     # Script de orquestração Captei
│   ├── extrair_fisgar.py     # Script de orquestração Fisgar
│   ├── extrair_eemovel.py    # Script de orquestração EEmovel
│   ├── consolidar_multi_origem.py  # Pipeline de consolidação (8 stages)
│   ├── migrar_dados_existentes.py  # Migração de dados anteriores
│   └── benchmark_cross_origem.py   # Análise de overlap entre origens
├── DOCUMENTACAO_TECNICA.md   # Documentação técnica e roadmap
├── extracted/                # Dados extraídos anteriormente
└── README.md                 # Este arquivo
```

### Componentes Principais

#### Módulo Comum
Funções utilitárias compartilhadas:
- `canonicalizar_texto()` - Normalização para matching
- `gerar_record_key()` - Chave única composta
- `classificar_entidade()` - Classificação PF/PJ
- `criar_estrutura_lote()` - Criação de diretórios
- Funções de validação e formatação

#### Agente Captei
Gerencia extração do sistema Captei:
- Inventário de tabela paginada
- Classificação automática PF/PJ
- Manifest append-only
- Checkpoints para retomada
- Validação de WhatsApp
- Relatórios de reconciliação

#### Agente Fisgar
Gerencia extração do sistema Fisgar:
- Inventário de tabela virtualizada
- Localização de CTA por DOM relativo
- Suporte a scroll position
- Dados específicos (CPF, RG)
- Checkpoints com posição de scroll

#### Agente EEmovel
Gerencia extração do sistema EEmovel:
- Consulta de proprietários + moradores ("Possível morador")
- Múltiplos endereços e CPF
- Campo de busca por rua e faixa de números
- Dados específicos: CPF, RG, data de nascimento, óbito

#### Consolidação Multi-Origem
Pipeline unificado (8 stages) para unir Captei, Fisgar e EEmovel:
- **Load** — leitura de manifests NDJSON por origem
- **Normalize** — canonicalização (aplicada na extração)
- **Sanitize** — camada LGPD
- **Deduplicate** — resolução de identidade (CPF forte > record_key exato > telefone+nome > fuzzy)
- **Merge** — políticas por campo (most_complete, union_dedup, source_priority)
- **Validate** — validação cross-origem
- **Score** — confidence 0-100 por campo, quality tier, revisão
- **Output** — Golden Records JSON + relatório MD

CLI: 

## 🚀 Uso

### Captei

```bash
cd agentes

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
cd agentes

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

### Migração de Dados

```bash
cd agentes

# Migrar dados extraídos anteriormente
python3 migrar_dados_existentes.py
```

## 📊 Estrutura de Saída

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

## 🔄 Máquina de Estados

Estados para cada registro:
- `inventariado` - Registro no manifest
- `pendente_modal` - Aguardando processamento
- `empresa_classificada` - Empresa excluída
- `resultado_persistido` - Dados salvos
- `concluido` - Processamento completo
- `revisao_manual` - Requer intervenção manual

## 📋 Status Atual

### Captei
- ✅ Sistema de extração implementado
- ✅ Testes funcionais concluídos
- ✅ Migração de 20 registros anteriores
- ⏳ Integração com browser automation pendente

### Fisgar
- ✅ Sistema de extração implementado
- ✅ Testes funcionais concluídos
- ⏳ Integração com agent-browser pendente
- ⏳ Resolução de autenticação (401 Unauthorized)

## 🔒 Segurança

- Não armazenar credenciais
- Logs sem dados sensíveis
- Manifest append-only (auditável)
- RAW preservado (não sobrescrito)
- Finalidade definida (LGPD)

## 🚧 Próximos Passos

1. Implementar integração real com browser automation
2. Adicionar suporte a retomada automática
3. Implementar validação de qualidade avançada
4. Adicionar cross-reference entre sistemas
5. Criar dashboards de monitoramento

## 📄 Licença

Copyright © 2026 Futuremove Consulting