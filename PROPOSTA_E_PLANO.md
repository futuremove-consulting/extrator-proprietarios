# Proposta, Plano e Análise Crítica - Extrator de Proprietários

**Projeto:** extrator-proprietarios
**Idioma:** Português brasileiro
**Data:** 03-04/09/2026
**Status:** Fase 1 implementada; extração real por navegador pendente

---

## 1. Proposta Original

### 1.1 Contexto

O usuário solicitou o desenvolvimento de **agentes/scripts de consulta e extração de dados de proprietários** para dois sistemas:

- **Captei** - consulta de proprietários (app.captei.com.br/lead/proprietario/buscar)
- **Fisgar** - painel de consulta de proprietários (painel.fisgar.com.br/proprietarios)

Ponto de partida: pasta do projeto, com pacotes de evidências e documentação de workstreams anteriores (skills, manifestos, checkpoints e bases sanitizadas).

### 1.2 Objetivo

Executar, somente com a sessão autenticada já disponível no navegador do usuário, a extração controlada de **proprietários pessoa física** nos sistemas Captei e Fisgar, preservando a fonte RAW, criando manifest append-only, deduplicando por chave composta e registrando cada transição de estado.

### 1.3 Premissas (traduzido das skills)

| Premissa | Descrição |
|---|---|
| Autenticação | Só sessão autenticada; nunca receber senha, MFA, cookie ou token |
| Escopo | Pessoa física; empresas classificadas e excluídas |
| Cobrança | Não contornar paywall/capcoins; aprovação por consulta sequencial |
| Completude | Mapear listas paginadas/virtualizadas inteiras antes de enriquecer |
| Qualidade | Separar camadas RAW, sanitizada, persistida e pendente |
| Deduplicação | Chave composta (nome + unidade + endereço) |
| LGPD | Nascimento, celular e e-mail são dados pessoais |
### 1.4 Plano Inicial Detalhado (traduzido da proposta)

**Para o Captei:**

1. Script de automação para consulta por endereço com autocomplete (campo enderecoCompletoAux).
2. Navegação da tabela paginada (10, 25, 50 ou 100 registros por página), mapeando todas as páginas antes de enriquecer.
3. Abertura do modal modalDadosProprietarios com abas Imóvel, Proprietário, Telefones e E-mails.
4. Ação opcional de Validar Whatsapp para marcar a qualidade do telefone.
5. Sistema de checkpoints e retomada por lote; cada consulta custa 1 Capcoin, portanto consulta sequencial aprovada.
6. Deduplicação por chave composta; classificação PF x PJ (empresas classificadas e excluídas).
7. Saídas em JSON e Markdown; manifest append-only e log de transições de estado.

**Para o Fisgar:**

1. Automação da consulta por endereço em dois passos (Buscar + Confirmar Busca).
2. Leitura da tabela virtualizada (container owners-table com scroll infinito), varrendo todas as linhas MuiTableRow.
3. Abertura do modal com abas Detalhes, Telefones e Emails para cada proprietário pendente.
4. Geração de base por endereço, pronta para planilhas (Google Sheets).

**Arquitetura comum proposta:**

- Lote por endereço; manifest append-only; checkpoints por registro; log JSONL de transições.
- Estados: resultado_persistido, pendente_modal, pendente_validacao, empresa_excluida.
- Reconciliação final por lote; camadas RAW, sanitizada, persistida e pendente separadas.

## 2. O Que Foi Executado (estado atual do projeto)

**Commit:** fdaf371 - implementação completa Fase 1 - Consolidação Multi-Origem.

| Componente | Estado |
|---|---|
| 3 agentes (captei, fisgar, eemovel) | Operativos como processadores offline de JSON (flag apenas-inventario) |
| 4 CLIs (3 extratores + consolidador) | Compilam e respondem ao --help |
| Módulos comuns (identity_resolution, merge_policies, scoring, validators, consolidation) | Pipeline de 8 stages: load, normalize, sanitize, deduplicate, merge, validate, score, output |
| consolidar_multi_origem.py | Roda ponta a ponta |
| benchmark_cross_origem | Documentado, com fuzzy matching |

**Validações executadas em sessão:**

1. py_compile de todos os módulos: OK.
2. --help dos 4 CLIs: respostas corretas.
3. Smoke test de extração (apenas-inventario) nas 3 fontes: detecta 5 registros (4 PF + 1 PJ).
4. Consolidação multi-origem com as 3 fontes: 4 grupos de identidade (record_key_exact a 85 por cento) e 27 Golden Records a partir de 31 source records.

**Documentação atualizada:** README da raiz, agentes/README.md e DOCUMENTACAO_TECNICA.md (EEmovel marcado como implementado; DoD com status realista).

## 3. Análise Crítica: Proposta Inicial x Execução

| Dimensão | Proposta inicial | O que foi executado | Avaliação |
|---|---|---|---|
| Fontes | Captei + Fisgar | Captei + Fisgar + EEmovel | Ampliação positiva |
| Automação de navegador | Agente com sessão autenticada (DOM, modais, Validar Whatsapp) | Processadores offline de JSON; navegador adiado para a Fase 4 | Lacuna crítica |
| Dados | Lote real (Rua Marc Chagall, 397: 500 ocorrências, 342 chaves) | Fixtures sintéticos (teste_*) | Pendência de calibração |
| Arquitetura | Extração por lote + manifest + checkpoints | Extração + consolidação multi-origem com identity resolution e Golden Record | Evolução positiva |
| Métricas DoD | Confiança média > 85; revisão manual < 10 por cento | Confiança ~56; revisão ~100 por cento (dados sintéticos) | DoD não cumprida |
| Governança | Commit após validação | Commit de Fase 1 completa antes da calibração | Risco de leitura equivocada |

**Diferenças essenciais:**

1. O plano inicial era de extração; a execução construiu extração (offline) mais integração (consolidação). A peça mais valiosa, o Golden Record, não estava no escopo original.
2. O núcleo motivador do projeto, a extração autenticada no Captei e no Fisgar, segue manual: os CLIs exigem um JSON já extraído à mão, via flag --dados.
3. A ordem foi invertida: construiu-se o como (pipeline, scoring, merge) antes de garantir o quê (dados reais limpos e automação da coleta).

## 4. Alertas

1. **Rotulagem de status:** o commit sugere Fase 1 completa, mas o DoD exige dados de produção; há risco de alguém avançar para a Fase 2 (PilotCRM) com um pipeline não calibrado.
2. **Gargalo de negócio:** sem automação de navegador, cada lote depende de extração manual; o agent-browser falhou com erro 401 no diagnóstico original; recomenda-se Playwright.
3. **Rota de carga do lote real:** o loader busca teste_*/manifest; os dados reais estão em extracted/ com estrutura distinta; a Golden Record real ainda não foi produzida.
4. **Fluxo de trabalho frágil:** nesta sessão houve arquivos apagados e duplicados (heredocs partidos); o git salvou o trabalho; adotar commits atômicos frequentes.
5. **Constantes de domínio:** mismatch de acentos entre Pessoa Física e Pessoa Fisica alterou contagens de pendentes; falta enum centralizada.

## 5. Conclusão

A execução superou a proposta em arquitetura: passou de dois extratores para três extratores mais um motor de consolidação multi-origem, que é o desenho correto para o problema real (bases fragmentadas entre Captei, Fisgar e EEmovel). A camada de consolidação é hoje a mais sólida do projeto.

Por outro lado, a execução se adiantou à validação: o pipeline roda sobre fixtures sintéticos, as métricas de DoD não foram atingidas e a automação da extração, motivo de existência do projeto, permanece manual. O estado honesto do projeto é: pipeline implementado e validado apenas com dados sintéticos; extração autenticada e Golden Record real pendentes.

## 6. Recomendações Priorizadas

1. **Não encerrar a Fase 1.** Renomear o status para pipeline implementado, pendente calibração com dados de produção, e ajustar README e mensagem de commit.
2. **Antecipar a automação do navegador (Fase 4 para agora).** Playwright no Captei como piloto, reaproveitando a sessão autenticada do usuário, sem credenciais no código.
3. **Criar a rota de carga do lote real.** Adaptar o stage de carga para ler extracted/ (ou um manifest gerado do CSV consolidado de Marc Chagall) e produzir a primeira Golden Record real.
4. **Centralizar constantes de domínio** (por exemplo, ENTITY_PESSOA_FISICA) para eliminar o mismatch de acentos.
5. **Endurecer o fluxo de trabalho:** commits atômicos por módulo, com compilação e import testados antes de cada commit.
6. **Redefinir o DoD com metas mensuráveis no lote real** (ex.: confiança > 80 nas chaves de teste; revisão < 50 por cento no lote real).
7. **CI simples (GitHub Actions):** py_compile, smoke tests dos CLIs e execução do pipeline sobre fixtures, para que o estado completo seja verificado automaticamente.

## 7. Veredito

| Item | Veredito |
|---|---|
| Arquitetura de consolidação | Sólida; manter |
| Extração autenticada | Crítica; pendente (prioridade máxima junto com dados reais) |
| Status da Fase 1 | Reabrir como pendente de calibração |
| Próximo passo imediato | Rota de carga do lote Marc Chagall + Playwright no Captei |
