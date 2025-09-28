"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.staticfiles')

# Initialize Django ASGI application early to ensure the AppRegistry is populated
django_asgi_app = get_asgi_application()

# Import FastAPI app after Django is set up
from driving.api.fastapi_app import fastapi_app

# Create main ASGI application using Starlette that properly handles both Django and FastAPI
application = Starlette(
    routes=[
        Mount("/", app=fastapi_app),
        # Mount("/users/admin", app=django_asgi_app),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ],
)
