# Validacao de WhatsApp via Dono do Zap — Analise e Plano

**Projeto:** extrator-proprietarios
**Data da analise:** 04/09/2026
**Status:** Fase 1 (sonda) aprovada; decisoes registradas na secao 9
**Regra central do usuario:** comparar se o **nome publico de exibicao daquele WhatsApp** bate com o **nome do proprietario** em questao.

---

## 1. Contexto e objetivo

- Telefones extraidos de EEmovel e Fisgar entram no pipeline como "nao_validado".
- A validacao de WhatsApp no Captei custa Capcoins — recurso pre-pago e escasso (saldo atual: 77; pacote de 50 por R$ 49,90).
- Objetivo: validar o WhatsApp dos proprietarios com **melhor qualidade, consistencia e custo**, usando o **nome de exibicao publico** do WhatsApp como evidencia de identidade, e reduzir o gasto de Capcoins a casos de excecao.

## 2. As duas ferramentas (sao produtos diferentes)

| Aspecto | donodozap.com.br | donodozap.com |
|---|---|---|
| Posicionamento | Consulta de numero WhatsApp para seguranca/anti-golpe | Descobridor de dono global; "+2 milhoes de pesquisas"; conta opcional |
| Fluxo | 4 passos: digita numero -> analise em segundos -> resultado -> liberacao criptografada | +55 + numero -> "Descobrir" |
| Custo | "Iniciar consulta gratuita" + pagamento para resultado completo | "A pesquisa inicial pelo nome associado ao numero e GRATUITA. O relatorio completo (foto de perfil, dados adicionais) pode exigir o desbloqueio via PIX" |
| Retorno | "Informacoes disponiveis" sobre o dono | Nome de exibicao publico do WhatsApp (gratis) + foto de perfil (pago) |
| Fonte de dados | "Informacoes publicas" | "Motor de busca que indexa informacoes ja disponiveis publicamente na internet (fontes abertas, OSINT), como o nome de exibicao e a foto de perfil publicos do WhatsApp... Nao acessamos conteudo de conversas" |
| Sigilo | FAQ: "A pessoa sabera que consultei?" (resposta nao acessivel) | "A consulta e feita de forma anonima" |
| LGPD | Footer: "conformidade com a LGPD"; "As consultas devem respeitar a legislacao vigente e a privacidade dos usuarios" | "A ferramenta apenas organiza e exibe informacoes que ja estao publicas... O uso que voce faz dos resultados e de sua responsabilidade" |
| API | Nenhuma mencao | Nenhuma mencao |

## 3. Limitacoes de acesso (descoberta por HTTP)

- Ambos sao SPA: paginas internas (FAQ completa, termos, precos) retornam 404 via HTTP estatico; buscadores bloquearam a varredura.
- **Sem API documentada** em nenhuma home.
- O preco do desbloqueio PIX aparece **somente dentro do fluxo de consulta** -> medir empiricamente na Fase 1 (com numeros da propria equipe).

## 4. Insight estrategico

O dado que falta aos telefones brutos da cascata e exatamente o que o Dono do Zap oferece **de graca**: o **nome de exibicao publico** do WhatsApp. E o motor de comparacao de nomes ja existe no projeto ("agentes/comum/matching_revisao.py::similaridade_nomes", banda auto_merge >= 0.92 / revisao 0.75-0.92, tolerante a abreviatura e conectores).

## 5. Nova camada de validacao (antes de gastar Capcoin)

    Telefone bruto (EEmovel/Fisgar, "nao_validado")
            |
            v
    [Dono do Zap — pesquisa inicial GRATUITA]  ->  nome publico de exibicao do WhatsApp
            |
            v
    similaridade_nomes(nome_do_proprietario, nome_publico_whatsapp)
            |-- score >= 0.92   -> "whatsapp_validado_publico"   (custo: R$ 0 — Capcoin poupado)
            |-- 0.75 a 0.92     -> "ambiguo_revisao"             (operador decide; foto paga opcional)
            |-- score < 0.75    -> "nao_correspondente"          (numero provavelmente nao e do proprietario)
                    \_ (opcional) Captei "Validar Whatsapp" so nos casos duvidosos

Cada telefone validado registra proveniencia: fonte (donodozap_gratis), score da comparacao, timestamp.

**Limitacao conhecida (documentada):** iniciais do nome do meio ("Paula E. Cunha" para Eleonora) caem na **banda de revisao** — o normalizador remove o conector "e"; o operador decide (ou usa a foto paga como evidencia). Comportamento conservador e intencional.

## 6. Impacto estimado

- Se 70–85% dos telefones tiverem nome publico casavel (padrao tipico no Brasil), a reducao de Capcoins e proporcional — **77 capcoins passam a cobrir 5–10x mais leads**.
- O Captei deixa de ser a rotina de validacao e vira **camada de excecao** (casos ambiguos e leads prioritarios).
- Qualidade sobe: nome publico + score + proveniencia por telefone (antes: apenas "nao_validado").

## 7. Riscos e mitigacao

| Risco | Mitigacao |
|---|---|
| ToS: sem API documentada; termos nao acessiveis por HTTP | Fase 1 **manual assistido** (sem scraping/automacao); automacao (Fase 3) somente apos revisao manual dos ToS, decisao documentada |
| Falsos positivos (apelidos: Ze x Jose) | Banda de revisao; foto paga como evidencia opcional para leads prioritarios |
| LGPD | Dados publicos (nome de exibicao); finalidade = verificacao de identidade do lead; proveniencia e finalidade registradas; sem revenda; opt-out respeitado nos disparos (Copiloto) |
| Antibot/limites de uso | Uso manual assistido, volumes normais, pausas entre consultas |
| Dois dominios possiveis | Sonda testa AMBOS (decisao do usuario) e o veredito recomenda qual usar no dia a dia |

## 8. Plano em 3 fases

**Fase 1 — Sonda (descoberta empirica, ~30–45 min, manual):**

- Servico: "agentes/sondar_donozap.py" + "agentes/teste_sondar_donozap.py".
- Protocolo com **numeros da propria equipe** (nunca leads reais): medir em cada dominio (.com e .com.br) o que a pesquisa gratuita retorna (nome publico? foto?), valor do desbloqueio PIX, tempo, sigilo declarado, limites/antibot.
- Saidas: "sondagem/donozap_medicoes.ndjson", "sondagem/donozap_vereditos.json", "sondagem/validacao_whatsapp_config.json".

**Fase 2 — Integracao na cascata (validacao gratuita em escala):**

- Modulo "comum/validacao_whatsapp.py" com "validar_por_nome_publico(nome_proprietario, nome_publico_wa)" (usa "similaridade_nomes").
- Etapa 4 do orquestrador: gerar **fila CSV operavel** de telefones "nao_validado" -> operador consulta no Dono do Zap -> importar resultados -> aplicar matching -> fila residual de Capcoins cai ao minimo.
- Reuso do "comum/process_logger.py" para auditoria.

**Fase 3 — condicional:** automacao Playwright **somente se** os ToS permitirem automacao (decisao documentada apos Fase 1).

## 9. Decisoes registradas (04/09/2026)

- (a) **Dominio: testar AMBOS** (.com e .com.br).
- (b) **Escopo: validacao por nome publico para TODOS os leads** (nao so prioritarios).
- (c) **Sonda com numeros da propria equipe** (nunca leads reais).
- Regra central: comparar se o **nome publico de exibicao** daquele WhatsApp bate com o **nome do proprietario** em questao (via "similaridade_nomes", banda 0.92/0.75).

## 10. Rastreabilidade

- Fontes: https://donodozap.com.br/ e https://donodozap.com/ (acesso em 04/09/2026).
- Paginas internas 404 (SPA); sem preco publico do PIX em buscadores (Bing generico; DuckDuckGo com captcha).
- Referencias internas: "ESTRATEGIA_EXTRACAO_CASCATA.md" (Secao 8 — Sondador de Cotas), "agentes/comum/matching_revisao.py", "agentes/comum/process_logger.py".
