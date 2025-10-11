import sys
import os
import logging
from src.config import BASEDIR
from src.utils.decorators import singleton
from logging.handlers import RotatingFileHandler


@singleton
class AppLogger:
    def __init__(self, **kwargs):
        ### GENERAL LOGGING
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

        ### CONSOLE
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.setFormatter(formatter)

        ### LOGDFILE
        log_filename = kwargs.get("log_filename")

        # create Log-dir if not existing
        log_dir = os.path.dirname(log_filename)
        os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_filename,
            mode="a",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding=None,
            delay=0,
        )

        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(stdout_handler)

    # direct redirects to Logger-Methods
    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """Log a msg with Level ERROR and add Exception-Info"""
        self.logger.exception(msg, *args, **kwargs)


logfile_path = os.path.join(BASEDIR, "logs", "logs.log")
logmsg: AppLogger = AppLogger(log_filename=logfile_path)
# logmsg = AppLogger(log_filename=logfile_path)
