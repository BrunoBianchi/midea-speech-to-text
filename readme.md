# Midea Speech-to-Text

Monorepo com três aplicações independentes, cada uma com seu próprio runtime
e ciclo de deploy:

```
apps/
├── backend/      # Servidor (TypeScript / Node.js)
├── ai-service/    # Serviço de IA (Python / Flask)
└── frontend/      # Cliente web
```

## Por que separadas?

- **backend** e **ai-service** usam linguagens, runtimes e gerenciadores de
  dependência diferentes (`package.json` vs `requirements.txt`), então cada
  um vive isolado em sua própria pasta, sem código compartilhado entre eles.
- A comunicação entre `backend` e `ai-service` acontece via HTTP, tratando
  cada serviço como uma caixa-preta em relação ao outro.
- O `frontend` conversa apenas com o `backend`; ele nunca acessa o
  `ai-service` diretamente.

Cada pasta em `apps/` tem seu próprio README com detalhes da estrutura interna.

## Documentação

Documentação adicional do projeto (arquitetura, decisões, etc.) fica em `docs/`.
