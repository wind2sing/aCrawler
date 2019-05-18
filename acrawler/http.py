from acrawler.task import Task
from acrawler.utils import to_asyncgen
import aiohttp
import aiofiles
import hashlib
from urllib.parse import urljoin
from pathlib import Path
import traceback
import logging
from yarl import URL
from pyquery import PyQuery
from parsel import Selector, SelectorList
from aiohttp import ClientResponse
from inspect import isasyncgenfunction, isgeneratorfunction, \
    isfunction, iscoroutinefunction, ismethod, signature
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

                 # Below are paras for parent class
                 dont_filter: bool = False,
                 meta: dict = None,
                 priority: int = 0,
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
        if callback:
            self.add_callback(callback)
        self.request_config = request_config if request_config else {}
        self.session = None
        self.response: Response = None
        self._userfamily = family

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
        to_close = False

        if self.session is None:
            self.session = aiohttp.ClientSession()
            to_close = True
        try:
            async with self.session.request(
                    self.method, self.url, **self.request_config) as cresp:

                body = await cresp.read()
                encoding = cresp.get_encoding()

                self.response = await Response.from_ClientResponse(url=cresp.url,
                                                                   status=cresp.status,
                                                                   cookies=cresp.cookies,
                                                                   headers=cresp.headers,
                                                                   history=cresp.history,
                                                                   body=body,
                                                                   encoding=encoding,
                                                                   request=self,
                                                                   family=self._userfamily)
                rt = self.response

        except Exception as e:
            logger.error(traceback.format_exc())
            rt = e
        finally:
            if to_close:
                await self.session.close()
        return rt

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
                 encoding: str,
                 callbacks: _Functions = None,
                 meta: dict = None,
                 **kwargs
                 ):
        dont_filter = kwargs.pop('dont_filter', True)
        super().__init__(dont_filter=dont_filter, **kwargs)
        self.url = url
        self.url_str = str(url)
        self.status = status
        self.cookies = cookies
        self.headers = headers
        self.history = history
        self.body = body
        self.encoding = encoding
        self.meta = meta
        self.request = request
        self.callbacks = callbacks

        self._text = None
        self._sel: Selector= None


    @classmethod
    async def from_ClientResponse(cls, url, status, cookies, headers, history, body, encoding, request: Request, **kwargs):

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
            encoding=encoding,
            **kwargs
        )
        return r

    @property
    def text(self):
        if self._text is None:
            self._text = self.body.decode(self.encoding)
        return self._text
    
    @property
    def sel(self):
        if self._sel is None:
            try:
                self._sel = Selector(self.text)
            except Exception as e:
                logger.error(e)
        return self._sel

    async def _execute(self, **kwargs):
        """Calls every callback function to yield new task."""
        for callback in self.callbacks:
            async for task in to_asyncgen(callback, self):
                yield task

    def urljoin(self, a):
        if isinstance(a, str):
            url = a
        elif isinstance(a, Selector):
            url = a.attrib['href']
        return urljoin(self.url_str, url)

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

    def __init__(self, url, callback=None, method='GET', request_config=None, dont_filter=False, meta=None, priority=0, family=None):
        if not callback:
            callback = file_save_callback

        super().__init__(url, callback=callback, method=method, request_config=request_config,
                         dont_filter=dont_filter, meta=meta, priority=priority, family=family)

    async def _execute(self, **kwargs):
        if self.file_dir_key in self.meta:
            self.file_dir = Path(self.meta[self.file_dir_key])

        self.file_name = self.url_str.split('/')[-1]
        if self.file_name_key in self.meta:
            self.file_name = self.meta[self.file_name_key]

        self.meta['where'] = self.file_dir/self.file_name

        async for task in super()._execute(**kwargs):
            yield task
