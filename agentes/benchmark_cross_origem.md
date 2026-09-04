# Benchmark Cross-Origem — Captei, Fisgar, EEmovel

## 1. Estatísticas por Origem

| Origem | Total | PF | Empresa | Moradores | c/ CPF | c/ Telefone | c/ Email | Keys Únicas |
|--------|-------|-----|---------|-----------|--------|-------------|----------|-------------|
| Captei | 15 | 12 | 3 | 0 | 0 | 4 | 4 | 5 |
| Fisgar | 15 | 12 | 3 | 0 | 0 | 4 | 4 | 5 |
| Eemovel | 25 | 23 | 2 | 5 | 0 | 5 | 5 | 25 |

## 2. Overlap por Record Key (Exato)

Total de chaves únicas estimadas: **30**

Overlaps encontrados: **5**

| Record Key | Origens |
|------------|---------|
| 2736f3820b80323c3893 | captei, fisgar |
| 370d522d890a833fa37b | captei, fisgar |
| 52e3a62efbbc29ff7985 | captei, fisgar |
| 593fb07b670b5bc7f764 | captei, fisgar |
| d112a0dbc9875bba1850 | captei, fisgar |

## 3. Overlap por CPF

Overlaps encontrados: **0**

| CPF (mascarado) | Origens |
|-----------------|---------|

## 4. Overlap por Telefone

Overlaps encontrados: **1**

| Telefone (dígitos) | Origens |
|--------------------|---------|
| (11) 99999-9999 | captei, fisgar, eemovel |

## 5. Overlap por Email

Overlaps encontrados: **1**

| Email | Origens |
|-------|---------|
| exemplo@email.com | captei, fisgar, eemovel |

## 6. Fuzzy Matches (Nome + Endereço similar)

Matches encontrados: **42**

| Origem 1 | Origem 2 | Nome 1 | Nome 2 | Sim. Nome | Sim. End | Key 1 | Key 2 |
|----------|----------|--------|--------|-----------|----------|-------|-------|
| captei | fisgar | ANA PAULA RODRIGUES | ANA PAULA RODRIGUES | 1.0 | 1.0 | 593fb07b... | 593fb07b... |
| captei | fisgar | ANA PAULA RODRIGUES | ANA PAULA RODRIGUES | 1.0 | 1.0 | 593fb07b... | 593fb07b... |
| captei | fisgar | ANA PAULA RODRIGUES | ANA PAULA RODRIGUES | 1.0 | 1.0 | 593fb07b... | 593fb07b... |
| captei | fisgar | JOÃO SILVA SANTOS | JOÃO SILVA SANTOS | 1.0 | 1.0 | 2736f382... | 2736f382... |
| captei | fisgar | JOÃO SILVA SANTOS | JOÃO SILVA SANTOS | 1.0 | 1.0 | 2736f382... | 2736f382... |
| captei | fisgar | JOÃO SILVA SANTOS | JOÃO SILVA SANTOS | 1.0 | 1.0 | 2736f382... | 2736f382... |
| captei | fisgar | MARIA APARECIDA OLIVEIRA | MARIA APARECIDA OLIVEIRA | 1.0 | 1.0 | 52e3a62e... | 52e3a62e... |
| captei | fisgar | MARIA APARECIDA OLIVEIRA | MARIA APARECIDA OLIVEIRA | 1.0 | 1.0 | 52e3a62e... | 52e3a62e... |
| captei | fisgar | MARIA APARECIDA OLIVEIRA | MARIA APARECIDA OLIVEIRA | 1.0 | 1.0 | 52e3a62e... | 52e3a62e... |
| captei | fisgar | PEDRO HENRIQUE COSTA | PEDRO HENRIQUE COSTA | 1.0 | 1.0 | d112a0db... | d112a0db... |
| captei | fisgar | PEDRO HENRIQUE COSTA | PEDRO HENRIQUE COSTA | 1.0 | 1.0 | d112a0db... | d112a0db... |
| captei | fisgar | PEDRO HENRIQUE COSTA | PEDRO HENRIQUE COSTA | 1.0 | 1.0 | d112a0db... | d112a0db... |
| captei | fisgar | ANA PAULA RODRIGUES | ANA PAULA RODRIGUES | 1.0 | 1.0 | 593fb07b... | 593fb07b... |
| captei | fisgar | ANA PAULA RODRIGUES | ANA PAULA RODRIGUES | 1.0 | 1.0 | 593fb07b... | 593fb07b... |
| captei | fisgar | ANA PAULA RODRIGUES | ANA PAULA RODRIGUES | 1.0 | 1.0 | 593fb07b... | 593fb07b... |
| captei | fisgar | JOÃO SILVA SANTOS | JOÃO SILVA SANTOS | 1.0 | 1.0 | 2736f382... | 2736f382... |
| captei | fisgar | JOÃO SILVA SANTOS | JOÃO SILVA SANTOS | 1.0 | 1.0 | 2736f382... | 2736f382... |
| captei | fisgar | JOÃO SILVA SANTOS | JOÃO SILVA SANTOS | 1.0 | 1.0 | 2736f382... | 2736f382... |
| captei | fisgar | MARIA APARECIDA OLIVEIRA | MARIA APARECIDA OLIVEIRA | 1.0 | 1.0 | 52e3a62e... | 52e3a62e... |
| captei | fisgar | MARIA APARECIDA OLIVEIRA | MARIA APARECIDA OLIVEIRA | 1.0 | 1.0 | 52e3a62e... | 52e3a62e... |

... e mais 22 matches.

## 7. Análise de Qualidade do record_key Atual


- Overlaps por record_key exato: **5**
- Overlaps por CPF (forte): **0**
- Overlaps por telefone: **1**
- Overlaps por email: **1**
- Fuzzy matches (>0.85 nome, >0.8 end): **42**

**Recomendações:**
1. **CPF deve ser fator primário** de identidade quando disponível em ≥2 origens
2. **record_key atual (name|unit|address)** funciona para matching exato, mas falha em variações de unidade
3. **Telefone + Nome** é boa chave secundária para deduplicação
4. **Fuzzy match** necessário para capturar variações de digitação/abreviação de unidade
5. **Moradores EEmovel** não devem ser dedupados com proprietários (tipo_pessoa diferente)
