---
name: parse-unidade-split
description: Unidade parseada em unidade_imovel + unidade_vaga + tipo_unidade; record_key v2 usa componentes separados
metadata:
  type: architecture
---

## Parse de Unidade Estruturado

### Função: `parse_unidade(unidade: str) -> Dict[str, str]`

Retorna:
```python
{
    'unidade_imovel': 'AP 101',           # Apartamento, sala, casa, cobertura, garden, loja
    'unidade_vaga': 'VG 3M TER',          # Vaga, garagem, box
    'tipo_unidade': 'apartamento'         # apartamento | cobertura | garden | sala | loja | vaga | outro
}
```

### Padrões Reconhecidos

**Imóvel**: AP, APARTAMENTO, CASA, SALA, LOJA, COBERTURA, GARDEN, TORRE X, BLOCO X, UNIDADE
**Vaga**: VG, VAGA, GARAGEM, BOX + sufixos (TER, SS1, SS2, M TER)

### Separação Inteligente
Divide por: vírgula, " e ", " + ", espaços duplos
Classifica cada parte por regex; ambíguos → keywords (VG/VAGA/GARAGEM/BOX = vaga)

### record_key v2
```python
gerar_record_key_v2(name_canonical, unidade_imovel, unidade_vaga, address_canonical)
# Componentes: nome|unidade_imovel|unidade_vaga|endereco
```

Melhora matching cross-origem: "AP 101 + VG 3M TER" vs "AP 101" vs "VG 3M TER" agora distinguíveis

### Integração
- `normalizar_linha_tabela()` em `extrair_orquestrado.py` usa parse_unidade
- Compatível com formato legado (`unidade` único) e novo (`unidade_imovel` + `unidade_vaga`)
- `tipo_unidade` salvo no manifest para análise/filtros