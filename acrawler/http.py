import hashlib
import json
import logging
from pathlib import Path
from typing import AsyncGenerator, Callable, Iterable, List, Union
from urllib.parse import urljoin

import aiohttp
from multidict import CIMultiDict
from parsel import Selector
from yarl import URL

from acrawler.task import Task
from acrawler.utils import (
    check_import,
    make_text_links_absolute,
    open_html,
    to_asyncgen,
)

aiofiles = check_import("aiofiles", allow_import_error=True)
pyquery = check_import("pyquery", allow_import_error=True)


_Function = Callable
_Functions = Union[_Function, List[_Function]]
_History = List["aiohttp.ClientResponse"]
_TaskGenerator = AsyncGenerator["Task", None]
_LooseURL = Union[URL, str]

logger = logging.getLogger(__name__)


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
        url: _LooseURL,
        callback: _Functions = None,
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

    def add_callback(self, func: _Function):
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
        return f"<Task {self.primary_family}> ({self.url.human_repr()})"

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
        url: URL,
        status: int,
        cookies: "http.cookies.SimpleCookie",
        headers: CIMultiDict,
        request: Request,
        body: bytes,
        encoding: str,
        links_to_abs: bool = False,
        callbacks: _Functions = None,
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
    def sel(self):
        if self._sel is None:
            try:
                self._sel = Selector(self.text)
            except Exception as e:
                logger.error(e)
        return self._sel

    @property
    def pq(self):
        if self._pq is None:
            self._pq = pyquery.PyQuery(self.text)
        return self._pq

    def update_sel(self, source=None):
        """ Update response's Selector.

        Args:
            source: can be a string or a PyQuery object.
                if it's None, use `self.pq` as source by default.

        """
        if source is None:
            source = self.pq
        if isinstance(source, pyquery.PyQuery):
            self._sel = Selector(source.html())
        elif isinstance(source, str):
            self._sel = Selector(source)

    @property
    def url_str(self):
        return self.url.human_repr()

    def open(self, path=None):
        """ Open in default browser """
        open_html(self.text, path=path)

    async def _execute(self, **kwargs):
        """Calls every callback function to yield new task."""
        if self.ok:
            for callback in self.callbacks:
                async for task in to_asyncgen(callback, self):
                    yield task
        else:
            yield None

    async def parse(self) -> list:
        """Parse the response(call all callback funcs) and return the list of yielded results.
        This method should be used in independent work without Crawler.
        """
        rt = []
        async for task in self.execute():
            if task:
                rt.append(task)
        return rt

    def urljoin(self, a) -> str:
        """ Accept a str (can be a relative url) or a Selector that has href attributes.

        Returns:
            return a absolute url.
        """
        url = None
        if isinstance(a, list):
            if len(a) > 0:
                a = a[0]
        if isinstance(a, str):
            url = a
        elif isinstance(a, Selector) and "href" in a.attrib:
            url = a.attrib["href"]
        else:
            raise ValueError("urljoin receive bad argument{}".format(a))
        return urljoin(self.url_str, url)

    def paginate(self, css: str, limit: int = 0, pass_meta=False, **kwargs):
        """ Follow links and yield requests with same callback functions.
        Additional keyword arguments will be used for constructing requests.

        Args:
            css (str): css selector
            limit: max number of links to follow.
        """
        meta = kwargs.pop("meta", {})
        if pass_meta:
            meta.update(self.meta)
        count = 0
        for url in self.sel.css(css).getall():
            request = Request(url, meta=meta, **kwargs)
            for cb in self.request.callbacks:
                request.add_callback(cb)
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

    def spawn(self, item, divider=None, pass_meta=True, **kwargs):
        """ Yield items in current page
        Additional keyword arguments will be used for constructing items.

        Args:
            divider (str): css divider
            item (ParselItem): item class
        """
        if divider:
            for sel in self.sel.css(divider):
                yield item(sel, meta=self.meta, **kwargs)
        else:
            yield item(self.sel, meta=self.meta, **kwargs)

    def add_callback(self, func: _Function):
        if isinstance(func, Iterable):
            for f in func:
                self.callbacks.append(f)
        else:
            self.callbacks.append(func)

    def reset_callback(self):
        self.callbacks = []

    def __str__(self):
        return f"<Task Response> <{self.status}> ({self.url.human_repr()})"

    def __getstate__(self):
        state = super().__getstate__()

        sel = state.pop("_sel", None)
        if sel:
            state["__sel_text"] = sel.get()
        return state

    def __setstate__(self, state):
        sel_text = state.pop("__sel_text", None)
        if sel_text:
            _sel = Selector(sel_text)
        else:
            _sel = None
        super().__setstate__(state)
        self.__dict__["_sel"] = _sel


async def file_save_callback(response: Response):
    if response.status == 200:
        where = response.meta["where"]
        async with aiofiles.open(where, "wb") as f:
            logger.info(f"Save file to {where}")
            await f.write(response.body)
    else:
        pass


class FileRequest(Request):
    """ A derived Request to download files.
    """

    def __init__(
        self,
        url,
        *args,
        fdir=None,
        fname=None,
        skip_if_exists=True,
        callback=None,
        method="GET",
        request_config=None,
        dont_filter=False,
        meta=None,
        priority=0,
        family=None,
        **kwargs,
    ):
        if not callback:
            callback = file_save_callback
        super().__init__(
            url,
            callback=callback,
            method=method,
            request_config=request_config,
            dont_filter=dont_filter,
            meta=meta,
            priority=priority,
            family=family,
            *args,
            **kwargs,
        )
        self.skip_if_exists = skip_if_exists

        self.file_dir = Path(fdir) if fdir else Path.cwd()
        self.file_dir.mkdir(parents=True, exist_ok=True)

        self.file_name = self.url_str.split("?", 1)[0].rsplit("/", 1)[-1]
        ext = self.file_name.split(".")[-1]
        if fname:
            self.file_name = fname + "." + ext

    async def _execute(self, **kwargs):
        self.meta["where"] = self.file_dir / self.file_name

        if self.skip_if_exists and self.meta["where"].exists():
            yield None
        else:
            async for task in super()._execute(**kwargs):
                yield task


class BrowserRequest(Request):
    """A derived Request using `pyppeteer` to crawl pages.

    There are two ways to directly deal with `pyppeteer.page.Page`. You can rewrite
    method :meth:`operate_page` or pass `page_callback` as parameter. Callback
    function accepts two parameters: `page` and `resposne`.
    """

    def __init__(
        self,
        url,
        *args,
        page_callback=None,
        callback=None,
        method="GET",
        request_config=None,
        dont_filter=False,
        meta=None,
        priority=0,
        family=None,
        **kwargs,
    ):
        super().__init__(
            url,
            callback=callback,
            method=method,
            request_config=request_config,
            dont_filter=dont_filter,
            meta=meta,
            priority=priority,
            family=family,
            *args,
            **kwargs,
        )
        self.page_callback = page_callback
        self.page = None

    async def _execute(self, **kwargs):
        """Wraps :meth:`fetch`"""
        async for task in to_asyncgen(self.fetch):
            yield task

    async def fetch(self):
        """Sends a request and return the response as a task."""
        try:
            self.page = await self.client.newPage()
            if self.url_str:
                resp = await self.page.goto(self.url_str)
                logger.info(f"<BrowserRequest> <{resp.status}> ({resp.url})")
            else:
                resp = None
            async for task in to_asyncgen(self.operate_page, self.page, resp):
                yield task
            async for task in to_asyncgen(self.page_callback, self.page, resp):
                yield task
        except Exception as e:
            raise e
        finally:
            await self.client.cookies_manager.update_from_pyppeteer(self.page)
            await self.page.close()
            self.page = None

    async def operate_page(self, page, response):
        """Can be rewritten for customed operation on the page. Should be a asyncgenerator to yield new tasks.
        """
        yield None
