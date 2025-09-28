"""Django app config for UCL context models"""
from django.apps import AppConfig


class ContextConfig(AppConfig):
    """Configuration for context app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'driven.db.context'
    label = 'context'