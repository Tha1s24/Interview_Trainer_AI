# Arquitetura do Interview Trainer AI

O projeto utiliza uma arquitetura baseada em **Cliente-Servidor (REST API)**.

- **Frontend:** HTML5, CSS3, JavaScript (Módulos).
- **Backend:** Python com Flask.
- **Banco de Dados:** SQLite3.
- **IA:** OpenAI API (GPT-4o para texto e Whisper para áudio).



## Fluxo de Dados
1. O usuário interage com o `interview.js` no navegador.
2. O áudio é capturado e enviado para `/api/interview/process-voice`.
3. O `ai_service.py` processa a voz e consulta o LLM para gerar uma resposta.
4. O histórico da conversa é persistido no banco de dados SQLite.
5. O feedback é analisado pelo `analysis_service.py` e exibido no `feedback.html`.