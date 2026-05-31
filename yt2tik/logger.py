"""
Logging setup for yt2tik
"""
import logging
from datetime import datetime
from pathlib import Path
from rich.logging import RichHandler
from .config import LOG_DIR


def setup_logger(name: str = "yt2tik") -> logging.Logger:
    """
    Setup logger with file and console handlers
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # File handler with timestamp
    log_filename = f"yt2tik_{datetime.now().strftime('%Y-%m-%d')}.log"
    log_path = LOG_DIR / log_filename

    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Rich console handler
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=False,
        show_path=False
    )
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "yt2tik") -> logging.Logger:
    """Get or create logger"""
    return logging.getLogger(name)
