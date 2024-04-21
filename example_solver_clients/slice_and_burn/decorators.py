from datetime import datetime
from functools import wraps
import logging
import os
from pathlib import Path


def add_logging(obj):
    """Adds logging to solver objects."""

    @wraps(obj)
    def wrapper(*args, **kwargs):
        THIS_DIRECTORY = os.path.dirname(__file__)
        current = datetime.now()
        file_name = current.strftime("%Y%m-%d_%H%M%S") + 'game_logs.log'
        logger = logging.getLogger('SliceAndBurnSolver')
        log_path = Path(THIS_DIRECTORY, file_name)
        handler = logging.FileHandler(log_path)
        format = logging.Formatter("%(asctime)s: %(message)s")
        handler.setFormatter(format)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return wrapper