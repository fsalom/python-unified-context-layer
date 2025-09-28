from .custom_logging import *

INSTALLED_APPS += ['storages']

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', "")
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', "")
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', "")
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL', "")
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_S3_SIGNATURE_VERSION = "s3v4"


if bool(int(os.environ.get('DEBUG', "0"))):
    STATIC_URL = '/static/'
else:
    STATIC_URL = '{}/{}/'.format(os.environ.get('AWS_S3_ENDPOINT_URL', ""), 'static')
    STORAGES = {
        "default": {
            "BACKEND": "commons_package.commons.custom_storages.MediaStorage",
        },
        "staticfiles": {
            "BACKEND": "commons_package.commons.custom_storages.StaticStorage",
        },
    }

MEDIA_URL = '{}/{}/'.format(os.environ.get('AWS_S3_ENDPOINT_URL', "0"), 'media')
