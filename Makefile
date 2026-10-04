.PHONY: frontend
.PHONY: help install lint format typecheck test eval clean run-backend up down

PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin

help:
	@echo "FinSentry Developer Commands:"
	@echo "  make install     - Setup virtual environment and install dependencies"
	@echo "  make lint        - Run ruff linter checks"
	@echo "  make format      - Automatically format code with ruff"
	@echo "  make typecheck   - Run strict static type checking with mypy"
	@echo "  make test        - Run unit and integration tests"
	@echo "  make eval        - Execute DeepEval CI regression benchmark"
	@echo "  make up          - Start local Qdrant and Redis via Docker Compose"
	@echo "  make down        - Stop local Docker infrastructure"
	@echo "  make run-backend - Launch the FastAPI application with auto-reload"

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e "backend/[dev]"

lint:
	$(BIN)/ruff check backend/

format:
	$(BIN)/ruff format backend/
	$(BIN)/ruff check --fix backend/

typecheck:
	$(BIN)/mypy backend/app

test:
	$(BIN)/pytest backend/tests/ -v --cov=backend/app --cov-report=term-missing

eval:
	$(BIN)/pytest backend/evals/ -v -s

up:
	docker compose up -d

down:
	docker compose down

run-backend:
	cd backend && ../$(BIN)/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

frontend:
	@echo "Starting FinSentry Streamlit Dashboard..."
	.venv/bin/streamlit run frontend/app.py --server.port 8501

.PHONY: run
run:
	@echo "Starting FinSentry FastAPI Gateway on port 8000..."
	PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
