-- ============================================================
-- Interview Trainer IA — Schema SQLite
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- Usuários
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,           -- usr_<uuid4 hex>
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    plan        TEXT NOT NULL DEFAULT 'free',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- Preferências de acessibilidade e interface
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id         TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    theme           TEXT NOT NULL DEFAULT 'system',   -- light | dark | system
    font_size       TEXT NOT NULL DEFAULT 'medium',   -- small | medium | large | x-large
    libras_enabled  INTEGER NOT NULL DEFAULT 0,       -- 0 | 1 (boolean)
    high_contrast   INTEGER NOT NULL DEFAULT 0,
    language        TEXT NOT NULL DEFAULT 'pt-BR'     -- pt-BR | en-US | es-ES
);

-- ------------------------------------------------------------
-- Currículos enviados pelos usuários
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resumes (
    id          TEXT PRIMARY KEY,           -- res_<uuid4 hex>
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    parsed_json TEXT NOT NULL DEFAULT '{}', -- JSON com dados extraídos
    uploaded_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- Vagas para as quais o usuário está se candidatando
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jobs (
    id              TEXT PRIMARY KEY,       -- job_<uuid4 hex>
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    description     TEXT NOT NULL,
    type            TEXT NOT NULL DEFAULT 'general',
    seniority       TEXT NOT NULL DEFAULT 'mid',
    job_url         TEXT,
    analysis_json   TEXT NOT NULL DEFAULT '{}',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- Sessões de entrevista
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id              TEXT PRIMARY KEY,       -- sess_<uuid4 hex>
    user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id          TEXT REFERENCES jobs(id),
    resume_id       TEXT REFERENCES resumes(id),
    mode            TEXT NOT NULL DEFAULT 'text',       -- text | voice
    persona         TEXT NOT NULL DEFAULT 'senior_recruiter',
    pressure_mode   INTEGER NOT NULL DEFAULT 0,
    time_limit      INTEGER,                            -- minutos, NULL = sem limite
    status          TEXT NOT NULL DEFAULT 'active',     -- active | completed | abandoned
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at        TEXT
);

-- ------------------------------------------------------------
-- Mensagens trocadas durante a sessão
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id          TEXT PRIMARY KEY,           -- msg_<uuid4 hex>
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,              -- user | assistant
    content     TEXT NOT NULL,
    audio_path  TEXT,                       -- caminho do arquivo de áudio (modo voz)
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- Métricas de fala (geradas após sessão em modo voz)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS speech_metrics (
    id                  TEXT PRIMARY KEY,   -- spm_<uuid4 hex>
    session_id          TEXT NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    wpm_average         REAL,
    filler_words_json   TEXT NOT NULL DEFAULT '{}',
    pause_analysis_json TEXT NOT NULL DEFAULT '{}',
    vocabulary_json     TEXT NOT NULL DEFAULT '{}',
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ------------------------------------------------------------
-- Feedbacks gerados pela IA ao final da sessão
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedbacks (
    id                  TEXT PRIMARY KEY,   -- fbk_<uuid4 hex>
    session_id          TEXT NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    overall_score       INTEGER NOT NULL DEFAULT 0,
    score_breakdown_json    TEXT NOT NULL DEFAULT '{}',
    strengths_json          TEXT NOT NULL DEFAULT '[]',
    improvements_json       TEXT NOT NULL DEFAULT '[]',
    action_plan_json        TEXT NOT NULL DEFAULT '[]',
    next_session_focus_json TEXT NOT NULL DEFAULT '[]',
    generated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);