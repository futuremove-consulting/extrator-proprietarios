# F0 — Fundação Compartilhada: inventário de verificação

**Data:** 2026-09-08 · **Plano:** PLANO_FLUXOS_EXTRACAO.md seção 2

## F0.1 — agent-browser CLI (R1) ✅ VERIFICADO

- CLI: `/home/rochagus/.nvm/versions/node/v24.16.0/bin/agent-browser` (exige `export PATH` no shell não-interativo)
- Comandos confirmados: `open/get url/fill/click/wait/read/snapshot/eval/cookies/close`
- Sessões nomeadas: `--session <nome>` por comando (diretório `~/.agent-browser/sessions/` persiste cookies)
- Daemon: browser persiste entre comandos; idle-timeout 1h; `--restore` restaura estado

## F0.2 — Credenciais (R2) ⏳ AGUARDA OPERADOR

Template criado: `.env.example` (raiz). Operador deve preencher `.env` com:
- `EEMOVEL_EMAIL` / `EEMOVEL_SENHA` (Fluxo 1)
- Login manual validado na semana (evidência: print/log)

## F0.3 — Sondador de Cotas (R8) ✅ CLI VERIFICADA

`python3 agentes/sondar_cotas.py iniciar|medir|veredito|status|aplicar`
Protocolo ~15 min/sistema (P1–P5) → gera `agentes/sondagem/custos_verificados.json`.
**Pendente de execução:** requer operador com acesso aos 3 sistemas.

## F0.4 — Stack (R4) ✅ VERIFICADO

- Flask app importa e expõe `/healthz` + `/api/v1/extract` (testado)
- Subir API: `.venv/bin/extrator-api --port 8000` (ou `.venv/bin/python -m extrator_prop.api.cli`)
- CRM: `pnpm --filter pilotcrm dev` com `EXTRATOR_API_URL=http://localhost:8000`
- Prova de vida: `curl localhost:8000/healthz`

## F0.5 — Endereços-piloto (R6) ✅ DEFINIDOS

| ID | Endereço | Perfil esperado | Uso |
|----|----------|-----------------|-----|
| P1 | Rua Marc Chagall, 397 (Recanto Jacarandá) | rico — centenas de registros (evidência dos lotes anteriores) | E2E principal |
| P2 | Segundo endereço do mesmo condomínio (nº vizinho) | médio — dezenas | idempotência |
| P3 | Endereço inexistente/sem registros | vazio | teste de falha graciosa |

## F0.6 — Runbook e relatório de créditos (D5/D7)

- Template de runbook por fonte: `agentes/eemovel/RUNBOOK.md` (Fluxo 1; replicar para Fisgar/Captei)
- Relatório de créditos: `agentes/comum/creditos.py::RelatorioCreditos` → `relatorio_creditos.json` por execução (ações pagas, custo, operador, aprovação)

## Resultado do F0

| Item | Status |
|------|--------|
| R1 CLI | ✅ |
| R2 credenciais | ⏳ operador |
| R3 saldo | ⏳ operador |
| R4 stack | ✅ |
| R5 seletores | ⏳ calibração live (Fluxo 1, etapa 1.1) |
| R6 pilotos | ✅ |
| R7 guard-rail | ✅ (`--max-consultas` + creditos.py; aprovacao.json obrigatória no Captei/Fluxo 3) |
| R8 custos | ⏳ sondagem (F0.3) |
