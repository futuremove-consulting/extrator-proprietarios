# Plano Completo de Testes Reais — Validação de Ponta a Ponta

**Projeto:** extrator-proprietarios
**Data:** 04/09/2026
**Versão:** 1.0
**Objetivo:** validar ABSOLUTAMENTE TUDO — custos reais, sessões, extração, matching, cascata, validação de WhatsApp, consolidação, retomada e auditoria — com orçamento controlado, guard-rails e gates de Go/No-Go, ANTES de executar o lote real completo (Rua Marc Chagall, 397).

---

## 1. Princípios do plano (inegociáveis)

1. **Barato antes de caro:** nenhuma etapa paga roda antes da etapa gratuita/gratuita equivalente passar.
2. **Piloto antes de produção:** o lote real só executa depois de um piloto limitado (máx. 10 fichas) passar em todos os gates.
3. **Nada é pago sem aprovação registrada:** arquivo "aprovacao.json" com {aprovado, por, escopo} — sem ele o serviço bloqueia (exit 2) e registra a tentativa.
4. **Evidência de tudo:** toda medição entra em "sondagem/" (NDJSON); toda consulta paga entra no log do lote com saldo antes/depois.
5. **Números da própria equipe** para calibração de ferramentas externas (Dono do Zap); **leads reais** apenas nas fases de piloto do fluxo (3+), dentro do orçamento.
6. **Credenciais nunca são armazenadas:** login manual do usuário nos navegadores; o agente só opera depois da sessão aberta.
7. **Backup antes de gravar:** planilhas do Drive exportadas antes de qualquer publicação.

## 2. Papéis

| Papel | Quem | Responsabilidade |
|---|---|---|
| Operador de navegador | Leonardo (você) | Login/MFA nos 3 sistemas; leitura de saldos/contadores na tela; cliques de consulta e confirmações; execução das sondas manuais do Dono do Zap |
| Agente | Este sistema | CLIs, cálculo de deltas, vereditos, manifests, matching, consolidação, relatórios, auditoria e bloqueios de guard-rail |
| Aprovador | Leonardo | Assinar "aprovacao.json" antes de cada lote pago |

## 3. Orçamento total do plano (teto, conservador)

| Recurso | Teto do plano | Saldo atual | Folga |
|---|---|---|---|
| Capcoins (Captei) | 9 | 77 | ✅ |
| Consultas Fisgar | 6 | 250/mês | ✅ |
| Consultas EEmovel | 6 | 500/mês | ✅ |
| Listagens (1 crédito/sistema/busca) | 9 (3 por sistema) | dentro das cotas | ✅ |
| PIX Dono do Zap (testes de relatório completo) | R$ 10 (2 x ~R$ 5) | — | ✅ |

> Se qualquer fase estourar o teto: PARAR, registrar a divergência no sondador e reavaliar antes de continuar.

## 4. Fases, gates e roteiro de execução

### FASE 0 — Pré-voo (custo: R$ 0) — Dia 1

Checklist (tudo precisa estar ✅ antes da Fase 1):

- [ ] "git pull" limpo; "py_compile" de todos os módulos OK
- [ ] As 3 suítes de teste automatizadas verdes: teste_matching_revisao.py, teste_sondar_cotas.py, teste_sondar_donozap.py
- [ ] Sessão Captei aberta e autenticada (saldo visível na tela: anotar)
- [ ] Sessão Fisgar aberta e autenticada — **GATE CRÍTICO:** executar 1 busca de teste e conferir que a tabela RETORNA DADOS (histórico de 401/GetPeople); se tabela vazia, PARAR e resolver sessão
- [ ] Sessão EEmovel aberta e autenticada (contador de consultas visível: anotar)
- [ ] Contadores iniciais anotados (capcoins; consultas usadas Fisgar/EEmovel) — serão os "antes" das sondas
- [ ] Backup das planilhas do Drive exportado
- [ ] "aprovacao.json" criado: {"aprovado": true, "por": "Leonardo Cabral Ferreira", "escopo": "plano_testes_reais"}
- [ ] Lote-piloto definido: Rua Marc Chagall, 397 (endereço real conhecido: ~500 ocorrências, ~342 chaves, ~316 PF, 26 PJ)

**GATE 0:** todos os itens ✅. Senão, corrigir antes de prosseguir.

### FASE 1 — Sondas de custo REAIS (custo: ~6 créditos + 3 fichas) — Dia 1

Responde com evidência P1–P4 do "sondar_cotas.py" (ver expectativa corrigida: listagem consome 1 crédito).

Roteiro (por sistema, na ordem eemovel → fisgar → captei):

    # ANTES de buscar: anote saldo/contador da tela
    python3 sondar_cotas.py medir --pergunta P1 --sistema <sys> --evento busca_listagem         --tipo-saldo <capcoins|consultas> --saldo-antes A --saldo-depois B         --contador-antes C --contador-depois D
    # (faça a busca do endereço NA UI agora)
    # DEPOIS da busca: anote novamente e rode o comando com os valores reais

    # abra 1 ficha/consulta real e meça o delta por consulta:
    python3 sondar_cotas.py medir --pergunta P2 --sistema captei --evento consulta_detalhe         --tipo-saldo capcoins --saldo-antes X --saldo-depois Y         --contador-antes C --contador-depois D --pago --aprovacao aprovacao.json

Critérios de aceite (GATE 1):

- [ ] Custo real da LISTAGEM medido nos 3 sistemas (esperado: 1 crédito — validar)
- [ ] Custo real da FICHA medido nos 3 sistemas (esperado: 1 por consulta)
- [ ] Modalidade Captei esclarecida empiricamente (capcoins pré-pago x cota mensal)
- [ ] Deltas batem com os saldos exibidos na tela (0 divergências)
- [ ] "sondar_cotas.py aplicar" gerou "custos_verificados.json" sem pendências

### FASE 2 — Sonda Dono do Zap com AMBOS os domínios (custo: R$ 0 + até R$ 10 de PIX) — Dia 1

Com 2–3 números da própria equipe (rótulos mascarados):

    python3 sondar_donozap.py iniciar --lote sondagem_real --operador leonardo
    python3 sondar_donozap.py medir --dominio com --numero-sufixo "****XXXX"         --nome-publico "<nome retornado>" --foto-gratis false --pix-oferecido true         --pix-valor <valor> --tempo-segundos <t> --sigilo ui_afirma
    python3 sondar_donozap.py medir --dominio com_br --numero-sufixo "****XXXX" ... (idem)
    # calibrar a regra central com GROUND TRUTH (nós sabemos o nome real do dono):
    python3 sondar_donozap.py comparar --nome-proprietario "<nome real>"         --nome-publico "<nome retornado>" --registrar
    python3 sondar_donozap.py veredito
    python3 sondar_donozap.py aplicar

Critérios de aceite (GATE 2):

- [ ] Retorno gratuito medido nos 2 domínios (nome público: sim/não; foto: grátis/paga)
- [ ] Preço do desbloqueio PIX observado e registrado (se testado)
- [ ] Sigilo validado com o dono do número da equipe (nada apareceu no WhatsApp dele)
- [ ] Pelo menos 3 comparações de nome registradas, incluindo 1 caso verdadeiro (score medido)
- [ ] Limiares 0.92/0.75 confirmados OU ajustados com justificativa documentada
- [ ] "validacao_whatsapp_config.json" gerado com domínio recomendado

### FASE 3 — Piloto de LISTAGEM no endereço real (custo: 3 créditos) — Dia 2

    python3 extrair_orquestrado.py --endereco "Rua Marc Chagall, 397 - Água Branca, São Paulo - SP"         --sistemas eemovel fisgar captei --dados-dir piloto/dados --manifests-dir piloto         --apenas-inventario --log-dir piloto/logs

Critérios de aceite (GATE 3):

- [ ] Total exibido na UI == total no manifest (por sistema; divergência = PARAR e reconciliar)
- [ ] Paginação/scroll 100% varridos (sem "fim não confirmado")
- [ ] PF x PJ classificados (referência auditada: ~316 PF / ~26 PJ no Captei)
- [ ] Possíveis moradores separados dos proprietários (listas distintas)
- [ ] Listas originais salvas por sistema (RAW) + lista mestra consolidada (sem contato)
- [ ] Chaves deduplicadas sem duplicidade (validação de chaves)
- [ ] Custo real de listagem confere com a Fase 1

### FASE 4 — Piloto de CASCATA limitada (custo: máx. 10 fichas) — Dia 2

Seleção ESTRATÉGICA de 5–6 proprietários (amostra proposital de casos):

1. 2 presentes nas 3 fontes (valida overlap e a ordem EEmovel → Fisgar → Captei)
2. 1 presente só no Captei (valida lacuna → gasto de capcoin)
3. 1 homônimo (mesmo nome, unidades diferentes) — valida banda de revisão
4. 1 PJ (empresa) — valida EXCLUSÃO sem gasto
5. 1 sem contatos em nenhuma fonte — valida exceção e flag de qualidade

    python3 extrair_orquestrado.py --endereco "..." --sistemas eemovel fisgar captei         --dados-dir piloto/dados --manifests-dir piloto --limite 10 --log-dir piloto/logs

Critérios de aceite (GATE 4):

- [ ] ZERO compra duplicada (o matching impediu reabrir quem já foi coberto)
- [ ] Custo real por ficha == custo medido na Fase 1 (log com saldo antes/depois)
- [ ] PJ consultada ZERO vezes (excluída antes do gasto)
- [ ] Campos prioritários cobertos: telefone (EEmovel/Captei), CPF quando aparecer (Fisgar/EEmovel), e-mail
- [ ] CPF completo extraído e salvo quando disponível (flag no registro)
- [ ] Cada ficha paga tem aprovação registrada e evidência no log
- [ ] 1 interrupção proposital no meio de uma ficha + RETOMADA sem recompra e sem duplicação (Fase 7 parcial)

### FASE 5 — Validação de WhatsApp REAL (custo: R$ 0 + máx. 3 capcoins) — Dia 3

1. Gerar a fila CSV operável dos telefones do piloto (record_key, nome, unidade, telefone, sufixo mascarado)
2. Operador consulta cada número no domínio vencedor da Fase 2 e preenche a coluna "nome_publico_retornado"
3. Importar e aplicar a regra central:

    python3 sondar_donozap.py comparar --nome-proprietario "..." --nome-publico "..." --registrar

4. Captei "Validar Whatsapp" SOMENTE nos "ambiguo_revisao" de leads prioritários (máx. 3 capcoins)

Critérios de aceite (GATE 5):

- [ ] Taxa de validação gratuita medida (meta: >= 60% dos telefones com nome público)
- [ ] Distribuição de scores registrada (>= 0.92 / banda / < 0.75)
- [ ] Economia de capcoins medida (fichas que NÃO precisaram de Captei)
- [ ] Amostra da banda de revisão revisada por humano (decisões registradas)
- [ ] Zero disparo/envio de mensagem (apenas validação — Copiloto fora do escopo deste plano)

### FASE 6 — Consolidação, reconciliação e auditoria (custo: R$ 0) — Dia 3

    python3 consolidar_multi_origem.py --lote piloto --manifests-dir piloto

Critérios de aceite (GATE 6):

- [ ] Golden Records gerados com proveniência por campo (origem de cada dado)
- [ ] Equação de reconciliação fecha 100% (manifest_total = concluidos + empresas + falhas + revisão)
- [ ] Zero perda de dados (todos os SourceRecords preservados)
- [ ] Relatórios de reconciliação e golden_records salvos
- [ ] Pares da banda de revisão resolvidos (aceito/rejeitado via revisar_pares)

### FASE 7 — Robustez (custo: R$ 0) — Dia 3

- [ ] Retomada pós-interrupção (da Fase 4) validada: checkpoint respeitado, zero recompra, zero duplicação
- [ ] Simulação de sessão expirada: tela de login detectada → agente PARA e pede login (não tenta nada)
- [ ] Simulação de modal divergente: cancelar, registrar "wrong_modal_prevented", seguir
- [ ] Divergência de saldo intencional (anotar valor errado no sondador) → veredito marca irregular
- [ ] Guard-rail provado: 1 tentativa paga sem aprovação → bloqueada (exit 2) com evidência

### FASE 8 — Go/No-Go para o LOTE REAL completo — Dia 4

**GO exige TODOS os gates anteriores ✅ + este checklist:**

- [ ] Custos VERIFICADOS (não estimados) consolidados em custos_verificados.json
- [ ] Orçamento do lote real aprovado por escrito (lista mestra x cotas: ~378 consultas estimadas)
- [ ] Capcoins suficientes para as exceções (ou decisão de rodar sem exceções e revisar depois)
- [ ] Plano de execução em lotes diários (ex.: 50–80 fichas/dia com checkpoint a cada ficha)
- [ ] Fenômenos conhecidos mapeados (nomes mascarados, virtualização, homônimos)
- [ ] Papéis e horários definidos (operador disponível para as confirmações)

Execução do lote real: ciclo por ficha — localizar linha por chave → confirmar identidade → consultar (com aprovação do lote) → ler detalhes/telefones/e-mails → Validar WhatsApp (se regra mandar) → salvar → checkpoint → publicar. Qualquer divergência: PARAR, reconciliar, retomar pela chave.

## 5. Matriz de riscos e mitigação

| # | Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| 1 | Sessão Fisgar 401/tabela vazia | Média | Alto | Gate 0: prova de sessão com busca real antes de qualquer gasto |
| 2 | Listagem incompleta (paginação/scroll) | Média | Alto | GATE 3 exige contagem UI == manifest e fim confirmado |
| 3 | Compra duplicada (matching falhou) | Baixa | Médio | GATE 4: zero duplicata; banda de revisão para casos duvidosos |
| 4 | Dono do Zap sem API/antibot | Alta | Médio | Fase 2 manual assistido; automação só após ToS revisados (Fase 3 do projeto) |
| 5 | Capcoins insuficientes para exceções | Média | Médio | Orçamento reservado; fila de prioridade por score; plano segue sem exceções se necessário |
| 6 | Conflito multi-agente em arquivo | Média | Médio | Coordenar módulos por agente; re-verificar arquivo antes de patch; commits atômicos |
| 7 | Nome público com iniciais/apelidos | Alta | Baixo | Banda de revisão + foto paga opcional para prioritários |
| 8 | Divergência de saldo/contador na UI | Baixa | Médio | Sondador marca "irregular"; PARAR e reconciliar |

## 6. Critérios globais de sucesso (Definition of Done do plano)

- [ ] P1–P4 respondidas com evidência real (custos verificados, não estimados)
- [ ] Dono do Zap validado nos 2 domínios com regra central calibrada (ground truth da equipe)
- [ ] Piloto de ponta a ponta aprovado nos GATES 3–6
- [ ] Retomada pós-interrupção validada (F7)
- [ ] Guard-rail validado com tentativa negativa real
- [ ] Taxa de validação gratuita de WhatsApp medida (meta >= 60%) e economia de capcoins documentada
- [ ] Reconciliação 100% no piloto
- [ ] Go/No-Go assinado para o lote real

## 7. Artefatos gerados pelo plano

- "sondagem/": sessao, medicoes, vereditos, custos_verificados (sondar_cotas)
- "sondagem/": donozap_sessao, donozap_medicoes, donozap_comparacoes, donozap_vereditos, validacao_whatsapp_config (sonda Dono do Zap)
- "piloto/": manifests RAW por sistema, lista mestra consolidada, logs de processo, golden records, relatórios de reconciliação
- Fila CSV de validação WhatsApp (formato: record_key; nome; unidade; telefone; sufixo_mascarado; nome_publico_retornado; score; decisao)
- "aprovacao.json" (por lote pago) e logs de bloqueios (evidências)

## 8. O que este plano NÃO faz

- Não automatiza o navegador (Playwright fica para depois da revisão de ToS — Fase 3 do projeto Dono do Zap)
- Não envia mensagens/disparos (Copiloto fora do escopo; apenas validação)
- Não enriquece possíveis moradores com créditos (só registra da listagem)
- Não usa leads reais em ferramentas externas antes da calibração (Fase 2 usa números da equipe)
- Não publica na planilha do Drive sem backup prévio (F0)

## 9. Roteiro sugerido de dias

| Dia | Fases | Custo estimado |
|---|---|---|
| Dia 1 | F0 + F1 + F2 | ~6 créditos mistos + até R$ 10 PIX |
| Dia 2 | F3 + F4 | 3 listagens + até 10 fichas |
| Dia 3 | F5 + F6 + F7 | máx. 3 capcoins + R$ 0 |
| Dia 4 | F8 (Go/No-Go) | R$ 0 |
| Dia 5+ | Lote real em lotes diários | conforme orçamento aprovado |
