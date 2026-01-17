"""Logging configuration."""
import logging
import sys
from typing import Optional

_loggers = {}


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Configure and return logger."""
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    _loggers[name] = logger

    return logger


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get existing logger or create new one."""
    if name in _loggers:
        return _loggers[name]

    return setup_logger(name, level or "INFO")
