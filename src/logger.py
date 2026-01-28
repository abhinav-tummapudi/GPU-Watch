import logging
from logging.handlers import RotatingFileHandler
import socket
import os

def setup_logger(name='gpu_monitor', log_dir='logs'):
    # Get hostname
    hostname = socket.gethostname()

    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Shared log file
    log_file = os.path.join(log_dir, "monitor.log")

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Rotating file handler
    handler = RotatingFileHandler(log_file, maxBytes=5_000_000, backupCount=3)

    # Include hostname in each log line
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - ' + hostname + ' - %(message)s')
    handler.setFormatter(formatter)

    # Add handler only if it hasn't been added
    if not logger.hasHandlers():
        logger.addHandler(handler)

    return logger

