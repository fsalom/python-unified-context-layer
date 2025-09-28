.PHONY: help install update linters migrate createsuperuser run-django run-fastapi run-both kill-servers clean

help:
	@echo "Portfolio API - Hexagonal Architecture"
	@echo "Available commands:"
	@echo "  install        - Install dependencies"
	@echo "  update         - Update dependencies"
	@echo "  migrate        - Run Django migrations"
	@echo "  createsuperuser - Create Django superuser"
	@echo "  run-django     - Run Django development server (port 8001)"
	@echo "  run-fastapi    - Run FastAPI development server (port 8000)"
	@echo "  run-both       - Run both servers in parallel"
	@echo "  kill-servers   - Kill processes running on ports 8000 and 8001"
	@echo "  clean          - Clean up generated files"


install:
	@echo "Installing dependencies..."
	. scripts/install_private_repositories.sh
	uv sync

update:
	@echo "Updating dependencies..."
	uv sync --upgrade

linters:
	@echo "Running linters..."
	. scripts/run_linters.sh .

migrate:
	@echo "Running Django migrations..."
	python manage.py makemigrations
	python manage.py migrate

createsuperuser:
	@echo "Creating Django superuser..."
	python manage.py createsuperuser

run-django:
	@echo "Starting Django development server..."
	@bash scripts/run_django.sh $(SERVER_MODE)

run-fastapi:
	@echo "Starting FastAPI development server..."
	. scripts/run_fastapi.sh

run-both:
	@echo "Starting both servers..."
	@echo "Django admin: http://localhost:8003/admin"
	@echo "FastAPI: http://localhost:8002"
	@echo "FastAPI docs: http://localhost:8002/docs"
	. scripts/run_both.sh

kill-servers:
	@echo "Killing processes on ports 8002 and 8003..."
	@lsof -ti:8002 | xargs -r kill -9 2>/dev/null || echo "No process found on port 8002"
	@lsof -ti:8003 | xargs -r kill -9 2>/dev/null || echo "No process found on port 8003"
	@echo "Done!"

clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f db.sqlite3 