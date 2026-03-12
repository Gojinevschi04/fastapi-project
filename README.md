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
| **OpenAI** | STT (Whisper), NLU (GPT-4o), TTS |
| **aiosmtplib** | Async email notifications |
| **Black + Ruff** | Code formatting & linting |

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

### Start the Application

```bash
# 1. Start PostgreSQL
make db.up       # starts Docker container + runs migrations

# 2. Seed templates (first time only)
make db.seed

# 3. (Optional) Seed demo users + tasks for testing
make db.seed.demo

# 4. Start the server
make app.start   # runs on http://localhost:8000
```

The API docs are available at `http://localhost:8000/docs` (Swagger UI).

### Common Commands

```bash
# Database
make db.up                              # Start PostgreSQL + run migrations
make db.down                            # Rollback all migrations
make db.make_migrations m='description' # Generate new Alembic migration
make db.seed                            # Seed dialog templates
make db.seed.demo                       # Seed demo users + tasks

# Code quality
make black.run    # Format code with Black
make ruff.run     # Lint + format with Ruff
make mypy.run     # Type checking

# Tests
pytest                     # Run all tests
pytest tests/unit/         # Unit tests only
pytest tests/integration/  # Integration tests only

# Server
make app.start    # Start Docker + migrations + server
make app.stop     # Stop everything
```

---

## Project Structure

```
app/
├── core/                     # Shared infrastructure
│   ├── config.py             # Pydantic BaseSettings (loads .env)
│   ├── database.py           # Async SQLAlchemy engine & session
│   ├── models.py             # BaseModel (id, created_at, updated_at)
│   ├── repositories.py       # Base repository class
│   ├── exceptions.py         # BaseServiceError
│   └── logging.py            # Logger setup
│
├── modules/                  # Feature modules (each follows Views → Service → Repository pattern)
│   ├── auth/                 # JWT authentication (login, register, refresh)
│   ├── users/                # User management + profile endpoints
│   ├── files/                # File upload/download
│   ├── tasks/                # Task CRUD + lifecycle (create, cancel, execute)
│   ├── templates/            # Dialog templates (admin CRUD)
│   ├── calls/                # Call sessions + transcript log lines
│   └── notifications/        # Post-call email notifications
│
├── integrations/             # External service adapters
│   ├── interfaces.py         # IVoiceProvider, ILLMProvider (abstract)
│   ├── twilio_adapter.py     # Twilio VoIP implementation
│   ├── openai_adapter.py     # OpenAI STT/TTS/NLU implementation
│   └── call_manager.py       # Call orchestrator (dialog loop)
│
├── scripts/
│   └── seed_templates.py     # Seed database with predefined templates
│
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

Each module in `app/modules/` follows this layered pattern:

| File | Role |
|------|------|
| `views.py` | HTTP endpoints, dependency injection |
| `service.py` | Business logic |
| `repository.py` | Database queries (async, user-scoped) |
| `models.py` | SQLModel ORM entities |
| `schema.py` | Pydantic request/response schemas |
| `exceptions.py` | Custom errors |

---

## API Endpoints

### Auth (`/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT tokens |
| POST | `/auth/refresh` | Refresh access token |

### Users (`/users`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/me` | Get current user profile |
| PUT | `/users/me` | Update profile (email, phone) |
| POST | `/users/me/change-password` | Change password |

### Tasks (`/tasks`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tasks/` | Create a new call task |
| GET | `/tasks/` | List tasks (with filters & pagination) |
| GET | `/tasks/{id}` | Get task detail |
| GET | `/tasks/stats` | Get task counts by status |
| POST | `/tasks/{id}/cancel` | Cancel a pending/scheduled task |
| POST | `/tasks/{id}/execute` | Trigger task execution |

### Templates (`/templates`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/templates/` | List all templates |
| GET | `/templates/{id}` | Get template detail |
| POST | `/templates/` | Create template (admin) |
| PUT | `/templates/{id}` | Update template (admin) |
| DELETE | `/templates/{id}` | Delete template (admin) |

### Calls (`/calls`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/calls/tasks/{id}/transcript` | Get call transcript |
| GET | `/calls/tasks/{id}/session` | Get call session info |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS` | PostgreSQL connection |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | JWT auth config |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | Twilio VoIP |
| `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE`, `OPENAI_STT_MODEL` | OpenAI AI services |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Email (SMTP) |
| `EMAIL_FROM`, `EMAIL_FROM_NAME`, `EMAIL_ENABLED` | Email sender config |
| `BASE_URL` | Backend base URL |
| `LOG_LEVEL` | Logging level (default: INFO) |

See `.env.example` for defaults.

---

## Connecting with the Frontend

1. Start this backend on `http://localhost:8000`
2. In the frontend repo, set `VITE_API_URL=http://localhost:8000` in `.env`
3. Start the frontend with `npm run dev` — it runs on `http://localhost:5173`

The frontend communicates with all endpoints listed above via Axios with JWT Bearer authentication.
