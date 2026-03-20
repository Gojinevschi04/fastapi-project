# Quiet Call AI — Backend

FastAPI async backend for **Quiet Call AI**, a voice assistant SaaS that automates repetitive phone calls using AI (OpenAI for STT/NLU/TTS, Twilio for VoIP).

Frontend repository: [quiet-call-ai-frontend](https://disa.codestorage.space/ana.gojinevschi/quiet-call-ai-frontend)

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.13** | Language |
| **FastAPI** | Async web framework |
| **SQLModel + SQLAlchemy** | ORM (async, with asyncpg driver) |
| **PostgreSQL** | Database (via Docker) |
| **Alembic** | Database migrations |
| **Poetry** | Dependency management |
| **PyJWT** | JWT authentication (HS256) |
| **Twilio** | VoIP — initiate and manage phone calls |
| **OpenAI** | STT (Whisper), NLU (GPT-4o-mini), TTS (nova voice) |
| **edge-tts** | Demo audio generation with neural voices |
| **aiosmtplib** | Async email notifications (7 branded templates) |
| **WebSocket** | Real-time call status updates |
| **Black + Ruff** | Code formatting & linting |

---

## Features

- **Automated phone calls** — AI-driven dialog via Twilio VoIP + OpenAI
- **Webhook-driven call flow** — `say_and_gather()` with Twilio `<Gather>` for speech collection
- **Multi-language support** — English, Russian, Romanian (templates, emails, TTS)
- **Real-time call monitoring** — WebSocket endpoint streams live call events to connected clients
- **Background task execution** — calls run asynchronously, instant API response
- **Scheduled calls** — worker process auto-executes tasks at `scheduled_time`
- **Auto-retry** — failed tasks retry with exponential backoff
- **Local recording storage** — recordings downloaded from Twilio post-call for fast playback
- **CSV export** — users can export their tasks as CSV
- **Notification preferences** — users can toggle email notifications on/off
- **Post-call processing** — AI summary generation, email notification, recording archival (parallel)
- **Admin panel** — system stats, user management (role toggle, delete), all tasks view
- **Rate limiting** — per-IP request throttling
- **569 tests** — unit + integration, 87% coverage

---

## Getting Started

### Prerequisites

- **Python 3.13**
- **Poetry** (`pip install poetry`)
- **Docker** (for PostgreSQL)

### Installation

```bash
# Clone the repo
git clone https://disa.codestorage.space/ana.gojinevschi/quiet-call-ai.git
cd quiet-call-ai

# Install dependencies
poetry install

# Create environment file and fill in your credentials
cp .env.example .env
```

### Start with Docker (recommended)

```bash
# Start everything (Postgres + API + Worker)
make app.start

# Run migrations
make db.up

# Seed templates (first time only)
make db.seed

# (Optional) Seed demo users + tasks for testing
make db.seed.demo
```

This starts 3 containers:
- **qc_api** — FastAPI server at `http://localhost:8000`
- **qc_worker** — Background task scheduler
- **qc_postgres** — PostgreSQL database

API docs: `http://localhost:8000/docs`

### Start locally (without Docker)

```bash
# Start PostgreSQL container only
docker compose up qc_postgres -d

# Run migrations
make db.up

# Start the server
poetry run python -m app.main

# (In another terminal) Start the worker
poetry run python -m app.worker
```

### Common Commands

```bash
# Docker
make app.start              # Build and start all containers
make app.stop               # Stop all containers
make app.logs               # Follow logs from all containers
make app.logs.api           # Follow API logs only
make app.logs.worker        # Follow worker logs only
make app.test               # Run tests in Docker container

# Database
make db.up                              # Run migrations
make db.down                            # Rollback all migrations
make db.make_migrations m='description' # Generate new Alembic migration
make db.seed                            # Seed dialog templates
make db.seed.demo                       # Seed demo users + tasks

# Code quality
make black.run    # Format code with Black
make ruff.run     # Lint + format with Ruff
make mypy.run     # Type checking

# Tests
poetry run pytest                      # Run all 569 tests
poetry run pytest tests/unit/          # Unit tests only
poetry run pytest tests/integration/   # Integration tests only
```

---

## Project Structure

```
app/
├── core/                     # Shared infrastructure
│   ├── config.py             # Pydantic BaseSettings (loads .env)
│   ├── constants.py          # Shared constants (timeouts, limits, headers)
│   ├── database.py           # Async SQLAlchemy engine & session
│   ├── models.py             # BaseModel (id, created_at, updated_at)
│   ├── repositories.py       # Base repository class
│   ├── exceptions.py         # BaseServiceError
│   ├── ws_manager.py         # WebSocket event broadcaster (call events pub/sub)
│   ├── audio.py              # Demo audio generation (edge-tts, WAV fallback)
│   ├── retry.py              # @async_retry decorator (exponential backoff)
│   ├── logging.py            # Logger setup
│   ├── middleware.py          # Request logging middleware
│   └── rate_limit.py         # Per-IP rate limiting middleware
│
├── modules/                  # Feature modules (Views → Service → Repository)
│   ├── auth/                 # JWT auth (login, register, refresh, password reset)
│   ├── users/                # User CRUD + profile + notification preferences
│   ├── files/                # File upload/download (generic storage)
│   ├── tasks/                # Task CRUD + lifecycle + CSV export
│   ├── templates/            # Dialog templates (admin CRUD, multi-language)
│   ├── calls/                # Call sessions, transcripts, recordings, WebSocket
│   ├── admin/                # System stats, user/task management
│   ├── scheduler/            # Task executor (scheduled + retry logic)
│   ├── notifications/        # Email service (7 templates) + post-call processor
│   ├── feedback/             # Contact form → email forwarding
│   └── webhooks/             # Twilio callback handlers
│
├── integrations/             # External service adapters
│   ├── interfaces.py         # IVoiceProvider, ILLMProvider (abstract)
│   ├── twilio_adapter.py     # Twilio VoIP (call, gather, hangup, recording)
│   ├── openai_adapter.py     # OpenAI STT/TTS/NLU (Whisper, nova, GPT-4o-mini)
│   ├── call_manager.py       # Call orchestrator (dialog loop + WS events)
│   ├── conversation.py       # Dialog state manager (turns, intents, history)
│   └── prompt_builder.py     # System prompt construction
│
├── scripts/
│   ├── seed_templates.py     # Seed 20+ dialog templates (en/ru/ro)
│   ├── seed_demo.py          # Seed demo users + tasks
│   └── constants.py          # Seed data constants
│
├── worker.py                 # Background scheduler process
└── main.py                   # FastAPI app factory + router registration

migrations/                   # Alembic migrations
tests/
├── unit/                     # Unit tests (mocked DB sessions)
└── integration/              # Integration tests (HTTP client, patched services)
```

---

## Architecture

```
Client (FE) → FastAPI Router (views.py)
                   ↓
              Service (service.py) — business logic
                   ↓
              Repository (repository.py) — data access
                   ↓
              SQLModel / PostgreSQL
```

### Call Execution Flow

```
User clicks Execute → POST /tasks/{id}/execute (returns immediately)
  ↓ (background)
CallManager.execute_task()
  → Set status IN_PROGRESS + emit WS event
  → TwilioAdapter.initiate_call() → wait for answer
  → LLM generates opening → say_and_gather() → Twilio speaks + collects speech
  → Dialog loop (max 10 turns):
      STT → intent detection → LLM response → TTS → gather next speech
      (each turn emits WS "message" event)
  → Hangup → generate summary → update task status
  → PostCallProcessor: save recording locally + send email + archive logs
```

### WebSocket Events

Connect: `ws://host/ws/calls/{task_id}?token=JWT`

| Event | Data | When |
|-------|------|------|
| `status_change` | `{status}` | Task moves to IN_PROGRESS |
| `dialing` | `{phone}` | Call initiated |
| `call_answered` | — | Interlocutor picks up |
| `message` | `{speaker, text, intent?}` | Each dialog turn |
| `generating_summary` | — | Call ended, AI summarizing |
| `call_ended` | `{status, summary, error_reason}` | Final result |

---

## API Endpoints (48 total)

### Auth (`/auth`) — Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/reset-password` | Request password reset email |
| POST | `/auth/reset-password/confirm` | Confirm password reset |

### Users (`/users`) — Authenticated
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me` | Get profile (includes `email_notifications` pref) |
| PUT | `/users/me` | Update profile (email, phone, notification toggle) |
| POST | `/users/me/change-password` | Change password (requires reauth) |

### Tasks (`/tasks`) — Authenticated
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tasks/` | Create a new call task |
| GET | `/tasks/` | List tasks (status filter, pagination) |
| GET | `/tasks/export` | Export tasks as CSV download |
| GET | `/tasks/stats` | Task counts by status |
| GET | `/tasks/{id}` | Task detail (includes `template_name`) |
| PUT | `/tasks/{id}` | Edit pending/scheduled task |
| POST | `/tasks/{id}/cancel` | Cancel task (admin can cancel any) |
| POST | `/tasks/{id}/execute` | Execute task (non-blocking, admin can execute any) |

### Calls (`/tasks`) — Authenticated
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks/{id}/transcript` | Structured transcript (session + log lines) |
| GET | `/tasks/{id}/transcript/download` | Download transcript as .txt |
| GET | `/tasks/{id}/session` | Call session metadata |
| GET | `/tasks/{id}/recording` | Stream/download recording (local or Twilio) |

### Templates (`/templates`) — Mixed
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/templates/` | List all active templates |
| GET | `/templates/{id}` | Template detail |
| POST | `/templates/` | Create template (admin) |
| PUT | `/templates/{id}` | Update template (admin) |
| DELETE | `/templates/{id}` | Soft-delete template (admin) |

### Admin (`/admin`) — Admin only
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/stats` | System stats (users, tasks, calls) |
| GET | `/admin/users` | List users (paginated) |
| GET | `/admin/tasks` | List all tasks (paginated, status filter) |
| PUT | `/admin/users/{id}` | Update user role |
| DELETE | `/admin/users/{id}` | Delete user (cascade) |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `ws /ws/calls/{task_id}?token=JWT` | Real-time call status events |

### Other — Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/feedback/` | Submit feedback (emailed to admins) |
| GET | `/health` | Health check |
| POST | `/webhooks/calls/{id}` | Twilio initial callback |
| POST | `/webhooks/calls/{id}/gather` | Twilio speech result |
| POST | `/webhooks/calls/{id}/status` | Twilio call status |
| POST | `/webhooks/calls/{id}/recording` | Twilio recording URL |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS` | PostgreSQL connection |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | JWT auth config |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | Twilio VoIP |
| `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE`, `OPENAI_STT_MODEL` | OpenAI services |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Email (SMTP) |
| `EMAIL_FROM`, `EMAIL_FROM_NAME`, `EMAIL_ENABLED` | Email sender config |
| `FEEDBACK_EMAILS` | Comma-separated emails for feedback forwarding |
| `BASE_URL` | Backend base URL (for Twilio callbacks) |
| `FRONTEND_URL` | Frontend URL (for email links) |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) |
| `RATE_LIMIT_PER_MINUTE` | API rate limit per IP (default: 60) |
| `LOG_LEVEL` | Logging level (default: INFO) |

See `.env.example` for defaults.

---

## Docker Architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  qc_frontend │  │   qc_api     │  │  qc_worker   │
│  (nginx:80)  │  │ (uvicorn:8K) │  │ (scheduler)  │
│  port 3000   │  │  port 8000   │  │  background  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       └────────┬────────┴──────────────────┘
                │
        ┌───────▼───────┐
        │  qc_postgres  │
        │  (port 5432)  │
        └───────────────┘
```

---

## Connecting with the Frontend

**With Docker:**
```bash
# Backend (this repo)
make app.start

# Frontend (quiet-call-ai-frontend repo)
make docker.start    # runs at http://localhost:3000
```

**Local development:**
```bash
# Backend
make app.start       # or: poetry run python -m app.main

# Frontend
npm run dev          # runs at http://localhost:5173
```

Demo accounts (after `make db.seed.demo`):
- Admin: `ana.gojinevschi@isa.utm.md` / `admin1234`
- Admin: `annagojinevschi@gmail.com` / `admin1234`
