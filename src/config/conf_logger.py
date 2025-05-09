import logging
from pathlib import Path

from src.config.config import LOGGER_LEVEL


def setup_logger(name: str, file: str, level: int = LOGGER_LEVEL) -> logging.Logger:
    log_dir = Path(__file__).resolve().parents[2] / "log"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_dir / f"{file}.log", mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
