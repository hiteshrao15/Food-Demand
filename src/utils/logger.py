import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import logging

def setup_logging() -> None:
    """Configure logging for the application."""
    # Basic configuration
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance with console and file handlers.

    Args:
        name: Logger name (usually __name__ or module name)

    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)

    # If logger already has handlers, avoid adding duplicate ones
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Formatter for logs
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler for real-time tracking
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    try:
        # File Handler for persistant logging
        log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
        os.makedirs(log_dir, exist_ok=True)

        log_file = log_dir / f"app_{datetime.now().strftime('%Y-%m')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if file logging fails due to permissions
        logger.warning(f"Could not setup file logging: {str(e)}")

    # Prevent propagation to root logger to avoid duplicate prints
    logger.propagate = False

    return logger
