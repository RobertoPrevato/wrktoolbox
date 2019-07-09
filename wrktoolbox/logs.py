import logging
import logging.handlers
from datetime import datetime
from rocore.folders import ensure_folder


logger = None


def get_app_logger():
    global logger

    if logger is not None:
        return logger

    logger = logging.getLogger('wrktoolbox')

    logger.setLevel(logging.INFO)

    max_bytes = 24 * 1024 * 1024

    file_handler = logging.handlers.RotatingFileHandler

    now = datetime.now()
    ts = now.strftime('%Y%m%d')

    ensure_folder(f'logs/{ts}')

    handler = file_handler(f'logs/{ts}/wrktoolbox.log',
                           maxBytes=max_bytes,
                           backupCount=5)

    handler.setLevel(logging.DEBUG)

    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())

    return logger
