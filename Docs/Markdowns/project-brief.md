Product Brief: Midea Speech-to-Text & Call Center Intelligence (PoC)
1. Visão Geral do Produto (Product Concept)
O produto consiste em uma Prova de Conceito (PoC) de um sistema automatizado e assíncrono para o processamento, transcrição (Speech-to-Text), diarização e auditoria inteligente das chamadas de suporte técnico do call center da Midea.
A arquitetura opera por meio de microsserviços orientados a eventos (gerenciados via RabbitMQ / Redis com sistema nativo de Retry e tolerância a falhas) divididos em três esteiras principais de processamento (Workers):
Noise Reduction Workflow: Pré-processamento acústico utilizando Deep Complex Filtering (DeepFilterNet3) e restauração vocal para elevar a relação sinal-ruído sem comprometer a inteligibilidade.
Transcript Workflow: Conversão de áudio (prioritariamente em formato .WAV sem compressão com perdas) em texto via Whisper Large-v3 Turbo / WhisperX, acoplado a algoritmos de diarização (Silero VAD + Pyannote.audio) para separação exata entre os turnos de fala do atendente e do consumidor, seguido de etapa de NLP para mascaramento/remoção de dados pessoais (PII) em conformidade com a LGPD.
AI Decision Workflow: Interpretação contextual da transcrição diarizada por meio de Grandes Modelos de Linguagem (LLMs locais como JEV para validação de regras de negócio, geração de objetos JSON estruturados e envio de notificações em tempo real à interface via Server-Sent Events (SSE).
2. Declaração do Problema (Problem Statement)
Atualmente, a operação de atendimento da Midea armazena milhares de horas de gravações ricas em inteligência operacional que permanecem subutilizadas devido à inviabilidade de auditoria manual em escala. Isso gera duas falhas críticas que o produto soluciona diretamente:
Triagem falha e validação precária para abertura de Ordens de Serviço (OS): A coleta incompleta de requisitos pelo atendente induz a diagnósticos técnicos incorretos por telefone, resultando no acionamento indevido de assistência técnica de campo.
Ausência de verificação sistemática de conformidade de script: Supervisores não conseguem auditar a totalidade das ligações para garantir que os operadores seguiram o protocolo obrigatório de atendimento, gerando desvios operacionais, omissão de campos obrigatórios e transbordos indevidos de chamadas.
3. Importância de Resolver o Problema Agora (Why Now?)
A operação enfrenta uma tendência crescente na abertura de Ordens de Serviço improcedentes, acompanhada de gargalos na qualidade do atendimento telefônico. Postergar a automação dessa triagem significa absorver custos logísticos crescentes com deslocamento desnecessário de técnicos, sobrecarga da rede autorizada e degradação progressiva dos indicadores de satisfação do consumidor final.
4. Pontos de Dados e Risco de Churn (Data Points & Potential Churn)
A ineficiência na camada inicial de suporte impacta diretamente a retenção de clientes e os custos operacionais:
Atrito na Experiência do Cliente (Churn Driver): Diagnósticos incorretos geram retrabalho, dilatam o tempo total de resolução do problema (SLA) e elevam drasticamente a insatisfação do consumidor com a marca Midea.
Degradação Acústica na Ponta: Testes preliminares demonstram que áudios brutos de atendimento possuem ruídos severos de linha e ambiente que mascaram informações críticas da fala; sem o filtro neural prévio, modelos de transcrição sofrem com erros de reconhecimento e alucinações fonéticas.
Cegueira Operacional: Sem a separação automatizada de locutores (diarização) e sumarização via LLM, a auditoria depende de escuta humana integral, cobrindo uma fração estatisticamente irrelevante das chamadas diárias.
5. Oportunidade e Retorno sobre o Investimento (Opportunity & ROI)
A implementação da arquitetura proposta destrava retorno financeiro direto por meio da contenção de despesas operacionais (OpEx) e eficiência de infraestrutura:
Corte drástico em OS improcedentes: A IA atua como uma barreira de validação, auxiliando na identificação de falsos defeitos antes que um técnico seja enviado a campo sem necessidade.
Isenção Total de Licenciamento de Software (R$ 0,00): O ecossistema baseia-se 100% em tecnologias Open Source executadas localmente/offline (WhisperX, Pyannote, DeepFilterNet, Qwen/Mistral), eliminando tarifas recorrentes de APIs comerciais cobradas por minuto/hora de áudio.
Flexibilidade de CapEx/OpEx: Viabilidade de implantação local com baixo custo inicial de hardware  de R$ 6.000 a R$ 8.500 no Cenário Standard (Workstation com Qwen 4B exigindo apenas 4 GB de RAM dedicada) até R$ 28.000 a R$ 45.000 no Cenário High Performance (Servidor com Mistral 24B exigindo 55 GB de RAM) — ou em nuvem controlada (estimada em US$ 662,40/mês com GPU NVIDIA T4), com esforço enxuto de engenharia entre 80 a 120 horas técnicas.
Ganho de Produtividade na Supervisão: Supervisores deixam de ouvir áudios aleatórios e passam a atuar cirurgicamente sobre alertas de erro, campos ausentes e resumos gerados instantaneamente pela IA.
6. Riscos Mapeados (Risks)
Degradação Acústica e Sobreposição de Voz (Overlap): Ruídos extremos, sotaques regionais acentuados, compressão de áudio (ex: MP3/MP4 ou telefonia 8kHz) e falas simultâneas entre cliente e atendente podem reduzir a acurácia do ASR e fundir canais na diarização.
Alucinação em Termos Proprietários: Modelos de linguagem e transcrição podem falhar ao reconhecer códigos técnicos específicos ou nomes de linhas de produtos da Midea, exigindo futuro fine-tuning com bases em português espontâneo (como os corpus NURC-SP e CORAA).
Conformidade Legal e Privacidade (LGPD/GDPR): Gravações contêm dados pessoais sensíveis (CPF, endereço, telefone). Se a etapa de anonimização/mascaramento (NLP) no Transcript Worker falhar ou se as políticas de retenção e expurgo de disco não forem estritas, a empresa incorre em risco regulatório.
Gargalos de Hardware e Filas: Subdimensionamento de memória VRAM em picos de chamadas pode gerar atrasos nas filas do RabbitMQ/Redis, exigindo calibragem rigorosa do Retry System e balanceamento de carga.
7. Público-Alvo (Target Audience)
Supervisores e Auditores de Qualidade do Call Center: Usuários diretos do painel de auditoria que consomem os resumos, timestamps e alertas (flags) de desvio de roteiro.
Atendentes / Operadores de Suporte: Beneficiados pelo auxílio na coleta precisa dos requisitos do cliente e preenchimento de campos obrigatórios.
Gestores de Operações e Rede Autorizada Midea: Tomadores de decisão que utilizam os dados agregados para reduzir custos de campo e mapear falhas recorrentes de produtos.
8. Definição de Pronto (Definition of Done - DoD)
O projeto (PoC/MVP) será considerado concluído ao final do ciclo de 6 meses (Julho a Dezembro de 2026) quando atingir os seguintes critérios:
Infraestrutura configurada (Ambiente CUDA, drivers de GPU, containers, Load Balancer e mensageria assíncrona via Redis/RabbitMQ com Retry System operacional).
Pipeline de pré-processamento acústico (DeepFilterNet3) integrado e funcional para limpeza de ruído.
Transcript Worker executando transcrição (Whisper Large-v3 Turbo/WhisperX) combinada à diarização (Silero VAD/Pyannote) e remoção automática de dados pessoais (PII) para adequação à LGPD.
AI Worker integrado ao LLM local (Qwen 4B ou equivalente), processando o texto limpo e retornando o objeto JSON estruturado com resumo, validação de OS e análise de script.
Persistência em banco de dados configurada e comunicação assíncrona via Callback/SSE atualizando o painel mínimo do supervisor sem bloqueio de interface.
Validação técnica e institucional homologada com amostras de áudios reais da operação da Midea (Marco M6 do cronograma).
9. Métricas de Sucesso e OKRs (Success Metrics / OKRs)
Objetivo 1 (Qualidade Técnica): Garantir alta fidelidade na transcrição e interpretação de chamadas reais em Português Brasileiro.
KR 1.1: Atingir um Word Error Rate (WER) abaixo do limite de corte operacional em áudios reais da Midea pós-filtragem pelo DeepFilterNet.
KR 1.2: Manter o Real-Time Factor (RTF) do pipeline assíncrono < 1.0, garantindo que o tempo de processamento seja inferior à duração original da chamada sem gerar acúmulo crítico nas filas (RabbitMQ/Redis).
KR 1.3: Atingir índice de eficácia >= 95% no mascaramento automático de Dados Pessoais Identificáveis (PII) nas transcrições geradas.
Objetivo 2 (Eficiência Operacional e Negócio): Mitigar custos logísticos e escalar a capacidade de auditoria do Call Center.
KR 2.1: Reduzir em X% (meta a ser calibrada no Marco M6) o número de Ordens de Serviço abertas com diagnóstico incorreto ou sem validação prévia de requisitos.
KR 2.2: Elevar a cobertura de chamadas auditadas de uma amostra manual restrita para 100% dos áudios submetidos ao pipeline, entregando alertas automáticos de aderência ao script para a supervisão.
KR 2.3: Reduzir em Y% o tempo médio gasto por supervisores na revisão individual de atendimentos críticos por meio do consumo direto dos resumos e flags gerados pelo LLM.

