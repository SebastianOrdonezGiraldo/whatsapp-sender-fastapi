.PHONY: help install dev worker test lint format clean docker-up docker-down migrate

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Instalar dependencias
	poetry install

dev: ## Iniciar servidor de desarrollo
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker: ## Iniciar worker de RQ
	rq worker --with-scheduler

worker-campaigns: ## Iniciar worker para campañas
	rq worker campaigns --with-scheduler

worker-messages: ## Iniciar worker para mensajes
	rq worker messages --with-scheduler

test: ## Ejecutar tests
	pytest

lint: ## Ejecutar linter
	ruff check app/
	black --check app/

format: ## Formatear código
	black app/
	ruff check --fix app/

clean: ## Limpiar archivos temporales
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +

docker-up: ## Iniciar servicios con Docker Compose
	docker-compose up -d

docker-down: ## Detener servicios de Docker Compose
	docker-compose down

migrate: ## Ejecutar migraciones
	alembic upgrade head

migrate-create: ## Crear nueva migración (usa: make migrate-create NAME=nombre_migracion)
	alembic revision --autogenerate -m "$(NAME)"

db-reset: ## Resetear base de datos (CUIDADO: borra todos los datos)
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 5
	alembic upgrade head

