import os
import logging
import structlog
from logging.handlers import RotatingFileHandler
from app.config import settings

LOG_DIR = "logs"
SERVICE_NAME = os.getenv("SERVICE_NAME", "app")
LOG_FILE = f"{SERVICE_NAME}.log"

_LOGGING_CONFIGURED = False


def _configure_logging():
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    root_logger = logging.getLogger()

    # Prevent duplicate handlers (pytest, reloads, imports)
    if root_logger.handlers:
        _LOGGING_CONFIGURED = True
        return

    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, LOG_FILE)

    root_logger.setLevel(logging.INFO)
    root_logger.propagate = False

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(file_handler)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            structlog.processors.JSONRenderer()
            if settings.log_format == "json"
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    _LOGGING_CONFIGURED = True


def get_logger(name: str):
    _configure_logging()
    return structlog.get_logger(name)
