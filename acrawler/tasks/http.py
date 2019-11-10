import hashlib
import typing
from typing import AsyncGenerator, Callable, Iterable, List, Union

import aiohttp
from parselx import SelectorX
from yarl import URL

from ..utils import get_logger, make_text_links_absolute, open_html, to_asyncgen
from .task import Task


logger = get_logger("http")


class Request(Task):
    """Request is a Task that execute :meth:`fetch` method.

    Attributes:
        url:
        callback: should be a callable function or a list of functions.
            It will be passed to the corresponding response task.
        family: this family will be appended in families and also passed to corresponding
            response task.
        status_allowed: a list of allowed status integer. Otherwise any response task
            with `status!=200` will fail and retry.
        meta: a dictionary to deliver information. It will be passed to :attr:`Response.meta`.
        request_config: a dictionary, will be passed as keyword arguments
            to :meth:`aiohttp.ClientSession.request`.

            acceptable keyword:

                params - Dictionary or bytes to be sent in the query string of the new request

                data - Dictionary, bytes, or file-like object to send in the body of the request

                json - Any json compatible python object

                headers - Dictionary of HTTP Headers to send with the request

                cookies - Dict object to send with the request

                allow_redirects - If set to False, do not follow redirects

                timeout - Optional ClientTimeout settings structure, 5min total timeout by default.

    """

    def __init__(
        self,
        url,
        callback=None,
        method: str = "GET",
        request_config: dict = None,
        status_allowed: list = None,
        encoding=None,
        links_to_abs=True,
        # Below are paras for parent class
        dont_filter: bool = False,
        ignore_exception: bool = False,
        meta: dict = None,
        priority: int = 0,
        family=None,
        recrawl=0,
        exetime=0,
        **kwargs,
    ):
        super().__init__(
            dont_filter=dont_filter,
            ignore_exception=ignore_exception,
            priority=priority,
            meta=meta,
            family=family,
            recrawl=recrawl,
            exetime=exetime,
            **kwargs,
        )

        self.url = URL(url)
        self.method = method
        self.status_allowed = status_allowed
        self.callbacks = []
        if callback:
            self.add_callback(callback)
        self.request_config = request_config if request_config else {}
        self.session = None
        self.client = None
        self.response: Response = None
        self.httpfamily = family
        self.encoding = encoding
        self.links_to_abs = links_to_abs

        self.inprogress = False  # is this request start execution; for counter

    @property
    def url_str(self):
        return self.url.human_repr()

    @property
    def url_str_canonicalized(self):
        query_str = "&".join(sorted(self.url.raw_query_string.split("&")))
        return (
            str(self.url)
            .replace(self.url.raw_query_string, query_str)
            .replace("#" + self.url.raw_fragment, "")
        )

    def add_callback(self, func):
        if isinstance(func, Iterable):
            for f in func:
                self.callbacks.append(f)
        else:
            self.callbacks.append(func)

    def reset_callback(self):
        self.callbacks = []

    def _fingerprint(self):
        """fingerprint for a request task.
        .. todo::write a better hashing function for request.
        """
        fp = hashlib.sha1()
        fp.update(self.url_str_canonicalized.encode())
        fp.update(self.method.encode())
        return fp.hexdigest()

    async def _execute(self, **kwargs):
        """Wraps :meth:`fetch`"""
        yield await self.fetch()

    async def send(self):
        """This method is used for independent usage of Request without Crawler.
        """
        resp = None
        async for task in self.execute():
            if isinstance(task, Response):
                resp = task
        return resp

    async def fetch(self):
        """Sends a request and return the response as a task."""
        to_close = False

        if self.session is None:
            self.session = aiohttp.ClientSession()
            to_close = True
        try:
            async with self.session.request(
                self.method, self.url, **self.request_config
            ) as cresp:

                body = await cresp.read()
                encoding = self.encoding or cresp.get_encoding()

                self.response = Response(
                    url=cresp.url,
                    status=cresp.status,
                    cookies=cresp.cookies,
                    headers=cresp.headers.copy(),
                    body=body,
                    encoding=encoding,
                    links_to_abs=self.links_to_abs,
                    callbacks=self.callbacks.copy(),
                    request=self,
                    meta=self.meta,
                    family=self.httpfamily,
                )
                rt = self.response
                logger.info(f"<{self.response.status}> {self.response.url_str}")
                return rt
        except Exception as e:
            raise e
        finally:
            if to_close:
                await self.session.close()

    def __str__(self):
        return f"<Task {self.family}> ({self.url.human_repr()})"

    def __getstate__(self):
        state = super().__getstate__()
        state.pop("session", None)
        state.pop("client", None)
        return state

    def __setstate__(self, state):
        super().__setstate__(state)
        self.__dict__["session"] = None
        self.__dict__["client"] = None


class Response(Task):
    """Response is a Task that execute parse function.

    Attributes:
        status: HTTP status code of response, e.g. 200.
        url: url as yarl URL
        url_str: url as str
        sel: a ``Selector``. See `Parsel <https://parsel.readthedocs.io/en/latest/>`_ for parsing rules.
        doc: a ``PyQuery`` object.
        meta: a dictionary to deliver information. It comes from :attr:`Request.meta`.
        ok: True if `status==200` or status is allowed from :attr:`Request.status_allowed`
        cookies: HTTP cookies of response (Set-Cookie HTTP header).
        headers: A case-insensitive multidict proxy with HTTP headers of response.
        history: Preceding requests (earliest request first) if there were redirects.
        body: The whole response’s body as `bytes`.
        text: Read response’s body and return decoded `str`
        request: Point to the corresponding request object that generates this response.
        callbacks: list of callback functions
    """

    def __init__(
        self,
        url: "URL",
        status: int,
        cookies: "http.cookies.SimpleCookie",
        headers: "CIMultiDict",
        request: "Request",
        body: bytes,
        encoding: str,
        links_to_abs: bool = False,
        callbacks=None,
        meta: dict = None,
        **kwargs,
    ):
        dont_filter = kwargs.pop("dont_filter", True)
        ignore_exception = kwargs.pop("ignore_exception", True)
        super().__init__(
            dont_filter=dont_filter, ignore_exception=ignore_exception, **kwargs
        )
        self.url = url
        self.status = status
        self.cookies = cookies
        self.headers = headers

        self.body = body
        self.encoding = encoding
        self.links_to_abs = links_to_abs
        self.meta = meta
        self.request = request
        self.callbacks = callbacks
        self.bind_cbs = False

        self._text_raw = None
        self._text_absolute = None
        self._json = None
        self._sel: Selector = None
        self._pq = None

    @property
    def url_str(self):
        return self.url.human_repr()

    @property
    def ok(self) -> bool:
        """ If the response is allowed by the config of request.
        """
        return (
            (self.status == 200)
            or (self.request.status_allowed == [])
            or (
                (self.request.status_allowed)
                and (self.status in self.request.status_allowed)
            )
        )

    @property
    def text(self):
        if self.links_to_abs:
            return self.text_absolute
        else:
            return self.text_raw

    @property
    def text_raw(self):
        if self._text_raw is None:
            try:
                self._text_raw = self.body.decode(self.encoding)
            except Exception as e:
                logger.debug("({}) {}".format(self.url_str, e))
                self._text_raw = self.body.decode(self.encoding, "ignore")
        return self._text_raw

    @property
    def text_absolute(self):
        if self._text_absolute is None:
            self._text_absolute = make_text_links_absolute(self.text_raw, self.url_str)
        return self._text_absolute

    @property
    def json(self):
        if self._json is None:
            self._json = json.loads(self.body)
        return self._json

    @property
    def sel(self) -> SelectorX:
        if self._sel is None:
            try:
                self._sel = SelectorX(self.text, vars=self.meta)
            except Exception as e:
                logger.error(e)
        return self._sel

    @property
    def url_str(self):
        return self.url.human_repr()

    def open(self, path=None):
        """ Open in default browser """
        open_html(self.text, path=path)

    def paginate(self, css: str, limit: int = 0, **kwargs):
        """ Follow links and yield requests with same callback functions.
        Additional keyword arguments will be used for constructing requests.
        Args:
            css (str): css selector
            limit: max number of links to follow.
        """
        count = 0
        for url in self.sel.css(css).getall():
            request = Request(url, meta=meta, **kwargs)
            request.callbacks = self.request.callbacks
            yield request
            count += 1
            if limit and count >= limit:
                break

    def follow(self, css, callback=None, limit=0, pass_meta=False, **kwargs):
        """ Yield requests in current page using css selector.
        Additional keyword arguments will be used for constructing requests.
        Args:
            css (str): css selector
            callback (callable, optional):  Defaults to None.
            limit: max number of links to follow.
        """
        meta = kwargs.pop("meta", {})
        if pass_meta:
            meta.update(self.meta)
        count = 0
        for url in self.sel.css(css).getall():
            request = Request(url, callback=callback, meta=meta, **kwargs)
            yield request
            count += 1
            if limit and count >= limit:
                break

    def spawn(self, item, divider=None, **kwargs):
        """ Yield items in current page
        Additional keyword arguments will be used for constructing items.
        Args:
            divider (str): css divider
            item (ParselItem): item class
        """
        if divider:
            for sel in self.sel.css(divider):
                yield item(sel, **kwargs)
        else:
            yield item(self.sel, **kwargs)

    async def _execute(self, **kwargs):
        """Calls every callback function to yield new task."""
        if self.ok:
            for callback in self.callbacks:
                async for task in to_asyncgen(callback, self):
                    yield task
        else:
            yield None

    def __str__(self):
        return f"<Task Response> <{self.status}> ({self.url_str})"