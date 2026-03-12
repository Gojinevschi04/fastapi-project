.PHONY: help db.make_migrations db.up db.down black.run ruff.run mypy.run app.start app.stop

.DEFAULT_GOAL := help

help:
	@echo "RAG Web Application - Makefile"
	@echo "usage: make COMMAND"
	@echo ""
	@echo "Database Commands:"
	@echo "  db.make_migrations    Generate new migration file (requires m='message')"
	@echo "                        Example: make db.make_migrations m='Add user table'"
	@echo "  db.up                 Run all pending migrations"
	@echo "  db.down               Rollback all migrations to base"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  black.run             Format Python code with Black"
	@echo "  ruff.run              Lint and format code with Ruff"
	@echo "  mypy.run              Type check code with MyPy"
	@echo ""
	@echo "Application Commands:"
	@echo "  app.start             Start Docker containers, API server"
	@echo "  app.stop              Stop all Docker containers and running processes"
	@echo ""
	@echo "Examples:"
	@echo "  make db.up                                    # Run migrations"
	@echo "  make db.make_migrations m='Add user table'   # Create migration"
	@echo "  make app.start                                # Start entire application"
	@echo "  make black.run                                # Format code"

db.make_migrations:
	@poetry run alembic revision --autogenerate -m "$(m)"

db.up:
	@poetry run alembic upgrade head

db.down:
	@poetry run alembic downgrade base

db.seed:
	@poetry run python -m app.scripts.seed_templates


black.run:
	@poetry run black app

ruff.run:
	@poetry run ruff check app --fix && poetry run ruff format app

mypy.run:
	@poetry run mypy app

app.start:
	@docker network inspect external_network >/dev/null 2>&1 || docker network create external_network
	@docker compose up -d
	@echo "Running migrations..."
	@make db.up
	@echo "Starting API server on http://localhost:8000 ..."
	@poetry run python -m app.main

app.stop:
	@echo "Stopping Docker containers..."
	-@docker compose down
	@echo "Stopping API server..."
	-@pkill -f "uvicorn app.main:app" 2>/dev/null || true
	@echo "All processes stopped."