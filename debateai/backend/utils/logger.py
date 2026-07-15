"""
Centralised logging configuration using loguru.

Every module should import the logger from here so that sink
configuration is applied once and consistently across the application.

Usage:
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
"""

import sys
from loguru import logger as _base_logger

# Remove the default loguru handler so we can apply our own format.
_base_logger.remove()

_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# Console sink — INFO and above by default.
_base_logger.add(
    sys.stderr,
    format=_LOG_FORMAT,
    level="INFO",
    colorize=True,
    backtrace=True,
    diagnose=True,
)


def get_logger(name: str):
    """
    Return a loguru logger bound to the given module name.

    Parameters
    ----------
    name:
        Typically ``__name__`` of the calling module.

    Returns
    -------
    loguru.Logger
        A context-bound logger instance.
    """
    return _base_logger.bind(name=name)
