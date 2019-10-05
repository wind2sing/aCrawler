from parsel import Selector
from .item import ParselItem
from .http import Request
from .utils import to_asyncgen
import re
import urllib.parse
import logging
from typing import List, Callable

# Typing
_RE = str
_Function = Callable
logger = logging.getLogger(__name__)


class Parser:
    """A basic parser.

    It is a shortcut class for parsing response. If there are parsers int :attr:Crawler.parsers,
    then crawler will call Parser's parse method with the response to yield new Request Task or Item Task.

    Args:
        in_pattern: a string as a regex pattern or a function.
        follow_patterns: a list containing strings as regex patterns or a function.
        item_type: a custom item class to store results.
        css_divider: You may have many pieces in one response. Yield them in different selectors by providing a css_divider.
        selectors_loader: a function accepts selector and yield selectors. Default one deals with css_divider.
        callbacks: additional callbacks.
    """

    def _selectors_loader(self, selector):
        """You may have many pieces in one response. Yield them in different selectors."""

        if self.css_divider:
            for sel in selector.css(self.css_divider):
                yield sel
        else:
            yield selector

    def __init__(
        self,
        in_pattern: _RE = "",
        follow_patterns: List[_RE] = None,
        css_divider: str = None,
        item_type: ParselItem = None,
        extra: dict = None,
        pass_meta: bool = False,
        selectors_loader: _Function = None,
        callbacks: List[_Function] = None,
    ):

        self.in_pattern = in_pattern
        self.follow_patterns = follow_patterns or []

        self.item_type = item_type
        self.extra = extra
        self.pass_meta = pass_meta

        self.css_divider = css_divider
        self.selectors_loader = selectors_loader or self._selectors_loader

        self.callbacks = callbacks or []

    def _check_in_pattern(self, response):
        if isinstance(self.in_pattern, str):
            pattern = re.compile(self.in_pattern)
            match = pattern.search(str(response.url))
            if match:
                return True
        return False

    async def parse(self, response):
        """Main function to parse the response."""

        if self._check_in_pattern(response) and response.ok:
            for item in self.parse_items(response):
                yield item
            for req in self.parse_links(response):
                yield req
            for callback in self.callbacks:
                async for task in to_asyncgen(callback, response):
                    yield task
        else:
            yield None

    def parse_links(self, response):
        """Follow new links and yield Request in the response."""
        if self.follow_patterns:
            for p in self.follow_patterns:
                pattern = re.compile(p)
                html = response.text
                sel = Selector(html)
                links = [
                    urllib.parse.urljoin(str(response.url), href)
                    for href in sel.css("a::attr(href)").getall()
                ]
                for link in links:
                    if pattern.search(link):
                        rq = Request(link)
                        yield rq

    def parse_items(self, response):
        """Get items from all selectors in the loader."""

        for sel in self.selectors_loader(response.sel):
            if self.item_type:
                if issubclass(self.item_type, ParselItem):
                    extra = {}
                    if self.extra:
                        extra.update(self.extra)
                    if self.pass_meta and response.meta:
                        meta = response.meta
                    else:
                        meta = None
                    yield self.item_type(sel, extra=extra, meta=meta)
                else:
                    logger.warning(
                        f"Parser'item_type should be a subclass of <ParselItem>, {self.item_type}found!"
                    )
