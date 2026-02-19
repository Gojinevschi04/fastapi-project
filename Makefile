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
	@echo "  app.start             Start Docker containers, API server, and client dev server"
	@echo "  app.stop              Stop all Docker containers and running processes"
	@echo ""
	@echo "Examples:"
	@echo "  make db.up                                    # Run migrations"
	@echo "  make db.make_migrations m='Add user table'   # Create migration"
	@echo "  make app.start                                # Start entire application"
	@echo "  make black.run                                # Format code"


db.make_migrations:
	@uv run alembic revision --autogenerate -m "$(m)"

db.up:
	@uv run alembic upgrade head

black.run:
	@uv run black app

ruff.run:
	@uv run ruff check app --fix && uv run ruff format app

mypy.run:
	@uv run mypy app

db.down:
	@uv run alembic downgrade base

app.start:
	@docker network create external_network || true
	@docker-compose up -d
	@echo "Starting API server in background..."
	@make db.up
	@cd api && uv run python -m app.main &
	@echo "Starting client development server..."
	@cd client && npm run dev

app.stop:
	@echo "Stopping Docker containers..."
	-@docker stop $$(docker ps -aq) 2>/dev/null
	-@docker rm $$(docker ps -aq) 2>/dev/null
	@echo "Stopping API and client servers..."
	-@pkill -f "python -m app.main" 2>/dev/null
	-@pkill -f "npm run dev" 2>/dev/null
	-@pkill -f "vite" 2>/dev/null
	@echo "All processes stopped."
