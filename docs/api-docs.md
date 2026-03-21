# API Documentation — Interview Trainer IA

> Versão: 1.0.0 | Base URL: `http://localhost:5000/api` | Autenticação: Bearer JWT

---

## Sumário

- [Autenticação](#autenticação)
- [Usuário e Perfil](#usuário-e-perfil)
- [Currículo e Vaga](#currículo-e-vaga)
- [Sessões de Entrevista](#sessões-de-entrevista)
- [Análise de Fala](#análise-de-fala)
- [Feedback e Relatório](#feedback-e-relatório)
- [Acessibilidade](#acessibilidade)
- [Códigos de Erro](#códigos-de-erro)

---

## Autenticação

### `POST /auth/register`

Registra um novo usuário.

**Body:**
```json
{
  "name": "Ana Lima",
  "email": "ana@email.com",
  "password": "senha_segura123"
}
```

**Response `201`:**
```json
{
  "user_id": "usr_abc123",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400
}
```

---

### `POST /auth/login`

Autentica um usuário existente.

**Body:**
```json
{
  "email": "ana@email.com",
  "password": "senha_segura123"
}
```

**Response `200`:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": "usr_abc123",
    "name": "Ana Lima",
    "plan": "free"
  }
}
```

---

## Usuário e Perfil

### `GET /user/profile` 🔒

Retorna o perfil completo do usuário autenticado.

**Response `200`:**
```json
{
  "user_id": "usr_abc123",
  "name": "Ana Lima",
  "email": "ana@email.com",
  "plan": "free",
  "sessions_used": 2,
  "sessions_limit": 3,
  "preferences": {
    "language": "pt-BR",
    "theme": "dark",
    "font_size": "medium",
    "libras_enabled": false,
    "high_contrast": false
  },
  "created_at": "2025-01-10T14:30:00Z"
}
```

---

### `PATCH /user/preferences` 🔒

Atualiza preferências de acessibilidade e interface.

**Body:**
```json
{
  "theme": "dark",
  "font_size": "large",
  "libras_enabled": true,
  "high_contrast": false,
  "language": "pt-BR"
}
```

Valores aceitos:
- `theme`: `"light"` | `"dark"` | `"system"`
- `font_size`: `"small"` | `"medium"` | `"large"` | `"x-large"`
- `language`: `"pt-BR"` | `"en-US"` | `"es-ES"`

**Response `200`:**
```json
{ "updated": true, "preferences": { ... } }
```

---

## Currículo e Vaga

### `POST /user/resume` 🔒

Faz upload e processa o currículo do usuário (PDF ou DOCX).

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `file` | File | PDF ou DOCX, máx. 5 MB |

**Response `201`:**
```json
{
  "resume_id": "res_xyz789",
  "parsed": {
    "name": "Ana Lima",
    "summary": "Desenvolvedora Full Stack com 4 anos de experiência...",
    "skills": ["Python", "React", "Docker"],
    "experience": [
      {
        "title": "Desenvolvedora Backend",
        "company": "Empresa ABC",
        "period": "2022 – atual",
        "highlights": ["Reduziu tempo de deploy em 40%", "Liderou equipe de 3 devs"]
      }
    ],
    "education": ["Ciência da Computação – UFES, 2021"]
  },
  "suggested_questions_preview": 12
}
```

---

### `POST /user/job` 🔒

Adiciona a vaga para a qual o usuário está se candidatando.

**Body:**
```json
{
  "title": "Desenvolvedora Backend Sênior",
  "company": "Tech Corp",
  "description": "Buscamos profissional com experiência em Python, APIs REST e microsserviços...",
  "type": "tech",
  "seniority": "senior",
  "job_url": "https://linkedin.com/jobs/123456"
}
```

Tipos de vaga (`type`): `"tech"` | `"design"` | `"marketing"` | `"hr"` | `"sales"` | `"finance"` | `"general"`

**Response `201`:**
```json
{
  "job_id": "job_def456",
  "analysis": {
    "key_requirements": ["Python avançado", "Liderança técnica", "Cloud AWS"],
    "culture_signals": ["startup", "autonomia", "resultados"],
    "estimated_questions": 18,
    "difficulty": "high"
  }
}
```

---

## Sessões de Entrevista

### `POST /interview/session` 🔒

Cria e inicia uma nova sessão de entrevista.

**Body:**
```json
{
  "job_id": "job_def456",
  "resume_id": "res_xyz789",
  "mode": "text",
  "pressure_mode": false,
  "time_limit_minutes": null,
  "persona": "senior_recruiter",
  "language": "pt-BR"
}
```

| Campo | Valores |
|-------|---------|
| `mode` | `"text"` \| `"voice"` |
| `pressure_mode` | `true` \| `false` |
| `time_limit_minutes` | `null` \| `15` \| `20` \| `30` |
| `persona` | `"senior_recruiter"` \| `"hr_generalist"` \| `"tech_lead"` |

**Response `201`:**
```json
{
  "session_id": "sess_ghi012",
  "status": "active",
  "first_message": "Olá, Ana! Sou Carlos, recrutador sênior da Tech Corp. Vamos começar? Me fale um pouco sobre você e o que te trouxe até aqui.",
  "time_limit": null,
  "started_at": "2025-03-21T10:00:00Z"
}
```

---

### `POST /interview/session/{session_id}/message` 🔒

Envia uma resposta em texto durante a entrevista.

**Body:**
```json
{
  "content": "Tenho 4 anos de experiência com desenvolvimento backend em Python, trabalhei principalmente com APIs REST e microsserviços...",
  "type": "text"
}
```

**Response `200`:**
```json
{
  "message_id": "msg_jkl345",
  "ai_response": "Interessante! Você mencionou microsserviços — pode me dar um exemplo concreto de um desafio técnico que você resolveu nessa arquitetura?",
  "session_status": "active",
  "question_count": 2,
  "time_elapsed_seconds": 180
}
```

---

### `POST /interview/session/{session_id}/audio` 🔒

Envia um chunk de áudio para transcrição e processamento (modo voz).

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `audio` | File | WebM/WAV, chunk de até 30s |
| `chunk_index` | int | Índice do chunk (para streaming) |
| `is_final` | bool | `true` se é o último chunk |

**Response `200`:**
```json
{
  "transcript": "Trabalhei em um projeto de e-commerce onde precisamos migrar um monolito...",
  "confidence": 0.94,
  "ai_response": "Boa experiência! E como você lidou com a consistência de dados durante essa migração?",
  "speech_preview": {
    "wpm": 142,
    "filler_detected": ["então", "tipo"]
  }
}
```

---

### `POST /interview/session/{session_id}/end` 🔒

Encerra a sessão e aciona a geração de feedback.

**Response `200`:**
```json
{
  "session_id": "sess_ghi012",
  "status": "completed",
  "duration_seconds": 1247,
  "total_exchanges": 8,
  "feedback_id": "fbk_mno678",
  "feedback_ready": true
}
```

---

### `GET /interview/sessions` 🔒

Lista o histórico de sessões do usuário.

**Query params:** `?page=1&limit=10&type=voice`

**Response `200`:**
```json
{
  "sessions": [
    {
      "session_id": "sess_ghi012",
      "job_title": "Desenvolvedora Backend Sênior",
      "company": "Tech Corp",
      "mode": "text",
      "score": 78,
      "duration_seconds": 1247,
      "completed_at": "2025-03-21T10:20:47Z"
    }
  ],
  "total": 5,
  "page": 1
}
```

---

## Análise de Fala

### `GET /analysis/session/{session_id}` 🔒

Retorna métricas detalhadas de comunicação da sessão.

**Response `200`:**
```json
{
  "session_id": "sess_ghi012",
  "speech_metrics": {
    "wpm_average": 142,
    "wpm_variation": "stable",
    "total_words": 1890,
    "filler_words": {
      "count": 23,
      "rate_per_minute": 1.1,
      "top_fillers": [
        { "word": "então", "count": 12 },
        { "word": "tipo", "count": 7 },
        { "word": "né", "count": 4 }
      ]
    },
    "pause_analysis": {
      "avg_pause_ms": 320,
      "long_pauses_count": 3,
      "hesitation_rate": "low"
    },
    "vocabulary": {
      "technical_terms_used": ["microsserviços", "API REST", "Docker", "CI/CD"],
      "clarity_score": 82,
      "sentence_avg_length": 18.4
    }
  }
}
```

---

## Feedback e Relatório

### `GET /feedback/{feedback_id}` 🔒

Retorna o feedback estruturado da entrevista.

**Response `200`:**
```json
{
  "feedback_id": "fbk_mno678",
  "overall_score": 78,
  "score_breakdown": {
    "technical_knowledge": 85,
    "communication": 72,
    "structure_clarity": 76,
    "cultural_fit": 80,
    "confidence": 74
  },
  "strengths": [
    "Exemplos concretos e mensuráveis nas respostas",
    "Forte domínio técnico em Python e arquitetura de microsserviços",
    "Boa capacidade de síntese em perguntas abertas"
  ],
  "improvements": [
    "Reduza o uso de 'então' como conector — impacta percepção de confiança",
    "Respostas sobre gestão de conflito ficaram muito genéricas",
    "Trabalhe a estrutura STAR para perguntas comportamentais"
  ],
  "action_plan": [
    "Pratique 2 respostas STAR por dia sobre liderança",
    "Grave a si mesmo e identifique vícios de linguagem",
    "Pesquise mais sobre a cultura da empresa antes da próxima simulação"
  ],
  "next_session_focus": ["perguntas comportamentais", "salary negotiation"]
}
```

---

### `GET /feedback/{feedback_id}/report` 🔒

Gera e retorna o relatório completo em PDF para download.

**Query params:** `?format=pdf&lang=pt-BR`

**Response `200`:**
- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="relatorio_ana_lima_2025-03-21.pdf"`

O PDF inclui: score geral, gráfico de radar por categoria, métricas de fala, transcrição resumida, pontos de melhoria e plano de ação.

---

## Acessibilidade

### `GET /accessibility/libras/{text}` 🔒

Retorna URL do vídeo de interpretação em Libras para um trecho de texto (via integração VLibras).

**Response `200`:**
```json
{
  "text": "Me fale sobre sua experiência profissional",
  "libras_url": "https://vlibras.gov.br/...",
  "duration_seconds": 8
}
```

---

## Códigos de Erro

| Código | Significado |
|--------|-------------|
| `400` | Requisição inválida — verifique os campos |
| `401` | Token ausente ou expirado |
| `403` | Plano não permite esta ação (limite de sessões) |
| `404` | Recurso não encontrado |
| `413` | Arquivo muito grande (máx. 5 MB) |
| `422` | Erro de validação — detalhe no campo `errors` |
| `429` | Rate limit atingido — aguarde 60 segundos |
| `500` | Erro interno do servidor |

**Formato padrão de erro:**
```json
{
  "error": {
    "code": "SESSIONS_LIMIT_REACHED",
    "message": "Você atingiu o limite de 3 sessões do plano gratuito.",
    "upgrade_url": "/planos"
  }
}
```

---

> 🔒 Endpoints marcados requerem header `Authorization: Bearer <token>`