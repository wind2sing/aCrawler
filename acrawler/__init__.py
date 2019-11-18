from .crawler import Crawler
from .parser import Parser
from .task import Task
from .item import Item, ParselItem, Processors, ParselXItem
from .http import Request, Response, FileRequest
from .middleware import middleware, Handler, register
from .handlers import callback
from .utils import get_logger, open_html
from .exceptions import (
    SkipTaskError,
    ReScheduleError,
    SkipTaskImmediatelyError,
    ReScheduleImmediatelyError,
)

from .chain import ChainCrawler, ChainRequest, ChainItem

# alias
x = Processors
