from acrawler.task import Task
import aiohttp
import aiofiles
import hashlib
from pathlib import Path
import traceback
import logging
from yarl import URL
from pyquery import PyQuery
from parsel import Selector

from inspect import isasyncgenfunction, isgeneratorfunction, \
    isfunction, iscoroutinefunction, ismethod
# Typing

from typing import Callable, List, Union, AsyncGenerator, Iterable, Set
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
                 encoding=None,

                 # Below are paras for parent class
                 dont_filter: bool = False,
                 meta: dict = None,
                 priority: int = 0,
                 session=None,
                 family=None
                 ):
        super().__init__(dont_filter=dont_filter,
                         priority=priority,
                         meta=meta,
                         family=family
                         )

        self.url = URL(url)
        self.url_str = str(self.url)
        self.method = method
        self.callbacks = []
        self.add_callback(callback)
        self.request_config = request_config if request_config else {}
        self.encoding = encoding
        self.session = None
        self.outer_session = session

    def add_callback(self, func: _Function):
        if isinstance(func, Iterable):
            for f in func:
                self.callbacks.append(func)
        else:
            self.callbacks.append(func)

    def reset_callback(self):
        self.callbacks = []

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
        if self.outer_session:
            self.session = self.outer_session
        try:
            async with self.session.request(
                    self.method, self.url, **self.request_config) as cresp:

                body = await cresp.read()
                text = None
                try:
                    text = await cresp.text()
                except Exception as e:
                    logger.warning("Decoding body failed: {}".format(e))
                    text = str(body)

                self.response = await Response.from_ClientResponse(url=cresp.url,
                                                                   status=cresp.status,
                                                                   cookies=cresp.cookies,
                                                                   headers=cresp.headers,
                                                                   history=cresp.history,
                                                                   body=body,
                                                                   text=text,
                                                                   request=self)
                rt = self.response

        except Exception as e:
            logger.error(traceback.format_exc())
            rt = e
        finally:
            await self.close()
        return rt

    async def close(self):
        if self.outer_session:
            await self.outer_session.close()
        self.session = None

    def __str__(self):
        return "<%s> (%s)" % ('Task Request', self.url)


class Response(Task):
    """Response is a Task that execute parse function.

    :param status: HTTP status code of response, e.g. 200.
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
                 status: int,
                 cookies: _Cookies,
                 headers: CIMultiDictProxy,
                 history: _History,
                 request: Request,
                 body: bytes,
                 text: str = None,
                 callbacks: _Functions = None,
                 meta: dict = None,
                 ):
        super().__init__(dont_filter=True)
        self.url = url
        self.url_str = str(url)
        self.status = status
        self.cookies = cookies
        self.headers = headers
        self.history = history
        self.body = body
        self.text = text
        self.meta = meta
        self.request = request
        self.callbacks = callbacks
        self.logger = logger

        self.sel: Selector = Selector(self.text)

        #: A pyquery instance for the response's body.
        self.doc = PyQuery(self.body)
        self.doc.make_links_absolute(str(self.request.url))

    @classmethod
    async def from_ClientResponse(cls, url, status, cookies, headers, history, body, text, request: Request):

        r = cls(
            url=url,
            status=status,
            cookies=cookies,
            headers=headers,
            history=history,
            meta=request.meta,
            callbacks=request.callbacks,
            request=request,
            body=body,
            text=text,
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
        if isinstance(func, Iterable):
            for f in func:
                self.callbacks.append(func)
        else:
            self.callbacks.append(func)

    def reset_callback(self):
        self.callbacks = []

    def __str__(self):
        return f"<Task Response> <{self.status}> ({self.url})"


async def file_save_callback(response: Response):
    if response.status == 200:
        where = response.meta['where']
        async with aiofiles.open(where, 'wb') as f:
            logger.info('Save file to {}'.format(where))
            await f.write(response.body)
    else:
        pass


class FileRequest(Request):
    file_dir_key = '_fdir'
    file_dir = Path.cwd()
    file_name_key = '_fname'
    file_name = ''

    def __init__(self, url, callback=None, method='GET', request_config=None, encoding=None, dont_filter=False, meta=None, priority=0, session=None, family=None):
        if not callback:
            callback = file_save_callback

        super().__init__(url, callback=callback, method=method, request_config=request_config, encoding=encoding,
                         dont_filter=dont_filter, meta=meta, priority=priority, session=session, family=family)

    async def _execute(self, **kwargs):
        if self.file_dir_key in self.meta:
            self.file_dir = Path(self.meta[self.file_dir_key])

        self.file_name = self.url_str.split('/')[-1]
        if self.file_name_key in self.meta:
            self.file_name = self.meta[self.file_name_key]

        self.meta['where'] = self.file_dir/self.file_name

        async for task in super()._execute(**kwargs):
            yield task
