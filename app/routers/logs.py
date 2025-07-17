import logging
from logging.config import dictConfig
import sys
import json
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'line': record.lineno,
            'message': record.getMessage()
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)


log_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        # 'default': {
        #     'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        #     'datefmt': '%Y-%m-%d %H:%M:%S',
        # },
        'json': {
            '()': JsonFormatter
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            # 'formatter': 'default',
            'formatter': 'json',
            'stream': 'ext://sys.stdout',
        },
        # 'file': {
        #     'class': 'logging.FileHandler',
        #     'level': 'INFO',
        #     # 'formatter': 'default',
        #     'formatter': 'json',
        #     'filename': 'routs.log',
        #     'mode': 'a',
        # },
        'rotating_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'json',
            'filename': 'logs/main.log',
            'maxBytes': 10485760, # 10MB
            'backupCount': 5,
        },
        # "time_rotating_file": {
        #     "class": "logging.handlers.TimedRotatingFileHandler",
        #     "level": "INFO",
        #     "formatter": "json",
        #     "filename": "fastapi.log",
        #     "when": "midnight",
        #     "interval": 1,
        #     "backupCount": 7,
        # },
    },
    'loggers': {
        'main': {
            'handlers': ['rotating_file'],
            'level': 'INFO',
            'propagate': False
        },
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

dictConfig(log_config)

# Создание кастомного логгера
# routs_logger = logging.getLogger('routs')

main_logger = logging.getLogger('main')