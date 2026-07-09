.PHONY: help venv install up down logs mongo psql scrape-test serve fmt

help:
	@echo "Comandos disponibles:"
	@echo "  make venv         Crea entorno virtual .venv"
	@echo "  make install      Instala dependencias y Chromium para Playwright"
	@echo "  make up           Levanta Docker (Mongo, Postgres, MLflow)"
	@echo "  make down         Baja Docker"
	@echo "  make mongo        Abre shell de MongoDB"
	@echo "  make psql         Abre shell de PostgreSQL"
	@echo "  make scrape-test  Ejecuta scraper de prueba contra Idealista"
	@echo "  make serve        Arranca la API FastAPI en modo dev"
	@echo "  make fmt          Formatea con ruff"

venv:
	python -m venv .venv

install:
	.venv/bin/pip install -U pip
	.venv/bin/pip install -r requirements.txt
	.venv/bin/playwright install chromium

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

mongo:
	docker exec -it housing-mongo mongosh -u admin -p admin

psql:
	docker exec -it housing-postgres psql -U housing -d housing

scrape-test:
	PYTHONPATH=src .venv/bin/python -m housing.scraper.idealista

serve:
	PYTHONPATH=src .venv/bin/uvicorn housing.api.main:app --reload --port 8000

fmt:
	.venv/bin/ruff check --fix src tests
	.venv/bin/ruff format src tests
