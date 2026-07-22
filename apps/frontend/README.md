# Frontend

Cliente web da aplicação. Consome exclusivamente a API do `apps/backend`
(nunca fala diretamente com o `apps/ai-service`).

## Estrutura

```
src/
├── main.tsx     # ponto de entrada
├── components/  # componentes de UI reutilizáveis
├── pages/       # telas / rotas da aplicação
└── services/    # clientes de API (chamadas HTTP ao backend)
public/          # arquivos estáticos servidos diretamente
```
