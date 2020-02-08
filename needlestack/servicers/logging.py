import logging
import logging.handlers

from needlestack.servicers.settings import BaseConfig


def configure_logger(config: BaseConfig):
    """Configure the base logger using a configuration class.
    Sets the log level, debug handler, and file handler.

    Args:
        config: Config class that defines how to log
    """
    logger = logging.getLogger()
    logger.setLevel(config.LOG_LEVEL)

    if config.DEBUG:
        handler = get_debug_handler(config.DEBUG_LOG_FORMAT, config.LOG_FORMAT_DATE)
        logger.addHandler(handler)

    if config.LOG_FILE:
        handler = get_file_handler(
            config.LOG_FILE_LOG_FORMAT,
            config.LOG_FORMAT_DATE,
            config.LOG_FILE,
            config.LOG_FILE_MAX_BYTES,
            config.LOG_FILE_BACKUPS,
        )
        logger.addHandler(handler)


def get_debug_handler(fmt: str, datefmt: str):
    """Get a debug stdout logging handler

    Args:
        fmt: Logging format string
        datefmt: Date format
    """
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt, datefmt))
    return handler


def get_file_handler(
    fmt: str, datefmt: str, log_file: str, max_bytes: int, backup_count: int
):
    """Get a rotating file logging handler

    Args:
        fmt: Logging format string
        datefmt: Date format
        log_file: Path to log file
        max_bytes: Number of builts per log file
        backup_count: Number of log files to keep in rotation
    """
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(fmt, datefmt))
    return handler
