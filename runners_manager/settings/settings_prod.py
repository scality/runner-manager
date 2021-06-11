import logging.config

FILE_LOG_LEVEL = "WARNING"
DEFAULT_LOG_LEVEL = "INFO"
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'level': FILE_LOG_LEVEL,
            'filename': '/var/log/openstack_runner.log',
            'maxBytes': 1024 * 1000,
            'backupCount': 20
        },
    },
    "loggers": {
        '': {
            "handlers": ["default", "file"],
            'level': DEFAULT_LOG_LEVEL,
            'propagate': True
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
