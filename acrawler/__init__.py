from .crawler import Crawler
from .parser import Parser
from .item import Item, Processors, ParselItem
from .http import Request

import logging

LOGGER = logging.getLogger(__name__)


handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)


LOGGER.addHandler(handler)
LOGGER.setLevel(logging.DEBUG)
