from .i18n import *

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "": "commons_package.commons.classes.JSONFormatter",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "info": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "error": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
