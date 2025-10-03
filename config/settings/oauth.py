import os

from oauth2_provider.settings import oauth2_settings

from .push_notifications import *

# from .base import *


# https://django-oauth-toolkit.readthedocs.io/en/latest/index.html

INSTALLED_APPS += [
    'oauth2_provider',
    'corsheaders',
]

MIDDLEWARE += [
    'corsheaders.middleware.CorsMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
    'commons_package.commons.backends.EmailBackend',
]

OAUTH2_PROVIDER = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': 3600,
    'APPLICATION_MODEL': 'oauth2_provider.Application',
    'REFRESH_TOKEN_EXPIRE_SECONDS': 3600,
    'ROTATE_REFRESH_TOKENS': True,
}

# https://medium.com/codex/google-sign-in-rest-api-with-python-social-auth-and-django-rest-framework-4d087cd6d47f
# https://python-social-auth.readthedocs.io/en/latest/configuration/django.html

INSTALLED_APPS += [
    'social_django',
]

AUTHENTICATION_BACKENDS += [
    'social_core.backends.google.GoogleOAuth2',
]

# https://developers.google.com/oauthplayground/

#SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
#SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')

# APPLE_PRIVATE_KEY = BASE_DIR / os.environ.get('APPLE_PRIVATE_KEY')

oauth2_settings.defaults['ALLOWED_REDIRECT_URI_SCHEMES'] = [
    'http',
    'https',
    #os.environ.get('APP_DEEP_LINK_DOMAIN'),
]
