from celery.schedules import crontab

from .oauth import *

# Celery
BROKER_TRANSPORT = "redis"
CELERY_BROKER_URL = f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:6379/0"
CELERY_RESULT_BACKEND = f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:6379/0"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Europe/Madrid"
CELERY_ENABLE_UTC = True


# https://docs.celeryq.dev/en/latest/userguide/periodic-tasks.html
CELERY_BEAT_SCHEDULE = {}
