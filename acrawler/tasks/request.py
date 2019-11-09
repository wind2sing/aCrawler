from .task import Task

from yarl import URL
from typing import AsyncGenerator, Callable, Iterable, List, Union
import aiohttp

import typing
import hashlib


if typing.TYPE_CHECKING:
    pass
from .response import Response
from ..utils import get_logger

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
