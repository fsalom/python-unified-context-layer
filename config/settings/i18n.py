import importlib.resources as pkg_resources

from .tasks import *

MIDDLEWARE.append('django.middleware.locale.LocaleMiddleware')
LOCALE_PATHS = [
    BASE_DIR / 'locale',
    str(pkg_resources.files("commons_package").joinpath("locale")),
]
USE_I18N = True
USE_L10N = True
ugettext = lambda s: s
LANGUAGES = (
    ('es', ugettext('Spanish')),
    ('en', ugettext('English')),
)
