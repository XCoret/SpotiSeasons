import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logger(log_file: str = "SpotiSeasons.log") -> logging.Logger:
    """Configures and returns a reusable application logger.

    Args:
        log_file (str): Path to the log file.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger("SpotiSeasons")

    # Avoid duplicate handlers (important in imports)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    os.makedirs("logs", exist_ok=True)
    file_path = os.path.join("logs", log_file)

    handler = RotatingFileHandler(
        file_path,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s]: %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger