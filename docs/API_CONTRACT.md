# API Contract — extrator-proprietarios (v0.1.0)

Serviço HTTP autônomo (**produto independente**) consumido pelo PilotCRM e
operado standalone via `extrator-api`.

## Serviço

- Entry-point: `extrator-api` (CLI Click — `python -m extrator_prop.api.cli`)
- Framework: Flask · Porta padrão: 8000
- Instalação: `pip install -e ".[dev]"`

### GET /healthz

Probe de vida usada pelo load balancer / CI.

```http
GET /healthz
```

```json
{"status": "ok", "timestamp": <epoch>}
```

### POST /api/v1/extract

Extrai proprietários de um endereço, orquestrando todos os agentes ativos
(`CapteiAgent`, `EEmovelAgent`, `FisgarAgent`) e devolvendo tanto o contrato
**canôônico** (extrator) quanto o **compatível com PilotCRM**.

**Request**

```http
POST /api/v1/extract
Content-Type: application/json

{
  "address": "Av. Paulista, 1000 — São Paulo",
  "tipo_documento": "proprietario"
}
```

| Campo | Tipo | Obrig. | Descrição |
|-------|------|--------|-----------|
| `address` | string | sim | Consulta de captação. |
| `tipo_documento` | string | não | `proprietario`; futuramente `morador` |

**Responses**

`200 OK`

```json
{
  "address": "...",
  "tipo_documento": "proprietario",
  "resultados": [ <CanonicalContact.to_dict()> ],
  "items": [ <ExtractedOwner> ],
  "stats": { "total": 0, "pending": 0, "completed": 0, "excluded": 0, "errors": 0, "duration_seconds": 0.0 }
}
```

`400 Bad Request` — `address`/`query` vazio.
`502 Bad Gateway` — falha de extração (upstream inacessível / sem credenciais).

---

## Bridge PilotCRM ↔ Extrator (Sprint #5)

`items` segue o schema `ExtractedOwner` definido em
`pilotcrm/apps/pilotcrm/src/modules/captacao/types.ts` e consumido por
`CaptacaoForm.tsx` (`(data.items ?? []).map(...)`).

### Mapeamento de campos

| `CanonicalContact.to_dict()` | → `ExtractedOwner` | Regra |
|------------------------------|--------------------|-------|
| `name` | `fullName` | |
| `source` | `source` | só `captei`/`eemovel`/`fisgar`; *fallback* → `captei` |
| `cpf` | `cpf` | string formatada |
| `phones[0].number` | `phone` | |
| `emails[0].email` | `email` | |
| `address.street` | `street` | |
| `address.number` | `number` | |
| `address.complement` | `complement` | |
| `address.neighborhood` | `neighborhood` | |
| `address.city` | `city` | |
| `address.state` | `state` | |
| `address.postal_code` | `cep` | |
| `entity_type` + `confidence` | `classification` | ver tabela abaixo |
| `confidence` (alta/média/baixa) | `confidence` (0..1) | `0.9` / `0.6` / `0.3` |
| `phones[0]` (donodozap/is_valid) | `whatsappValidation` | ver tabela abaixo |
| `source_id` | `raw` | passthrough para auditoria |

### `classification` — `OwnerClassification`

Alinhado ao **DEMO** de `MockCaptureProvider` (`provider.ts`):

| `entity_type` | `confidence` | `classification` |
|---------------|--------------|------------------|
| `Pessoa Fisica` | `alta` | `proprietario` |
| `Pessoa Fisica` | `media` / `baixa` | `possivel_morador` |
| `Pessoa Juridica` | — | `empresa` |
| `Desconhecido` | — | `indefinido` |

### `whatsappValidation.status`

| Condição (`PhoneValidation`) | `status` |
|------------------------------|----------|
| sem phones | `sem_whatsapp` |
| `is_valid=True` **ou** `donodozap_com`/`donodozap_com_br=True` | `validado` |
| `is_valid=False` e donodozap falso | `nao_validado` |

Campos espelhados: `donodozap_com`, `donodozap_com_br`, `score_nome`, `source`.

---

## Rodando localmente

```bash
pip install -e ".[dev]"
extrator-api --port 8000
```

```bash
curl -X POST localhost:8000/api/v1/extract \
  -H 'Content-Type: application/json' \
  -d '{"address": "Av. Paulista, 1000, São Paulo"}' | python -m json.tool
```

---

## Sprint seguinte (Sprint #6 — pilotcrm)

`pilotcrm/apps/pilotcrm/src/app/api/crm/captacao/search/route.ts` deve
substituir `createCaptureProvider()` (Mock/Playwright) por um **proxy HTTP** para
`POST /api/v1/extract`:

1. Repostar payload `{source, query}` do PilotCRM para `{address, tipo_documento}`.
2. Mapear a resposta `{items, total}` de volta ao contrato PilotCRM (`CaptacaoResult`).
3. Garantir `source` do `items` respeite o `source` solicitado (filtrar ou
   orquestrar por agente no extrator).
