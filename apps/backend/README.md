# Backend (TypeScript)

Servidor da aplicação. Responsável por regras de negócio, persistência,
autenticação e por orquestrar a comunicação com o serviço de IA (`apps/ai-service`).

## Estrutura

```
src/
├── index.ts        # ponto de entrada do servidor
├── routes/         # definição das rotas expostas pela API
├── controllers/     # recebem a requisição e chamam os services
└── services/         # lógica de negócio
```

## Comunicação com a IA

Este serviço consome o `apps/ai-service` (Flask) via HTTP, tratando-o como um
serviço externo — sem dependências de código compartilhadas entre os dois.
