# API Documentation

## Authentication
- `POST /api/auth/login`: Autentica o usuário e retorna token.
- `POST /api/auth/register`: Cria um novo registro de usuário.

## Interview
- `POST /api/interview/ask`: Recebe o histórico e retorna a próxima pergunta da IA.
- `POST /api/interview/process-voice`: Recebe um arquivo `.webm` e retorna transcrição.

## Feedback
- `POST /api/feedback/generate`: Analisa as respostas e retorna JSON com métricas de performance.