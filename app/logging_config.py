import logging
from pydantic import BaseModel

class JsonFormatter(logging.Formatter):
    """
    Custom formatter to output log records as JSON.
    """
    def format(self, record):
        log_object = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_object['exc_info'] = self.formatException(record.exc_info)
        return str(log_object).replace("'", '"')

class LogConfig(BaseModel):
    """Logging configuration to be set for the server"""

    LOGGER_NAME: str = "proxmox_api"
    LOG_LEVEL: str = "DEBUG"

    # Logging config
    version: int = 1
    disable_existing_loggers: bool = False
    formatters: dict = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s | %(asctime)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "app.logging_config.JsonFormatter",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    }
    handlers: dict = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "file_json": {
            "formatter": "json",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "app.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
        },
    }
    loggers: dict = {
        LOGGER_NAME: {"handlers": ["default", "file_json"], "level": LOG_LEVEL},
    }
