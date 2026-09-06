# Memory Index — extrator-proprietarios

*One line per fact. Format: `- [slug](slug.md) — description`*

- [cascade-extraction-order](cascade-extraction-order.md) — EEmovel (R$0.81) → Fisgar (R$1.03) → Captei (R$1.57) per consulta; Stage 1 inventory costs 1 crédito/listagem
- [parse-unidade-split](parse-unidade-split.md) — Unidade parseada em `unidade_imovel` (AP 101) + `unidade_vaga` (VG 3M TER) + `tipo_unidade` (apartamento/cobertura/garden/sala/loja/vaga); record_key v2 usa componentes separados
- [donodozap-br-works](donodozap-br-works.md) — donodozap.com.br funciona com agent-browser: FREE retorna nome mascarado + nascimento/CPF parciais; PAID (PIX ~R$0,50) desbloqueia nome, CPF, RG, endereços, emails, telefones, parentes, empresas
- [donodozap-com-blocked](donodozap-com-blocked.md) — donodozap.com bloqueia headless browser ("Não foi possível validar sua conexão segura"); não usar como fallback automatizado
- [whatsapp-validation-stage](whatsapp-validation-stage.md) — Stage 2.5 no pipeline: após consolidação, valida telefones únicos via donodozap.com.br; policy: max R$0,60/telefone, cache 7 dias, prefere PAID
- [three-source-identity](three-source-identity.md) — Identity resolution cascata: 1) CPF (forte), 2) nome|unidade, 3) +email, 4) +telefone; intra-source dedup ANTES do cross-source merge; moradores ≠ proprietários (listas separadas desde Stage 1)
- [eEmovel-moradores](eEmovel-moradores.md) — EEmovel retorna "Possível morador" + "Proprietário" na mesma listagem; classificar por `tipo_pessoa` e salvar em listas distintas; não dedupar morador com proprietário
- [fisgar-volumes](fisgar-volumes.md) — Fisgar: 250 consultas/mês (Plano Plus R$3.084/ano); EEmovel: 500/mês (Pro R$4.846/ano); Captei: ~200/mês (Light R$3.772 + capcoins)
- [agent-browser-over-playwright](agent-browser-over-playwright.md) — Usar agent-browser (Vercel MCP) para WhatsApp validation; não Playwright (não instalado); agent-browser já configurado no ambiente
- [pilotcrm-integration-points](pilotcrm-integration-points.md) — PilotCRM Delta A: crm_contacts + person_role_property substituem crm_owners*; crm_property_sources já suporta origem fisgar/captei/eemovel; extractor vira módulo/serviço no monorepo pnpm
- [consolidation-pipeline-8-stages](consolidation-pipeline-8-stages.md) — Pipeline: load → normalize → sanitize(LGPD) → dedup(intra+cross) → merge(políticas por campo) → validate(cross-source) → score(confiança) → output(golden_records JSON + MD)
- [process-learning-logger](process-learning-logger.md) — ProcessLearningLogger: NDJSON estruturado + relatório Markdown auto; logs: stages, decisions, actions, costs, extraction results; gera learning report ao final
- [process-learning-evaluator](process-learning-evaluator.md) — Módulo de aprendizado contínuo: avalia se fluxo/ordem atual é ótimo (eficácia, eficiência, custo-benefício) baseando-se em logs reais; recomenda ajustes dinâmicos (ordem condicional, fallback, cache)