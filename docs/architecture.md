# Architecture — Interview Trainer IA

> Documento vivo — atualizar a cada mudança estrutural relevante.

---

## Visão Geral

O Interview Trainer IA é uma aplicação web monolítica com separação clara entre frontend e backend, projetada para escalar horizontalmente quando necessário. A arquitetura prioriza simplicidade de desenvolvimento (portfólio) com decisões que não barram a evolução para produto SaaS.

```
┌─────────────────────────────────────────────────┐
│                   BROWSER                        │
│  HTML5 + CSS3 + JS ES6 Modules + Web Audio API  │
└────────────────────┬────────────────────────────┘
                     │ HTTPS / WebSocket
┌────────────────────▼────────────────────────────┐
│              FLASK BACKEND (Python)              │
│  REST API  │  AI Orchestrator  │  File Service  │
└──────┬──────────────┬──────────────────┬────────┘
       │              │                  │
┌──────▼──────┐ ┌─────▼──────┐ ┌────────▼───────┐
│   SQLite DB  │ │ OpenAI API │ │  File System   │
│  (Sessions,  │ │ GPT-4o +   │ │  (Currículos,  │
│  Users, etc) │ │ Whisper)   │ │   Relatórios)  │
└─────────────┘ └────────────┘ └────────────────┘
```

---

## Stack Tecnológica

| Camada | Tecnologia | Justificativa |
|--------|-----------|--------------|
| Frontend | HTML5, CSS3, JS ES6 Modules | Zero build step, máxima transparência de código para portfólio |
| Backend | Python 3.11+ / Flask | Ecossistema IA nativo, rápido para prototipar |
| IA — Chat | OpenAI GPT-4o | Melhor custo-benefício em roleplay de recrutador |
| IA — Voz | OpenAI Whisper | Alta precisão em PT-BR, integração direta com a OpenAI |
| Análise | Pandas | Cálculo de WPM, vícios, métricas de fluência |
| Banco de Dados | SQLite | Sem infraestrutura adicional para portfólio; migrar para PostgreSQL no SaaS |
| PDF Upload | PyMuPDF (fitz) | Extração robusta de texto de currículos |
| PDF Export | ReportLab | Geração programática de relatórios com gráficos |
| Autenticação | Flask-JWT-Extended | JWT stateless, pronto para escalar |

---

## Estrutura de Pastas

```
interview-trainer-ia/
│
├── backend/
│   ├── app.py                      # Factory pattern, cria a app Flask
│   ├── config.py                   # Config por ambiente (dev/staging/prod)
│   ├── requirements.txt
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # POST /auth/register, /auth/login
│   │   │   ├── interview.py        # POST /interview/session, /message, /audio
│   │   │   ├── analysis.py         # GET /analysis/session/:id
│   │   │   ├── feedback.py         # GET /feedback/:id, /report
│   │   │   └── user.py             # GET|PATCH /user/profile, /resume, /job
│   │   │
│   │   └── middleware/
│   │       ├── auth.py             # Decorator JWT @require_auth
│   │       └── rate_limit.py       # Throttling por usuário/IP
│   │
│   ├── services/
│   │   ├── ai_orchestrator.py      # Constrói prompts + chama GPT-4o
│   │   ├── speech_service.py       # Envia áudio ao Whisper, retorna transcrição
│   │   ├── analysis_service.py     # Pandas: WPM, vícios, clareza
│   │   ├── resume_parser.py        # PyMuPDF → dict estruturado
│   │   ├── job_analyzer.py         # Extrai requisitos da vaga via GPT
│   │   ├── feedback_builder.py     # Agrega dados e monta JSON de feedback
│   │   └── report_generator.py     # ReportLab → PDF do relatório
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── feedback.py
│   │   └── job.py
│   │
│   ├── prompts/                    # Ver prompts.md para conteúdo
│   │   ├── recruiter_senior.txt
│   │   ├── recruiter_hr.txt
│   │   ├── recruiter_techlead.txt
│   │   └── feedback_generator.txt
│   │
│   └── database/
│       ├── db.py                   # Conexão SQLite + helpers
│       ├── schema.sql              # DDL completo
│       └── migrations/             # Scripts de migração versionados
│
├── frontend/
│   ├── index.html                  # Landing + onboarding
│   ├── pages/
│   │   ├── interview.html          # Tela principal da entrevista
│   │   ├── dashboard.html          # Histórico e métricas
│   │   └── feedback.html           # Resultado da sessão
│   │
│   ├── assets/
│   │   ├── css/
│   │   │   ├── main.css            # Reset, variáveis, tipografia
│   │   │   ├── themes.css          # Modo claro, escuro, alto contraste
│   │   │   ├── accessibility.css   # Font scale, foco, redução de movimento
│   │   │   ├── interview.css
│   │   │   └── dashboard.css
│   │   │
│   │   └── js/
│   │       ├── main.js             # Bootstrap da aplicação
│   │       ├── modules/
│   │       │   ├── interview.js    # Máquina de estados da entrevista
│   │       │   ├── recorder.js     # Web Audio API — captura e chunks
│   │       │   ├── timer.js        # Modo pressão cronometrado
│   │       │   ├── feedback.js     # Renderiza resultado e gráficos
│   │       │   ├── dashboard.js    # Histórico e evolução
│   │       │   └── accessibility.js # Tema, fonte, Libras, preferências
│   │       │
│   │       └── utils/
│   │           ├── api.js          # Fetch wrapper com JWT automático
│   │           └── storage.js      # LocalStorage helpers tipados
│
├── docs/
│   ├── api-docs.md                 # Este documento
│   ├── architecture.md             # Você está aqui
│   └── prompts.md                  # Engenharia de prompts documentada
│
├── tests/
│   ├── test_ai_orchestrator.py
│   ├── test_speech_service.py
│   ├── test_analysis_service.py
│   └── test_api_routes.py
│
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## Fluxo de uma Sessão de Entrevista

### Modo Texto

```
Usuário                Frontend              Backend             OpenAI
   │                      │                     │                   │
   ├─ Configura sessão ──►│                     │                   │
   │                      ├─ POST /session ────►│                   │
   │                      │                     ├─ Carrega currículo│
   │                      │                     ├─ Carrega vaga     │
   │                      │                     ├─ Monta prompt ───►│
   │                      │                     │◄── 1ª pergunta ───┤
   │◄── 1ª pergunta ──────┤◄── JSON response ───┤                   │
   │                      │                     │                   │
   ├─ Digita resposta ───►│                     │                   │
   │                      ├─ POST /message ─────►│                  │
   │                      │                     ├─ Salva no DB      │
   │                      │                     ├─ Monta contexto ─►│
   │                      │                     │◄── próx. pergunta ┤
   │◄── próx. pergunta ───┤◄── JSON response ───┤                   │
   │         ...           │          ...         │        ...        │
   ├─ Encerra ───────────►│                     │                   │
   │                      ├─ POST /end ─────────►│                  │
   │                      │                     ├─ Gera feedback ──►│
   │                      │                     │◄── JSON feedback ─┤
   │◄── Tela de resultado ┤◄── feedback_id ─────┤                   │
```

### Modo Voz

O modo voz adiciona a camada do Whisper entre o usuário e o backend:

1. **Captura:** `recorder.js` usa `MediaRecorder` da Web Audio API e segmenta em chunks de ~5 segundos.
2. **Envio:** Cada chunk é enviado para `POST /interview/session/:id/audio` via `multipart/form-data`.
3. **Transcrição:** `speech_service.py` encaminha para Whisper e retorna o texto.
4. **Exibição ao vivo:** A transcrição é exibida em tempo real no frontend enquanto o usuário fala.
5. **Processamento:** Ao sinalizar `is_final: true`, o backend consolida os chunks, analisa o áudio completo e gera a próxima pergunta.

---

## Banco de Dados — Schema Simplificado

```sql
-- Usuários e autenticação
users            (id, name, email, password_hash, plan, created_at)
user_preferences (user_id, theme, font_size, libras_enabled, high_contrast, language)

-- Contexto da candidatura
resumes          (id, user_id, filename, parsed_json, uploaded_at)
jobs             (id, user_id, title, company, description, type, seniority, analysis_json)

-- Sessões
sessions         (id, user_id, job_id, resume_id, mode, persona, pressure_mode,
                  time_limit, status, started_at, ended_at)
messages         (id, session_id, role, content, audio_path, created_at)

-- Análise e resultados
speech_metrics   (id, session_id, wpm_avg, filler_words_json, pause_analysis_json,
                  vocabulary_json)
feedbacks        (id, session_id, overall_score, score_breakdown_json, strengths_json,
                  improvements_json, action_plan_json, generated_at)
```

---

## Decisões de Arquitetura

### Por que SQLite e não PostgreSQL?
Para portfólio, SQLite é suficiente e elimina dependência externa. A camada `db.py` abstrai a conexão — trocar por PostgreSQL exige mudar apenas a string de conexão e o driver. Usar SQLAlchemy desde o início garante essa portabilidade.

### Por que chunks de áudio em vez de stream WebSocket?
Simplicidade de implementação e compatibilidade. WebSocket seria ideal para latência mínima, mas chunks via REST funcionam bem com latência aceitável (~1s) e são mais fáceis de debugar e documentar em portfólio.

### Por que manter prompts em arquivos `.txt`?
Versionamento claro, facilidade de editar sem tocar em código Python, e documenta explicitamente a "personalidade" de cada persona — um diferencial visível em portfólio que demonstra cuidado com prompt engineering.

### Por que módulos JS ao invés de um framework?
ES6 Modules nativos eliminam build step, tornando o projeto facilmente compreensível sem ferramental extra. Para evolução ao SaaS, migrar para React/Vue é simples dado que a lógica está encapsulada em módulos.

---

## Acessibilidade — Implementação

| Recurso | Implementação |
|---------|--------------|
| Modo escuro/claro | CSS custom properties + `prefers-color-scheme` + toggle manual salvo no backend |
| Tamanho de fonte | 4 níveis via classe no `<html>` (`font-sm`, `font-md`, `font-lg`, `font-xl`) |
| Alto contraste | Classe `high-contrast` com paleta WCAG AAA |
| Libras | Integração com VLibras (widget gov.br) — ativado por toggle nas preferências |
| Navegação por teclado | Todos os elementos interativos com `tabindex` e `focus-visible` estilizados |
| Redução de movimento | `@media (prefers-reduced-motion: reduce)` em todas as animações |
| Leitores de tela | `aria-live`, `aria-label`, papéis semânticos em toda a interface de entrevista |
| WCAG | Nível AA como mínimo; AAA nas telas críticas (entrevista, feedback) |

---

## Roadmap de Evolução (portfólio → produto)

### Fase 1 — MVP (portfólio)
- [x] Entrevista por texto e voz
- [x] Upload de currículo e vaga
- [x] Feedback estruturado
- [x] Relatório PDF básico
- [x] Acessibilidade WCAG AA

### Fase 2 — Produto Beta
- [ ] Autenticação social (Google, LinkedIn)
- [ ] Banco de perguntas curadas por área e senioridade
- [ ] Sistema de streak e badges de progresso
- [ ] Comparação de evolução entre sessões
- [ ] Modo empresa (RH cria roteiros customizados)

### Fase 3 — SaaS
- [ ] Migração para PostgreSQL + Redis (cache de sessões ativas)
- [ ] Planos via Stripe (Free / Pro / Enterprise)
- [ ] Deploy em containers (Docker + Railway / Render)
- [ ] API pública para integrações (LinkedIn, Glassdoor)
- [ ] Suporte a múltiplos idiomas (EN, ES)