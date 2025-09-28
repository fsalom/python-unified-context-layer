from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'driven.db.users'
    label = 'users'

    def ready(self):
        """Required by Django to detect models and make migrations"""
        from .models import UserDBO  # noqa
