#!/bin/bash

# Run FastAPI with uvicorn
echo "Starting FastAPI application with uvicorn..."

# Set environment variables
export DJANGO_SETTINGS_MODULE=config.settings.staticfiles

# Run with uvicorn
uvicorn config.asgi:application --host 0.0.0.0 --port 8002 --reload --log-level info