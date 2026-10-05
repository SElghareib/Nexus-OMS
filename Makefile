# Nexus OMS Makefile
# Standardized developer commands

.PHONY: up down seed logs test clean build restart

# Start all services
up:
	docker compose up -d

# Stop and remove all containers
down:
	docker compose down

# Seed the database with dummy data
seed:
	docker compose exec nexus-backend python -m app.db.seed

# Stream logs from all services
logs:
	docker compose logs -f

# Run backend tests
test:
	docker compose exec nexus-backend pytest

# Build all containers
build:
	docker compose build

# Restart all services
restart:
	docker compose restart

# Clean up volumes (WARNING: deletes all data)
clean:
	docker compose down -v

# Initialize environment
init:
	cp .env.example .env
	@echo "Environment file created. Please edit .env with your configuration."

# Run migrations (if using Alembic)
migrate:
	docker compose exec nexus-backend alembic upgrade head

# Show running containers
ps:
	docker compose ps

# Open shell in backend container
shell:
	docker compose exec nexus-backend bash

# Open shell in frontend container
frontend-shell:
	docker compose exec nexus-frontend bash
