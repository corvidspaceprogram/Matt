import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

logger = logging.getLogger("mastodon_llm_bot")


def setup_logging():
    """
    Set up structured logging with:
    - Console handler (INFO level for dev, WARNING+ for production)
    - Rotating file handler (DEBUG level, size/rotation limited)
    - Formatters with timestamps, thread names
    """
    
    # Get logger - create if doesn't exist
    logger = logging.getLogger("mastodon_llm_bot")
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory (relative to cwd, assumed to be repo root)
    import os
    logs_dir = Path(os.getcwd()) / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # File handler - captures all levels for debugging
    file_handler = RotatingFileHandler(
        str(logs_dir / "app.log"),
        maxBytes=10_000_000,
        backupCount=20
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler - visible output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(levelname)s: [%(threadName)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def warning_handler(log_file="errorlog.txt"):
    """
    Write warnings to the legacy errorlog.txt file for backward compatibility.
    This maintains existing debugging workflows.
    """
    try:
        with open(log_file, "a") as f:
            import traceback
            timestamp = logging.getLogger().handlers[0].formatTime() if logging.getLogger().handlers else ""
            f.write(f"{timestamp} - WARNING: \n{traceback.format_exc()}\n\n")
    except Exception:
        pass  # Don't fail if warning log fails


# Auto-initialize logger when this module is imported
# This ensures logger and warning_handler are properly configured globally
def _init_logger():
    """Automatically initialize logging when module is imported."""
    try:
        setup_logging()
    except Exception:
        pass  # Silent fail - main.py will initialize properly


# Call initialization immediately
_init_logger()
