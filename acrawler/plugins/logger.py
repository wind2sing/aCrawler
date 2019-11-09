from .base import Plugin
from ..utils import get_logger
import logging

logger = get_logger("logger")


class LoggerPlugin(Plugin):
    priority = 2000

    def start(self):

        level = self.config.log_level
        to_file = self.config.log_to_file
        fmt = self.config.log_fmt
        datefmt = self.config.log_datefmt
        LOGGER = logging.getLogger("acrawler")

        if to_file:
            handler = logging.FileHandler(to_file)
        else:
            handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        handler.setFormatter(formatter)

        LOGGER.addHandler(handler)
        LOGGER.setLevel(level)
        logger.info(self.middleware.plugins)
