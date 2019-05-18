from .crawler import Crawler
from .parser import Parser
from .item import Item, ParselItem, Processors
from .http import Request, Response
from .middleware import middleware, Handler, register
from .handlers import callback
from .utils import get_logger

import logging

LOGGER = logging.getLogger(__name__)


handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(name)-20s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)


LOGGER.addHandler(handler)
LOGGER.setLevel(logging.DEBUG)
