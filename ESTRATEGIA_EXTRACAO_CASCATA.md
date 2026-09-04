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
7. **Re-entrada na etapa 3 deve ser barata.** Se o lote for retomado noutro dia, a re-busca da listagem precisa ser gratuita; caso a plataforma expire resultados, revalidar antes de comprar.

## 6. Fluxo refinado em 5 etapas (recomendado)

| Etapa | Custo | O que acontece | Artefato salvo |
|---|---|---|---|
| 0 Setup | Zero | Sessões autenticadas; ler saldos/cotas (capcoins, consultas restantes); receber endereço | estado da sessão |
| 1 Varredura | Zero (a validar) | Busca por endereço nos 3; varredura integral; classificar PF/PJ e Proprietário/Possível morador | lista original por sistema (RAW) |
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
2. normalizador de unidade + fuzzy com banda de revisão na etapa 2.
3. modo cascata no consolidador: entrada incremental (base do dia 1, delta do sistema B, delta do C) sem retrabalho.
4. saídas separadas proprietarios x moradores (hoje o pipeline mescla no golden record).
5. registro de gasto: custo em créditos por consulta no manifest/log (auditoria de eficiência).

## 8. Perguntas abertas (bloqueiam a implementação)

1. A busca por endereço e a listagem são gratuitas nos 3 sistemas (crédito só no Consultar/detalhe)?
2. Captei: a cota real é o saldo de capcoins (77 hoje) ou renovação mensal? O plano Pro indica 500 consultas/mês — qual vale?
3. EEmovel: 1 consulta por proprietário na página de detalhe, ou 1 consulta cobre o perfil completo (e moradores vêm juntos)?
4. Fisgar: cada modal Consultar consome 1 das 250/mês?
5. [RESPONDIDA em 04/09/2026] Prioridade de negócio: o usuário decidiu ordenar por maior cota/menor custo primeiro, sem ponderação por campo. Ver seção 10.
6. Confirmado: possíveis moradores NÃO recebem gasto de crédito (só registro da listagem)?
7. Mantemos confirmação humana antes de cada lote de consultas pagas?

## 9. Próximo passo

Com as respostas das perguntas 1, 3 e 5, implementar nesta ordem: normalizador de unidade + banda de revisão (4.3), budget_planner (7.1) e modo cascata (7.3).

## 10. Decisão registrada: ordem da cascata (04/09/2026)

**Decisão do usuário:** maior cota/menor custo primeiro, tanto faz o campo. A ordenação passa a ser por eficiência econômica do crédito, não por prioridade de dado.

**Ordem resultante da cascata:**

| Ordem | Sistema | Justificativa econômica | Papel na cascata |
|---|---|---|---|
| 1º | EEmovel | Maior cota (500/mês) e contato completo (telefone + email) na página de detalhe, sem modal intermediário | Varredura principal: consultar a lista consolidada inteira de PF |
| 2º | Fisgar | Cota média (250/mês) | Complemento: apenas não-cobertos + campos deficientes (ex.: CPF/RG) |
| 3º | Captei | Crédito pré-pago escasso (77 capcoins) e reposição cara (50 por R$ 49,90) | Fechamento: lacunas residuais + validação WhatsApp dos leads prioritários |

**Custo estimado do lote-piloto (U = 320 PF):** EEmovel ~320 consultas (dentro da cota), Fisgar ~40-60 (delta + campos faltantes), Captei ~20-40 capcoins (lacunas + validação seletiva) — cabe no saldo atual de 77.

**Regra de exceção que permanece:** se um registro ficar sem contato após EEmovel + Fisgar, e for lead prioritário, o Captei cobre a lacuna; a validação WhatsApp não é automática — passa por fila de prioridade (score do lead).

**Perguntas ainda abertas (não bloqueiam o desenho, bloqueiam o budget_planner exato):** 1 (gratuidade da listagem), 2 (cota real do Captei), 3 (custo por registro no EEmovel), 4 (custo do modal no Fisgar), 6 (guard-rail humano).
