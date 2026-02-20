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


black.run:
	@poetry run black app

ruff.run:
	@poetry run ruff check app --fix && poetry run ruff format app

mypy.run:
	@poetry run mypy app

app.start:
	@docker network inspect external_network >nul 2>&1 || docker network create external_network
	@docker-compose up -d
	@echo "Starting API server in background..."
	@make db.up
	@poetry run python -m app.main &

app.stop:
	@echo Stopping Docker containers...
	-@for /f %%i in ('docker ps -aq') do docker stop %%i
	-@for /f %%i in ('docker ps -aq') do docker rm %%i
	@echo Stopping API server...
	-@taskkill /F /IM python.exe >nul 2>&1
	@echo All processes stopped.