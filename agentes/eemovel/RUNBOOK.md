# RUNBOOK — Fluxo 1: EEmóvel (extração de uma fonte → CRM)

**Para quem:** operador (não precisa ser desenvolvedor).
**Pré-requisitos:** ver `PLANO_FLUXOS_EXTRACAO.md` seção 0 (R1–R8) e `agentes/F0_FOUNDATION.md`.

---

## Passo 0 — Preparar ambiente (uma vez por sessão)

```bash
cd /home/rochagus/projetos-linux/extrator-proprietarios
export PATH="/home/rochagus/.nvm/versions/node/v24.16.0/bin:$PATH"
cp .env.example .env   # se ainda não existe; preencher EEMOVEL_USERNAME/EEMOVEL_PASSWORD
set -a; source .env; set +a
```

Verificação rápida:

```bash
agent-browser --help | head -3          # R1: CLI ok
curl -s localhost:8000/healthz          # R4: API ok (se ativa)
```

## Passo 1 — Calibração de seletores (só da 1ª vez ou quando o site mudar)

```bash
python3 agentes/eemovel/runner.py live --calibrate --endereco "Rua Marc Chagall, 397"
```

- Faz login com as credenciais do `.env` e salva o snapshot da página de consulta em `agentes/<lote>/logs/calibrate_*.txt`
- Abra o snapshot, confira os campos da busca e da tabela de resultados
- Edite `agentes/eemovel/selectors.json` se algum seletor não bater
- Repita o calibrate até o snapshot mostrar a tela de consulta correta
- **Não consome crédito de listagem**

## Passo 2 — Execução piloto (consome 1 listagem + N detalhes)

```bash
python3 agentes/eemovel/runner.py live \
  --endereco "Rua Marc Chagall, 397" \
  --max-consultas 3
```

O que esperar no terminal:

```
[login] sessão ativa reutilizada
[busca] disparada para 'Rua Marc Chagall, 397' (1-200)
[listagem] NNN linhas extraídas
[0] NOME PESSOA: X tel, Y emails
...
[fim] lote=... processados=3
[fim] creditos: 4 acao(oes) paga(s), custo total 4 → agentes/<lote>/logs/relatorio_creditos.json
```

Verifique os artefatos:
- `agentes/<lote>/manifest/manifest_*.ndjson` — inventário completo
- `agentes/<lote>/curated/*.json|md` — registros com contato
- `agentes/<lote>/logs/relatorio_creditos.json` — auditoria de créditos

**Se der erro "Nenhuma linha extraída":** siga as 3 causas listadas no terminal (calibrate é a mais comum).

## Passo 3 — Fluxo pelo CRM (E2E)

1. Suba a API com o runner habilitado: `EEMOVEL_BROWSER_ENABLED=1 .venv/bin/extrator-api --port 8000`
2. No PilotCRM: **Captação** → fonte **EEmóvel** → preencher endereço → **Modo Live ON** → Buscar
3. Conferir resultados (ResultsTabs) → Revisar → **Cadastrar selecionados**
4. Conferir em **Imóveis Captados** (`/crm/properties/captados`): imóvel com badge EEmóvel + proprietários

## Passo 4 — Teste de idempotência (Done D3)

Reexecute o Passo 2 e o Passo 3 com o mesmo endereço e confira:

| O quê | Esperado |
|-------|----------|
| Novos contatos no Supabase | 0 (dedupe por CPF/telefone/nome+unidade) |
| Novos imóveis | 0 (upsert por `crm_property_sources` unique) |
| Novas linhas de manifest | só se novos registros apareceram na listagem |

## Passo 5 — Teste de resiliência (Done D6)

Durante o Passo 2, mate o browser (`agent-browser close --all`) após o 2º detalhe.
Reexecute o mesmo comando: o checkpoint (`agentes/<lote>/checkpoints/runner_checkpoint.json`)
retoma do último índice — **nenhum detalhe já pago é repetido**.

## Solução de problemas

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| `login falhou` no Passo 1 | credenciais erradas/expiradas | conferir `.env`; login manual no site |
| `Nenhuma linha extraída` repetido | seletores desatualizados | Passo 1 (calibrate) |
| Runner trava >15 min | site lento/página inesperada | `agent-browser close --all` e reexecutar (checkpoint retoma) |
| `agent-browser: command not found` | PATH sem Node v24 | export PATH do Passo 0 |
| API responde 502 no CRM | runner/API falhou | ver `logs` do lote + stderr da API |
