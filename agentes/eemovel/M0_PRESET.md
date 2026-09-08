# M0 — Preset EEmóvel: fluxo, contratos e CLI (runner agent-browser)

**Data:** 2026-09-08
**Fonte única:** EEmóvel (`brokers.eemovel.com.br`)
**Motivo da escolha:** telefone/email direto na página de detalhe (sem modal intermediário), maior cota (500/mês), webhook S2-1 já aceita `eemovel`.

---

## 1. Fluxo mapeado

1. **Sessão:** `agent-browser` com sessão nomeada (`AGENT_BROWSER_SESSION=eemovel-runner`), perfil/cookies persistidos — login 1x, reuso depois.
2. **Login:** `https://brokers.eemovel.com.br/login` → preencher email/senha (env `EEMOVEL_EMAIL` / `EEMOVEL_SENHA`) → submeter. Logado se URL vira `/consulta`.
3. **Busca:** página `/consulta` → campos Cidade + Endereço + Nº inicial/final → clicar Buscar.
4. **Listagem (1 crédito):** tabela de possíveis PROPRIETÁRIOS e MORADORES. Uma consulta revela centenas de nomes; fica salva no manifest — retomada não repaga.
5. **Detalhe (1 crédito por registro):** cada linha leva à página de perfil com CPF, telefones, emails, endereços adicionais.

## 2. Contrato NDJSON de listagem (manifest record)

Uma linha da listagem → 1 registro no `manifest/manifest_<lote>.ndjson` (formato idêntico ao consumido pelo pipeline — zero mudança a jusante):

```json
{
  "name_raw": "ANA LAURA ALCANTARA ALVES",
  "name_canonical": "ana laura alcantara alves",
  "address_raw": "Rua Marc Chagall, 397",
  "address_canonical": "rua marc chagall 397",
  "unit_raw": "Ap 101 E 2 Vg Bl C Recanto Jacaranda",
  "unit_canonical": "ap 101 e 2 vg bl c recanto jacaranda",
  "unidade_vaga_raw": "",
  "unidade_vaga_canonical": "",
  "tipo_unidade": "apartamento",
  "tipo_pessoa": "Proprietário",
  "entity_type": "Pessoa Fisica",
  "source_system": "eemovel",
  "source_line": 1,
  "source_record_id": null,
  "record_key": "d82d867b9a4a2875afeb",
  "state": "inventariado",
  "timestamp": "2026-09-06T17:20:40.765417"
}
```

Helpers usados: `canonicalizar_texto`, `gerar_record_key_v2`, `classificar_entidade`, `classificar_tipo_unidade`, `parse_unidade` (`agentes/comum/__init__.py`).

## 3. Contrato de detalhe (`dados_modal` → `processar_modal_eemovel`)

```json
{
  "nome_completo": "...", "tipo_pessoa": "Proprietário",
  "endereco_principal": "...", "unidade": "...", "inscricao": "",
  "idade": null, "data_nascimento": null,
  "cpf": "***.***.***-**", "rg": "", "obito": false,
  "telefones": [{"numero_raw": "(11) 99999-9999", "digitos": "11999999999", "principal": true, "tipo": ""}],
  "emails": [{"endereco_raw": "a@b.com", "valido": true, "principal": false, "tipo": ""}],
  "enderecos_adicionais": [], "imovel_detalhes": {},
  "metadata": {"metodo_extracao": "browser_agent_browser", "modal_completo": true}
}
```

Processamento e persistência reusados sem alteração: `eemovel/extrator.py::processar_modal_eemovel` + `eemovel/persister.py::persistir_proprietario` (curated JSON + MD + raw).

## 4. CLI agent-browser (padrões do runner)

```bash
export AGENT_BROWSER_SESSION="eemovel-runner"
agent-browser open https://brokers.eemovel.com.br/login
agent-browser get url                      # detecta se já está logado
agent-browser fill  <sel> "<texto>"        # campos do formulário
agent-browser click <sel>                  # botão Buscar / linha da tabela
agent-browser wait <sel|ms>                # aguardar resultados
agent-browser eval "<js>"                  # extração determinística (innerText/rows)
agent-browser snapshot                     # accessibility tree p/ calibração
agent-browser cookies get > cookies.json   # backup de sessão
```

Seletores ficam em `agentes/eemovel/selectors.json` (calibráveis sem tocar no código).

## 5. Custos e guard-rails

- Listagem = 1 crédito; detalhe = 1 crédito/registro.
- Runner tem `--max-consultas N` (default 5) e registra cada ação que consome crédito em `logs/`.
- Teste de aceitação usa 1 endereço real do lote Marc Chagall.
- Modo `--mock-input` roda o pipeline inteiro sem browser (integração/testes, custo zero).
