from acrawler.task import Task
import aiohttp
import hashlib
import traceback
import logging
from yarl import URL
from pyquery import PyQuery
from inspect import isasyncgenfunction, isgeneratorfunction, \
    isfunction, iscoroutinefunction, ismethod
# Typing
from typing import Callable, List, Union, AsyncGenerator, Iterable
from multidict import CIMultiDictProxy
import http
_Function = Callable
_Functions = Union[_Function, List[_Function]]
_Cookies = 'http.cookies.SimpleCookie'
_History = List['aiohttp.ClientResponse']
_TaskGenerator = AsyncGenerator['Task', None]
_LooseURL = Union[URL, str]

logger = logging.getLogger(__name__)


class Request(Task):
    """Request is a Task that execute :meth:`fetch` method.

    :param url:
    :param callback: should be a callable function or a list of functions. 
        It will be passed to the response's task.
    :param method:
    :param request_config: will be passed to :meth:`aiohttp.ClientSession.request`.
    """

    def __init__(self, url: _LooseURL,
                 callback: _Functions = None,
                 method: str = 'GET',
                 request_config: dict = None,

                 # Below are paras for parent class
                 dont_filter: bool = False,
                 meta: dict = None,
                 priority: int = 0,
                 ):
        super().__init__(dont_filter=dont_filter,
                         priority=priority,
                         meta=meta,
                         )

        self.url = URL(url)
        self.method = method
        self.callback = callback
        self.request_config = request_config if request_config else {}
        self.session = None

    def _fingerprint(self):
        """fingerprint for a request task.
        .. todo::write a better hashing function for request.
        """
        fp = hashlib.sha1()
        fp.update(str(self.url).encode())
        return fp.hexdigest()

    async def _execute(self, **kwargs):
        """Wraps :meth:`fetch`"""
        yield await self.fetch()

    async def fetch(self):
        """Sends a request and return the response as a task."""
        try:
            async with self.session.request(
                    self.method, self.url, **self.request_config) as cresp:

                resp = await Response.from_ClientResponse(
                    cresp, meta=self.meta, callback=self.callback, request=self)
                rt = resp
        except Exception as e:
            logger.error(traceback.format_exc())
            rt = e
        finally:
            await self.close()
        return rt

    async def close(self):
        self.session = None

    def __str__(self):
        return "<%s> (%s)" % ('Task Request', self.url)


class Response(Task):
    """Response is a Task that execute parse function.

    :param status_code: HTTP status code of response, e.g. 200.
    :param url:
    :param cookies: HTTP cookies of response (Set-Cookie HTTP header).
    :param headers: A case-insensitive multidict proxy with HTTP headers of response.
    :param history: Preceding requests (earliest request first) if there were redirects.
    :param body: The whole response’s body as `bytes`.
    :param text: Read response’s body and return decoded `str`
    :param json: Read response’s body as `JSON` if avaliable
    :param request: Point to the request instance that generates this response.
    """

    def __init__(self,
                 url: URL,
                 status_code: int,
                 cookies: _Cookies,
                 headers: CIMultiDictProxy,
                 history: _History,
                 request: Request,
                 body: bytes,
                 text: str = None,
                 callback=None,
                 meta: dict = None,
                 ):
        super().__init__(dont_filter=True)
        self.url = url
        self.status_code = status_code
        self.cookies = cookies
        self.headers = headers
        self.history = history
        self.body = body
        self.text = text
        self.meta = meta
        self.callback = callback
        self.request = request

        #: A pyquery instance for the response's body.
        self.doc = PyQuery(self.body)
        self.doc.make_links_absolute(str(self.request.url))

        #: All callback functions stores in the list.
        self.callbacks: List[Callable] = []
        if isinstance(self.callback, Iterable):
            for cb in self.callback:
                self.add_callback(cb)
        else:
            self.add_callback(self.callback)

    @classmethod
    async def from_ClientResponse(cls, resp, meta, callback, request, json=False):
        r = cls(
            status_code=resp.status,
            url=resp.url,
            cookies=resp.cookies,
            headers=resp.headers,
            history=resp.history,
            meta=meta,
            callback=callback,
            request=request,
            body=await resp.read(),
            text=await resp.text(),
        )
        return r

    async def _execute(self, **kwargs):
        """Calls every callback function to yield new task."""
        for callback in self.callbacks:
            if isasyncgenfunction(callback):
                async for task in callback(self):
                    yield task
            elif isgeneratorfunction(callback):
                for task in callback(self):
                    yield task
            elif iscoroutinefunction(callback):
                yield await callback(self)
            elif ismethod(callback) or isfunction(callback):
                yield callback(self)

    def add_callback(self, func: _Function):
        """Add a callable function to response's :attr:`callbacks`"""
        if isfunction(func) or ismethod(func):
            self.callbacks.append(func)

    def __str__(self):
        return f"<Task Response> <{self.status_code}> ({self.url})"
