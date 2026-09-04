# Estratégia de Extração em Cascata Multi-Origem

**Projeto:** extrator-proprietarios
**Data:** 04/09/2026
**Status:** Proposta analisada; pendente validação de premissas (seção 8)

## 1. A Estratégia Proposta (resumo do usuário)

1. **Etapa 1:** agentes acessam os 3 sistemas e buscam pelo endereço inputado — valida se o sistema tem dados daquele endereço/condomínio (pode ter ou não ter).
2. **Etapa 2:** comparar as listas de proprietários de cada sistema (quantidade e dados), consolidar, salvar lista original por sistema + lista consolidada dos 3 — ainda SEM dados de contato.
3. **Etapa 3:** extrair dados de contato do sistema com maior número de proprietários na base; depois no outro sistema apenas dos proprietários que não estão no primeiro; e assim por diante até o 3º.

Premissas informadas:

- Captei e Fisgar não retornam telefone/email na listagem; EEmovel retorna na página de detalhe/perfil/contatos, sem modal intermediário de validação.
- Nenhum sistema é gratuito. Fisgar: Equipe Anual Plus R$ 3.084,00 por ano, 250 consultas/mês. Captei: Plano Imobiliária Light R$ 3.772,44 (adesão com 200 capcoins); saldo atual 77 capcoins; pacote avulso de 50 consultas por R$ 49,90; Plano Pro indica 500 consultas/mês (divergente, a confirmar). EEmovel: Plano Pro Anual com 500 consultas/mês (Basic 100, Enterprise 2000).
- Identidade: nome+unidade; depois nome+unidade+email e/ou nome+unidade+celular (e as combinações).
- Todos os sistemas podem trazer possível morador e possível proprietário; extrair da mesma forma, mas classificar e salvar em listas distintas.

## 2. Veredito

Faz sentido? **SIM.** É o padrão consolidar-antes-de-comprar (merge-before-fetch): toda a comparação e deduplicação acontece na camada gratuita (listagem) e o crédito só é gasto no preenchimento de lacunas. É inteligente e eficiente, com três correções obrigatórias (seção 4). Deixa de ser eficiente apenas se a deduplicação errar em qualquer direção: falso negativo paga consulta duplicada; falso positivo deixa de consultar quem tinha dado melhor.

## 3. Por que funciona — a matemática da economia

- Sobreposição medida no projeto (smoke test das 3 fontes): 4 grupos de identidade, 85 por cento casados por record_key exato. No lote Marc Chagall, Captei e Fisgar têm ~342 chaves únicas cada — bases quase espelhadas (mesma origem cadastral).
- Sem cascata: 3 x U consultas (U = PF únicas consolidadas). Com cascata: A(U) + B(U - S_AB) + C(só faltantes). Com U = 320 PF e sobreposição de 85 por cento: ~320 + ~48 + ~10 = ~378 consultas — economia de ~60 por cento.
- Com as cotas atuais (Captei 77 capcoins, Fisgar 250/mês, EEmovel 500/mês), a cascata é a única forma de cobrir um lote grande sem comprar pacotes: as cotas somam 827 consultas/mês, mas gastá-las integralmente nos mesmos proprietários é desperdício duplo (dinheiro + dado redundante).
- **CORREÇÃO (04/09): a listagem NÃO é gratuita** — consome 1 crédito por sistema. Custo fixo da descoberta no lote-piloto: +3 créditos. Continua sendo a compra mais barata do processo: 1 crédito revela centenas de nomes de uma vez e evita centenas de consultas duplicadas na cascata; e a lista fica salva (a retomada não repaga).

## 4. As três correções obrigatórias

### 4.1 Ordem por valor-por-crédito, não por contagem

O critério maior número de proprietários é incompleto. O correto é valor-por-crédito = (cobertura de campos prioritários x qualidade do dado) por consulta, respeitando o saldo disponível. Exemplo real: EEmovel entrega telefone e email na página de detalhe, sem modal, e com a maior cota (500/mês) — provável candidato a primeiro. Captei tem o diferencial de qualidade (WhatsApp validado), mas saldo escasso (77) e reposição cara (50 por R$ 49,90) — candidato a fechamento cirúrgico das lacunas e validação dos leads prioritários, não a varredura inicial.

### 4.2 Política por campo, não por registro

Consultar no 2º sistema apenas quem não está no 1º perde valor: o 2º sistema pode ter CPF ou email que o 1º não tem. Correção: no 2º sistema consultar (a) os não cobertos e (b) os cobertos com campo prioritário faltante ou de baixa qualidade. O projeto já tem políticas por campo (merge_policies: CPF prioritário Fisgar/EEmovel, WhatsApp prioritário Captei, SOURCE_PRIORITY_ORDER) — a cascata deve alimentar exatamente essas políticas.

### 4.3 Deduplicação com fuzzy e banda de revisão

A chave exata nome+unidade falha com abreviações (MARIA AP. DE SOUZA x MARIA Aparecida Souza), múltiplos proprietários na mesma unidade e variações de unidade (AP 22 E VG x APT 22 BL B). Correção: normalizador de unidade forte + fuzzy com limiar conservador (auto-merge em similaridade alta, ex. >= 0.92; banda 0.75-0.92 vai para revisão humana). Revisar um par custa segundos; uma consulta duplicada custa crédito real.

## 5. Alertas

1. **Moradores não recebem gasto de crédito.** Possível morador é classificado na listagem (grátis) e salvo em lista própria; nunca enriquecer via consulta paga, salvo hipótese forte de proprietário não registrado (flag para decisão humana).
2. **Excluir PJ antes de gastar.** O lote tem 26 empresas; a cascata só compra PF.
3. **Capcoins (pré-pago) x cotas mensais (usa-ou-perde) são recursos diferentes.** Esquentar primeiro o que é usa-ou-perde; reservar capcoins para lacunas e validação WhatsApp dos leads prioritários. Implementar budget planner que simule o custo da rodada contra os saldos antes de executar.
4. **Listagem incompleta quebra a dedup.** Paginação do Captei e scroll infinito do Fisgar precisam ser varridos integralmente antes da decisão; truncamento gera compra duplicada.
5. **Divergência entre fontes é sinal de qualidade, não ruído.** Telefone diferente entre sistemas = política de qualidade (validado x não validado, fonte mais recente), já coberta pelo scoring; divergência não justifica recompra automática.
6. **Guard-rail de conformidade.** Confirmação humana antes de cada lote pago (premissa de consulta sequencial aprovada) e atenção a ToS/LGPD — os contatos alimentarão disparos (Copiloto/WhatsApp), que exigem base legal e opt-out.
7. **Re-entrada na etapa 3: NÃO rebuscar endereço já inventariado.** A listagem é paga (1 crédito por sistema) e fica salva no manifest — retomar a partir da lista salva, sem nova busca; caso a plataforma expire resultados, revalidar antes de comprar.

## 6. Fluxo refinado em 5 etapas (recomendado)

| Etapa | Custo | O que acontece | Artefato salvo |
|---|---|---|---|
| 0 Setup | Zero | Sessões autenticadas; ler saldos/cotas (capcoins, consultas restantes); receber endereço | estado da sessão |
| 1 Varredura | 1 crédito por sistema (listagem paga — CORREÇÃO do usuário 04/09: a busca por endereço consome 1 crédito e retorna possíveis proprietários e possíveis moradores; fica salva no manifest — retomada não repaga) | Busca por endereço nos 3; varredura integral; classificar PF/PJ e Proprietário/Possível morador | lista original por sistema (RAW) |
| 2 Consolidação base | Zero | Normalizar unidade; dedup intra; consolidar inter (exata + fuzzy com banda); matriz de cobertura por campo; plano de compras com custo x saldos | lista_consolidada_base (sem contato) + plano_compras.json (aprovação humana) |
| 3 Cascata paga | Créditos | 1º sistema = maior valor/crédito com saldo; 2º e 3º = só não-cobertos + campos deficientes; log de gasto por consulta | contatos por registro + log de gastos |
| 4 Pós | Zero | Merge por campo; validação WhatsApp só no subconjunto prioritário; scoring; saídas separadas | lista_proprietarios_consolidada, lista_possiveis_moradores, golden records com proveniência |

## 7. Impacto no código atual

Já existe e serve de base:

- SourceRecord.tipo_pessoa (Proprietário / Possível morador) — classificação pedida pelo usuário.
- IdentityGroup com match_type (cpf_strong, record_key_exact, tel_name, fuzzy) — dedup em camadas.
- MERGE_POLICIES por campo + SOURCE_PRIORITY_ORDER — política por campo da correção 4.2.
- Scoring com completeness, cross_source_agreement e quality_tier — decide se vale recomprar campo deficiente.

Falta construir:

1. budget_planner: ler saldos/cotas, simular custo da rodada, emitir plano_compras.json para aprovação humana.
2. [IMPLEMENTADO 04/09/2026] comum/matching_revisao.py + CLI revisar_pares.py + teste_matching_revisao.py: unidade estrutural (número do imóvel domina — AP 10 x AP 20 nunca casa automático), nome por tokens com abreviatura (AP. = APARECIDA), banda auto_merge >= 0.92 / revisão 0.75–0.92, decisões humanas via JSON. Validado com 6 casos de teste e fluxo ponta a ponta com decisão humana.
3. modo cascata no consolidador: entrada incremental (base do dia 1, delta do sistema B, delta do C) sem retrabalho.
4. saídas separadas proprietarios x moradores (hoje o pipeline mescla no golden record).
5. registro de gasto: custo em créditos por consulta no manifest/log (auditoria de eficiência).

---

## 8. Sondador de Cotas — verificação empírica das perguntas abertas (04/09/2026)

Serviço: "agentes/sondar_cotas.py" + "agentes/teste_sondar_cotas.py". Transforma as 5 perguntas abertas em protocolo de medição antes/depois com veredito automático e guard-rail de aprovação humana.

| Pergunta | Evento medido | Veredito automático |
|---|---|---|
| P1 listagem gratuita? | saldo/contador antes e depois de buscar endereço SEM abrir consulta | gratuita x consome_credito |
| P2 Captei: capcoins ou cota mensal? | saldo capcoins + contador antes/depois de 1 consulta | pre_pago_capcoins x cota_mensal x hibrido |
| P3 EEmovel: perfil completo? | contador + moradores_inclusos no 1º detalhe | perfil_completo_1_consulta (custo 1) x moradores_consulta_separada (custo 2) |
| P4 Fisgar: modal = 1/250? | contador antes/depois de 1 modal | custo_por_modal 1 x 0 x irregular |
| P5 guard-rail | tentativa paga SEM aprovação DEVE ser bloqueada (exit 2) | ativo_e_validado x nao_testado |

Protocolo (~15 min por sistema):

    python3 sondar_cotas.py iniciar --lote mar_chagall --operador leonardo
    # P1 nos 3 sistemas (deltas devem ser 0)
    python3 sondar_cotas.py medir --pergunta P1 --sistema captei --evento busca_listagem --tipo-saldo capcoins --saldo-antes 77 --saldo-depois 77 --contador-antes 0 --contador-depois 0
    # P2/P3/P4: 1 consulta paga por sistema COM aprovação registrada
    python3 sondar_cotas.py medir --pergunta P2 --sistema captei --evento consulta_detalhe --tipo-saldo capcoins --saldo-antes 77 --saldo-depois 76 --contador-antes 3 --contador-depois 3 --pago --aprovacao aprovacao.json
    python3 sondar_cotas.py veredito
    python3 sondar_cotas.py aplicar   # gera custos_verificados.json: orquestrador usa custos VERIFICADOS, nao estimados

Guard-rail: todo evento "--pago" exige "--aprovacao arquivo.json" com {"aprovado": true, "por": "...", "escopo": "..."}; sem ele o evento é BLOQUEADO (exit 2) e a tentativa fica registrada em "medicoes.ndjson" como evidência de auditoria. Saídas em "agentes/sondagem/": sessao.json, medicoes.ndjson, vereditos.json, custos_verificados.json.

CPF: "comum/validators.py::extrair_cpf_texto" — quando o CPF completo aparecer (qualquer sistema, inclusive texto livre do modal), é extraído, validado por dígito verificador e vira chave forte (cpf_strong) no consolidador. Integração pendente no extrator do Captei enquanto o arquivo estiver em edição por outro agente (ver alerta de arquivo em disputa).

---

## 9. Camada de validacao de WhatsApp — Dono do Zap (04/09/2026)

Documento completo: **VALIDACAO_WHATSAPP_DONODOZAP.md** (analise das ferramentas donodozap.com.br e donodozap.com, decisoes e plano em 3 fases).

Resumo: o **nome de exibicao publico** do WhatsApp (gratis no donodozap, OSINT) e comparado ao nome do proprietario via "similaridade_nomes" (banda 0.92/0.75, do "comum/matching_revisao.py"). Validacao gratuita para **TODOS os leads**; o Captei "Validar Whatsapp" vira camada de excecao. Sonda da Fase 1 com numeros da propria equipe, em **ambos os dominios** (.com e .com.br), via "sondar_donozap.py" (padrao do Sondador de Cotas).

Decisoes do usuario (04/09/2026): testar ambos os dominios; validacao por nome publico para todos os leads; sonda com numeros da propria equipe. Regra central: comparar se o nome publico de exibicao daquele WhatsApp bate com o nome do proprietario em questao.
