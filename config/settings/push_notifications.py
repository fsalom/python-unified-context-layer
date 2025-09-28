import firebase_admin
from firebase_admin import credentials

from .base import *

try:
    cred = credentials.Certificate(
        str(BASE_DIR) + '/' + os.environ.get('FIREBASE_CREDENTIALS', '')
    )
    firebase_admin.initialize_app(cred)
except Exception:
    os.environ['USE_PUSH_NOTIFICATIONS'] = "0"
