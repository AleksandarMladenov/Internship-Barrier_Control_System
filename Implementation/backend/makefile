# -------- config --------
COMPOSE_DIR := ops
ENV_FILE    := .env
DC := docker compose -f $(COMPOSE_DIR)/docker-compose.yml --env-file $(ENV_FILE)

APP_PORT ?= 8000

# -------- helpers --------
.PHONY: help
help:
	@echo "Targets:"
	@echo "  up            - build & start api + db"
	@echo "  up-db         - start db only"
	@echo "  down          - stop & remove containers"
	@echo "  reset         - stop + remove containers & volumes"
	@echo "  ps            - show containers"
	@echo "  logs          - tail api logs"
	@echo "  migrate       - alembic upgrade head (inside api)"
	@echo "  revision m=.. - alembic autogenerate (inside api)"
	@echo "  psql          - open psql inside db container"
	@echo "  port          - show host port for api:8000"
	@echo "  health        - curl API /health"
	@echo "  docs          - print docs URL"
	@echo "  open-docs     - open docs in browser (macOS)"

# -------- docker lifecycle --------
.PHONY: up
up:
	$(DC) up -d --build

.PHONY: up-db
up-db:
	$(DC) up -d db

.PHONY: down
down:
	$(DC) down

.PHONY: reset
reset:
	$(DC) down -v

.PHONY: ps
ps:
	$(DC) ps

.PHONY: logs
logs:
	$(DC) logs -f api

# -------- alembic --------
.PHONY: migrate
migrate:
	$(DC) exec api alembic -c /app/alembic.ini upgrade head

.PHONY: revision
revision:
	@test "$(m)" != "" || (echo "Usage: make revision m=\"your message\""; exit 1)
	$(DC) exec api alembic -c /app/alembic.ini revision --autogenerate -m "$(m)"

# -------- db shell --------
.PHONY: psql
psql:
	# env vars come from $(ENV_FILE) and are present inside the db container
	$(DC) exec db psql -U $$POSTGRES_USER -d $$POSTGRES_DB

# -------- quick access / URLs --------
.PHONY: port
port:
	$(DC) port api 8000 || true

.PHONY: health
health:
	@curl -i http://localhost:$(APP_PORT)/health || true

.PHONY: docs
docs:
	@echo "Docs: http://localhost:$(APP_PORT)/docs"

.PHONY: open-docs
open-docs:
	@open "http://localhost:$(APP_PORT)/docs"
