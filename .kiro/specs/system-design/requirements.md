# Requirements Document

## Introduction

Este documento define os requisitos da **primeira fatia (first slice)** do sistema **Midea Speech-to-Text & Call Center Intelligence (PoC)**, derivados diretamente do documento de design aprovado (`design.md`) e do product brief (`Docs/Markdowns/project-brief.md`).

O escopo cobre o **sistema de backend inicial**, assíncrono e orientado a eventos: ponto de entrada → Kubernetes Ingress/Service (exposição de borda) → Gateway/Orquestrador Node.js (entrada HTTP, recebimento de upload, balanceamento/roteamento e orquestração das lanes) → contêineres FastAPI (Docker, 1 servidor por contêiner) → mensageria RabbitMQ (`direct-exchange` com routing keys) → três workers conceituais (Ruído, Transcrição, IA) → Retry System + Dead Letter Queue → persistência em MongoDB → notificações ao dashboard via SSE/callback. A ingestão de áudio ocorre **sempre via API/gateway**, nunca com acesso direto aos workers.

Os internals de ML de cada worker (DeepFilterNet3, WhisperX/Whisper, Pyannote, LLMs locais) permanecem em **nível conceitual**. Os requisitos capturam o comportamento observável do backend, as invariantes de correção do design e as metas mensuráveis dos OKRs do brief (RTF, mascaramento de PII, cobertura de auditoria, WER), além das restrições de conformidade LGPD, operação offline/local e tolerância a falhas.

## Glossary

- **System**: O sistema Midea Speech-to-Text & Call Center Intelligence (PoC) como um todo.
- **Gateway**: Gateway/Orquestrador Node.js — ponto de entrada HTTP, reverse proxy das réplicas FastAPI e coordenador das lanes.
- **API_Container**: Contêiner Docker encapsulando 1 servidor FastAPI, responsável pelo endpoint de upload e validação de payload.
- **Ingress**: Kubernetes Ingress/Service que expõe o Gateway na borda e realiza terminação TLS de borda.
- **Exchange**: `direct-exchange` do RabbitMQ que roteia mensagens por routing key.
- **Noise_Queue / Transcript_Queue / AI_Queue**: Filas RabbitMQ correspondentes às routing keys `routingKey.audio`, `routingKey.transcript` e `routingKey.AI`.
- **Noise_Worker**: Worker conceitual de redução de ruído (lane NOISE).
- **Transcript_Worker**: Worker conceitual de transcrição, diarização e mascaramento de PII (lane TRANSCRIPT).
- **AI_Worker**: Worker conceitual de decisão por IA que gera objeto JSON estruturado (lane AI).
- **RAG**: Componente de Retrieval-Augmented Generation que indexa os scripts/protocolos de atendimento de referência e fornece recuperação de contexto (somente leitura) ao AI_Worker.
- **Attendant_Script** (ou Script de Atendimento): O roteiro/protocolo que os atendentes deveriam seguir, armazenado na base `attendant_scripts` e consultado via RAG.
- **Retry_System**: Componente que recebe as arestas `Fail` das lanes, aplica política de retry e encaminha à Dead Letter Queue.
- **Dead_Letter_Queue (DLQ)**: Fila de mensagens cujas tentativas se esgotaram.
- **MongoDB**: Persistência durável de jobs, estados por lane, resultados e metadados.
- **Redis**: Armazenamento de estado efêmero / cache de apoio por lane.
- **SSE_Channel**: Canal Server-Sent Events que entrega notificações em tempo real ao dashboard.
- **Job**: Documento mestre de uma gravação em processamento (coleção `call_jobs`).
- **Lane**: Uma das três esteiras de processamento: NOISE, TRANSCRIPT ou AI.
- **PII**: Dados pessoais identificáveis (ex.: CPF, endereço, telefone) sujeitos à LGPD.
- **RTF**: Real-Time Factor — razão entre tempo de processamento e duração do áudio.
- **WER**: Word Error Rate — taxa de erro de palavras da transcrição.

## Requirements

### Requirement 1: Ingestão de Áudio via API

**User Story:** Como agente de suporte, quero enviar gravações de chamadas por upload através da API, para que o áudio entre no pipeline de processamento sem acesso direto aos workers.

#### Acceptance Criteria

1. WHEN um upload de áudio é recebido no endpoint de upload do API_Container, THE API_Container SHALL validar o payload (formato de áudio e metadados) usando Pydantic antes de aceitar o Job.
2. WHEN um upload de áudio é recebido no endpoint de upload do API_Container, THE API_Container SHALL aceitar apenas arquivos cujo formato esteja entre os formatos de áudio suportados, com tamanho de arquivo entre 1 byte e 500 MB e cada campo textual de metadados com no máximo 1024 caracteres.
3. IF o payload de upload é inválido (formato de áudio não suportado, ou metadados não conformes), THEN THE API_Container SHALL rejeitar a requisição sem criar documento em `call_jobs`, retornar uma resposta de erro de validação indicando o campo ou regra violada, e preservar inalterado o estado do System.
4. WHEN um upload válido é aceito, THE System SHALL criar, em até 5 segundos, um documento em `call_jobs` com um `_id` único, `status` igual a `RECEIVED` e `audioRef` presente apontando para o áudio armazenado.
5. WHEN um upload válido é aceito, THE API_Container SHALL retornar ao cliente uma resposta de confirmação contendo o `call_jobs._id` criado.
6. THE System SHALL exigir que todo áudio processado possua um `call_jobs._id` criado por um endpoint de upload da API, de modo que nenhum Noise_Worker, Transcript_Worker ou AI_Worker receba trabalho sem passar pelo Gateway e pelo API_Container.
7. WHERE o áudio é enviado em formato não comprimido (`.WAV`), THE System SHALL encaminhar o áudio ao pipeline sem aplicar recompressão ou transcodificação com perdas antes da lane NOISE.

### Requirement 2: Exposição de Borda e Balanceamento no Gateway

**User Story:** Como operador de infraestrutura, quero que a borda exponha apenas o Gateway e que o balanceamento de aplicação seja feito pelo próprio Gateway, para que a arquitetura de entrada seja consistente e controlada.

#### Acceptance Criteria

1. THE Ingress SHALL expor exclusivamente o Gateway como ponto de entrada externo na borda, realizar a terminação TLS de borda e não expor diretamente nenhum API_Container, Noise_Worker, Transcript_Worker, AI_Worker, Exchange, fila RabbitMQ, MongoDB ou Redis.
2. WHEN uma requisição HTTP chega ao Gateway, THE Gateway SHALL rotear a requisição, atuando como reverse proxy em nível de aplicação, para um dos API_Containers considerados disponíveis, distribuindo as requisições entre todos os API_Containers disponíveis.
3. WHERE um API_Container responde com sucesso a sua verificação de prontidão (readiness/health check) dentro de um limite de 2 segundos, THE Gateway SHALL considerá-lo disponível como destino de roteamento; caso contrário, THE Gateway SHALL considerá-lo indisponível e não roteá-lo.
4. IF nenhum API_Container está disponível no momento do roteamento, THEN THE Gateway SHALL rejeitar a requisição, retornar uma resposta de erro indicando indisponibilidade do serviço de upstream e não publicar nenhuma mensagem no Exchange para essa requisição.
5. THE Gateway SHALL ser o único produtor de mensagens para o Exchange, publicando exclusivamente com uma das routing keys definidas (`routingKey.audio`, `routingKey.transcript` ou `routingKey.AI`) conforme a lane de destino.

### Requirement 3: Roteamento Determinístico por Routing Key

**User Story:** Como arquiteto do sistema, quero roteamento determinístico de mensagens por routing key, para que cada mensagem chegue exclusivamente à fila correta.

#### Acceptance Criteria

1. WHEN o Gateway publica uma mensagem no Exchange com `routingKey.audio`, THE Exchange SHALL entregar a mensagem à Noise_Queue e a nenhuma outra fila.
2. WHEN o Gateway publica uma mensagem no Exchange com `routingKey.transcript`, THE Exchange SHALL entregar a mensagem à Transcript_Queue e a nenhuma outra fila.
3. WHEN o Gateway publica uma mensagem no Exchange com `routingKey.AI`, THE Exchange SHALL entregar a mensagem à AI_Queue e a nenhuma outra fila.
4. WHEN o Gateway publica uma mensagem no Exchange com uma routing key pertencente ao conjunto válido fechado `{routingKey.audio, routingKey.transcript, routingKey.AI}`, THE Exchange SHALL entregar a mensagem a exatamente uma fila de destino, determinada unicamente por essa routing key, e a nenhuma outra fila.
5. IF o Gateway publica uma mensagem no Exchange com uma routing key que não pertence ao conjunto válido `{routingKey.audio, routingKey.transcript, routingKey.AI}`, THEN THE Exchange SHALL não entregar a mensagem a nenhuma das filas Noise_Queue, Transcript_Queue ou AI_Queue e SHALL encaminhá-la à Dead_Letter_Queue, preservando a mensagem sem descarte silencioso.

### Requirement 4: Sequenciamento das Lanes de Processamento

**User Story:** Como arquiteto do sistema, quero que as lanes de processamento sejam sequenciadas corretamente, para que cada etapa só ocorra após o sucesso da etapa anterior.

#### Acceptance Criteria

1. WHEN um Job é criado com `call_jobs.status` igual a `RECEIVED`, THE Gateway SHALL publicar a mensagem com `routingKey.audio` para iniciar o Job pela lane NOISE e SHALL não publicar `routingKey.transcript` nem `routingKey.AI` para esse Job antes da conclusão com sucesso da lane NOISE.
2. WHEN a lane NOISE conclui com sucesso para um Job (`workflow_states.state` igual a `SUCCESS` com `outputRef` presente para `(jobId, NOISE)`), THE Gateway SHALL publicar a mensagem com `routingKey.transcript` para avançar o Job à lane TRANSCRIPT e SHALL atualizar `call_jobs.status` para `TRANSCRIPT`.
3. WHEN a lane TRANSCRIPT conclui com sucesso para um Job (`workflow_states.state` igual a `SUCCESS` com `outputRef` presente para `(jobId, TRANSCRIPT)`), THE Gateway SHALL publicar a mensagem com `routingKey.AI` para avançar o Job à lane AI e SHALL atualizar `call_jobs.status` para `AI`.
4. IF a lane TRANSCRIPT ainda não registrou `workflow_states.state` igual a `SUCCESS` para `(jobId, TRANSCRIPT)`, THEN THE Gateway SHALL não publicar `routingKey.AI` para esse Job, preservando o estado corrente do Job sem alterá-lo.
5. IF a lane NOISE ainda não registrou `workflow_states.state` igual a `SUCCESS` para `(jobId, NOISE)`, THEN THE Gateway SHALL não publicar `routingKey.transcript` para esse Job, preservando o estado corrente do Job sem alterá-lo.
6. IF uma mensagem de avanço para a lane TRANSCRIPT ou AI é recebida fora de ordem (sem o registro de sucesso da lane imediatamente anterior em `workflow_states`), THEN THE Gateway SHALL rejeitar o avanço usando `workflow_states` como fonte de verdade, sem produzir efeitos colaterais na lane de destino e sem alterar `call_jobs.status`.

### Requirement 5: Tolerância a Falhas com Retry e Dead-Letter

**User Story:** Como operador do sistema, quero tolerância a falhas com retry e dead-letter, para que nenhuma mensagem seja perdida silenciosamente.

#### Acceptance Criteria

1. IF um Noise_Worker, Transcript_Worker ou AI_Worker falha ao processar uma mensagem — sinalizando a aresta Fail, lançando erro ou não confirmando o processamento —, THEN THE System SHALL encaminhar a mensagem ao Retry_System em vez de descartá-la.
2. THE Retry_System SHALL usar um valor de `maxAttempts` inteiro, maior ou igual a 1 e menor ou igual a 10, com valor padrão igual a 3.
3. WHEN o Retry_System recebe uma mensagem com falha e `attempts` é menor que `maxAttempts`, THE Retry_System SHALL incrementar o contador de tentativas, aplicar um backoff cujo atraso é não decrescente e estritamente maior que o da tentativa anterior, entre 1 e 300 segundos, e re-publicar a mensagem na fila de origem via Exchange.
4. IF `attempts` é maior ou igual a `maxAttempts`, THEN THE Retry_System SHALL encaminhar a mensagem à Dead_Letter_Queue, marcar o Job como `FAILED` em `call_jobs`, registrar os metadados em `retry_metadata` e preservar a mensagem sem descarte.
5. THE System SHALL garantir que toda mensagem termine em exatamente um de dois estados terminais: concluída com sucesso (avança ou finaliza) ou registrada na Dead_Letter_Queue.
6. THE Retry_System SHALL marcar `retry_metadata.deadLettered` como `true` se e somente se `attempts` for maior ou igual a `maxAttempts`.

### Requirement 6: Conformidade LGPD e Mascaramento de PII

**User Story:** Como auditor de QA, quero que as transcrições estejam em conformidade com a LGPD, para que nenhum dado pessoal atravesse a fronteira de processamento.

#### Acceptance Criteria

1. WHEN o Transcript_Worker produz uma transcrição diarizada, THE Transcript_Worker SHALL aplicar a etapa de NLP de mascaramento/remoção de PII antes de persistir o resultado.
2. IF um documento de `transcripts` possui `piiMasked` ausente/indefinido ou igual a `false`, THEN THE System SHALL impedir sua persistência na coleção `transcripts` e preservar inalterado o estado da coleção.
3. THE AI_Worker SHALL derivar `ai_decisions` somente a partir de texto com `piiMasked` igual a `true`.
4. THE System SHALL mascarar com eficácia maior ou igual a 95% as ocorrências de PII das categorias CPF, endereço e telefone presentes nas transcrições geradas, medido sobre um conjunto de avaliação rotulado.
5. WHEN um segmento diarizado é persistido, THE System SHALL restringir `segments[].speaker` aos valores `AGENT` ou `CONSUMER` e SHALL rejeitar a persistência de segmento com valor de `speaker` fora desse conjunto.
6. IF a etapa de mascaramento de PII falha para uma transcrição, THEN THE System SHALL encaminhar a mensagem ao Retry_System e impedir a persistência da transcrição não mascarada.

### Requirement 7: Consistência de Estado por Job e Lane

**User Story:** Como desenvolvedor do backend, quero consistência de estado por job e lane, para que o estado do sistema permaneça rastreável e sem duplicação.

#### Acceptance Criteria

1. THE System SHALL manter no máximo um documento em `workflow_states` para cada par `(jobId, lane)`.
2. IF uma operação tenta criar um segundo documento em `workflow_states` para um par `(jobId, lane)` que já possui um documento, THEN THE System SHALL rejeitar a criação, preservar o documento existente inalterado e sinalizar a violação de unicidade à operação chamadora.
3. WHEN o estado da lane corrente de um Job transita para `PROCESSING`, THE System SHALL atualizar `call_jobs.status` para o valor correspondente à lane ativa dentre `NOISE`, `TRANSCRIPT` ou `AI`, de modo que `NOISE` corresponda à lane NOISE, `TRANSCRIPT` à lane TRANSCRIPT e `AI` à lane AI.
4. WHEN a lane AI de um Job transita para `SUCCESS`, THE System SHALL atualizar `call_jobs.status` para `DONE`.
5. WHEN uma lane conclui com sucesso, THE System SHALL registrar `workflow_states.state` igual a `SUCCESS` com o campo `outputRef` presente e não vazio.
6. IF uma lane falha de forma terminal para um Job, THEN THE System SHALL registrar `workflow_states.state` igual a `FAILED` para o par `(jobId, lane)` e atualizar `call_jobs.status` para `FAILED`.
7. WHEN um Job é criado após ingestão bem-sucedida, THE System SHALL registrar `call_jobs.status` igual a `RECEIVED`.
8. WHEN um Job é criado após ingestão bem-sucedida, THE System SHALL registrar o campo `audioRef` presente e não vazio no documento de `call_jobs`.

### Requirement 8: Idempotência de Reprocessamento

**User Story:** Como operador do sistema, quero que o reprocessamento seja idempotente, para que retries não gerem resultados duplicados.

#### Acceptance Criteria

1. WHEN uma mensagem é reprocessada após falha para um par `(jobId, lane)` cujo `workflow_states.state` já é igual a `SUCCESS`, THE System SHALL ignorar o reprocessamento sem reexecutar os efeitos colaterais da lane e sem criar um segundo resultado para esse par.
2. THE System SHALL consultar `workflow_states` como fonte de verdade e tratar uma etapa como já concluída quando, e somente quando, `workflow_states.state` for igual a `SUCCESS`, antes de aplicar qualquer efeito colateral da lane.
3. WHEN uma mensagem é reprocessada para um par `(jobId, lane)` cujo `workflow_states.state` ainda não é `SUCCESS`, THE System SHALL executar a lane normalmente e registrar o resultado no documento único de `workflow_states` existente para esse par, sem criar documento adicional.
4. IF uma lane já concluída com `workflow_states.state` igual a `SUCCESS` recebe nova tentativa de reprocessamento, THEN THE System SHALL preservar o `outputRef` já registrado e não substituí-lo nem gerar um `outputRef` adicional.
5. IF uma lane já concluída com `workflow_states.state` igual a `SUCCESS` recebe nova tentativa de reprocessamento, THEN THE System SHALL não publicar novamente a mensagem de avanço para a próxima lane via Exchange.

### Requirement 9: Notificações em Tempo Real via SSE

**User Story:** Como supervisor/auditor de QA, quero receber notificações em tempo real do estado do processamento, para que eu acompanhe o progresso sem bloqueio de interface.

#### Acceptance Criteria

1. WHEN um Job transita para o estado `DONE`, THE SSE_Channel SHALL emitir uma notificação ao dashboard em até 2 segundos.
2. WHEN um Job transita para o estado `FAILED`, THE SSE_Channel SHALL emitir uma notificação ao dashboard em até 2 segundos.
3. WHEN uma lane conclui com sucesso, THE System SHALL emitir via SSE_Channel o evento de progresso correspondente dentre `NOISE_DONE`, `TRANSCRIPT_DONE` e `AI_DONE`.
4. WHEN um API_Container emite um evento SSE de progresso, THE Gateway SHALL retransmitir esse evento ao dashboard.
5. WHEN o MongoDB conclui ou atualiza um estado relevante (transição de `call_jobs.status` ou de `workflow_states.state`), THE MongoDB SHALL emitir um callback ao Gateway.
6. IF a conexão SSE com o dashboard é perdida, THEN THE SSE_Channel SHALL permitir o restabelecimento da conexão e a retomada do fluxo de eventos sem bloquear o processamento dos Jobs.

### Requirement 10: Metas de Desempenho e Cobertura

**User Story:** Como gerente de operação, quero que o pipeline atenda às metas de desempenho e cobertura, para que a PoC seja viável e auditável em escala.

#### Acceptance Criteria

1. THE System SHALL manter o Real-Time Factor (RTF) de cada lane de processamento (NOISE, TRANSCRIPT e AI) estritamente abaixo de 1.0, medido como a razão entre o tempo de processamento da lane e a duração do áudio do Job, de modo que o tempo de processamento seja inferior à duração do áudio.
2. WHILE o pipeline opera sob carga nominal da PoC (até 50 Jobs em processamento concorrente), THE System SHALL manter a profundidade de cada fila (Noise_Queue, Transcript_Queue e AI_Queue) sem crescimento monotônico sustentado por mais de 300 segundos, de modo que não haja acúmulo crítico nas filas.
3. THE System SHALL conduzir 100% dos Jobs submetidos ao pipeline até exatamente um estado terminal — `call_jobs.status` igual a `DONE` (sucesso) ou `FAILED` após esgotamento de tentativas na Dead_Letter_Queue —, de modo que nenhum Job permaneça indefinidamente sem estado terminal.
4. IF, decorridos 600 segundos desde a criação do Job, um Job não atingiu um estado terminal (`DONE` ou `FAILED`), THEN THE System SHALL encaminhar a mensagem correspondente ao Retry_System para resolução até um estado terminal.
5. THE Transcript_Worker SHALL manter o Word Error Rate (WER) menor ou igual a 15% em um conjunto de avaliação de áudios reais da operação da Midea pós-filtragem pelo Noise_Worker, medido sobre transcrição de referência revisada por humano.

### Requirement 11: Operação Offline/Local e Open Source

**User Story:** Como gestor de TI, quero que todo o stack opere localmente e offline com stack open source, para que não haja custos recorrentes de APIs comerciais nem dependência de nuvem.

#### Acceptance Criteria

1. THE System SHALL operar integralmente em infraestrutura local/on-premises, sem realizar chamadas de rede a serviços externos de nuvem em tempo de execução para as funções de transcrição, processamento e armazenamento.
2. IF qualquer componente tentar estabelecer uma conexão de rede com um serviço externo de nuvem durante a operação em tempo de execução, THEN THE System SHALL bloquear a chamada e registrar um evento de log indicando a tentativa de acesso externo não autorizado.
3. THE System SHALL utilizar exclusivamente componentes de software distribuídos sob licenças open source aprovadas pela OSI, sem qualquer componente que exija licença comercial paga ou assinatura recorrente para operação em tempo de execução.
4. THE System SHALL ser autocontido, de modo que a totalidade das dependências necessárias para execução esteja empacotada e disponível localmente, sem necessidade de download de artefatos externos após a instalação inicial.
5. WHERE o gargalo de processamento em uma lane específica for identificado, THE System SHALL permitir o escalonamento horizontal independente dos workers daquela lane, via Docker e Kubernetes, sem exigir reinicialização ou reconfiguração dos workers das demais lanes.

### Requirement 12: Objeto JSON Estruturado de Decisão

**User Story:** Como auditor de QA, quero que o resultado final seja um objeto JSON estruturado validado por regras de negócio, para que eu atue cirurgicamente sobre alertas e resumos.

#### Acceptance Criteria

1. WHEN o AI_Worker processa um texto diarizado com `piiMasked` igual a `true`, THE AI_Worker SHALL gerar um documento `ai_decisions` cujo campo `decision` é um objeto JSON sintaticamente válido e conforme o schema de negócio (todos os campos obrigatórios presentes e com tipos esperados).
2. IF o objeto produzido para `ai_decisions.decision` não é um JSON sintaticamente válido ou não satisfaz o schema de negócio, THEN THE AI_Worker SHALL rejeitar o resultado, não persistir o documento `ai_decisions` e encaminhar a mensagem ao Retry_System com indicação de falha de validação de schema.
3. WHEN o AI_Worker gera um documento `ai_decisions`, THE AI_Worker SHALL registrar em `ai_decisions.rulesEvaluated` uma entrada para cada regra de negócio avaliada, contendo o identificador da regra e seu veredicto restrito aos valores `PASS`, `FAIL` ou `NOT_APPLICABLE`.
4. WHEN o AI_Worker gera um documento `ai_decisions`, THE AI_Worker SHALL produzir `ai_decisions.summary` como texto com no máximo 2000 caracteres, derivado exclusivamente de texto com `piiMasked` igual a `true`.
5. THE AI_Worker SHALL garantir que `ai_decisions.summary` não contenha nenhum PII (ex.: CPF, endereço, telefone), de modo que o resumo permaneça em conformidade com a LGPD.
6. WHEN o AI_Worker registra em `ai_decisions.rulesEvaluated` ao menos uma regra de aderência ao script de atendimento com veredicto igual a `PASS` ou `FAIL`, THE AI_Worker SHALL incluir em `ai_decisions.scriptContextRefs` ao menos uma referência de contexto de script recuperado do RAG e SHALL associar cada veredicto de aderência ao script a pelo menos uma entrada de `ai_decisions.scriptContextRefs`.

### Requirement 13: Recuperação de Contexto do Script via RAG

**User Story:** Como auditor de QA, quero que a validação de aderência ao roteiro seja fundamentada no script de referência recuperado via RAG, para que os veredictos de aderência sejam rastreáveis e auditáveis.

#### Acceptance Criteria

1. WHEN o AI_Worker vai gerar a decisão para um Job, THE AI_Worker SHALL consultar o RAG e recuperar o contexto do Attendant_Script de referência relevante antes de avaliar as regras de aderência ao roteiro.
2. THE RAG SHALL operar em modo somente leitura e local/offline, sem realizar chamadas de rede a serviços externos de nuvem durante a recuperação de contexto.
3. WHEN o AI_Worker registra em `ai_decisions.rulesEvaluated` um veredicto de aderência ao Attendant_Script, THE AI_Worker SHALL incluir em `ai_decisions.scriptContextRefs` ao menos uma referência ao trecho/versão de script recuperado do RAG que fundamentou esse veredicto.
4. IF o RAG não retorna nenhum contexto de Attendant_Script aplicável (base `attendant_scripts` vazia ou sem correspondência), THEN THE AI_Worker SHALL registrar os veredictos de aderência ao roteiro em `ai_decisions.rulesEvaluated` com o valor `NOT_APPLICABLE`, registrar a ausência de contexto recuperado e não criar nenhuma entrada em `ai_decisions.scriptContextRefs`.
5. THE System SHALL tratar a base `attendant_scripts` como fonte de recuperação (somente leitura) exclusiva da lane AI, de modo que nenhum Noise_Worker, Transcript_Worker ou AI_Worker escreva nessa base e que essa base não produza mensagens para o Exchange.
6. WHERE a base `attendant_scripts` disponibiliza múltiplas versões de um mesmo Attendant_Script, THE AI_Worker SHALL registrar em cada entrada de `ai_decisions.scriptContextRefs` o identificador e a versão do trecho de script recuperado do RAG que fundamentou o veredicto.
