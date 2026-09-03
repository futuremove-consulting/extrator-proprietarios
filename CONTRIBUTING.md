# Contribuindo para Extrator de Proprietários

Obrigado por interessar-se em contribuir com o projeto Extrator de Proprietários!

## Como Contribuir

### Relatando Bugs

Antes de criar um issue, verifique se já existe um bug report similar.
Forneça o máximo de informações possível:
- Descrição detalhada do problema
- Passos para reproduzir
- Comportamento esperado vs. comportamento atual
- Ambiente (Python version, OS, etc.)
- Logs relevantes

### Sugestindo Funcionalidades

1. Verifique se já existe uma request similar
2. Descreva a funcionalidade proposta claramente
3. Explique o caso de uso
4. Forneça exemplos se possível

### Desenvolvendo

#### Setup do Ambiente

```bash
# Clone o repositório
git clone https://github.com/futuremove-consulting/extrator-proprietarios.git
cd extrator-proprietarios

# Crie um ambiente virtual (opcional mas recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# O projeto usa apenas bibliotecas padrão do Python
# Não é necessário instalar dependências para o básico
```

#### Estrutura do Código

- `agentes/comum/` - Funções utilitárias compartilhadas
- `agentes/captei/` - Lógica específica do Captei
- `agentes/fisgar/` - Lógica específica do Fisgar
- `agentes/extrair_*.py` - Scripts de orquestração

#### Convenções de Código

- Seguir PEP 8
- Usar type hints quando apropriado
- Documentar funções complexas
- Manter funções pequenas e focadas

#### Testes

```bash
# Rodar testes (quando implementados)
pytest

# Rodar com coverage
pytest --cov=agentes
```

### Processo de Pull Request

1. Fork o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Add nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Código de Conduta

Seja respeitoso e construtivo. Debates técnicos são bem-vindos, mas desrespeito não será tolerado.

## Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a licença MIT do projeto.