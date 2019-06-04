from multidict import CIMultiDictProxy
from typing import Callable, List, Union, AsyncGenerator, Iterable, Set
from acrawler.task import Task
from acrawler.utils import to_asyncgen
import asyncio
import aiohttp
import aiofiles
import hashlib
import json
from json.decoder import JSONDecodeError
from urllib.parse import urljoin
from pathlib import Path
import traceback
import logging
from yarl import URL
from parsel import Selector, SelectorList
from aiohttp import ClientResponse
from inspect import isasyncgenfunction, isgeneratorfunction, \
    isfunction, iscoroutinefunction, ismethod, signature

# Typing


_Function = Callable
_Functions = Union[_Function, List[_Function]]
_History = List['aiohttp.ClientResponse']
_TaskGenerator = AsyncGenerator['Task', None]
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

    def __init__(self, url: _LooseURL,
                 callback: _Functions = None,
                 method: str = 'GET',
                 request_config: dict = None,
                 status_allowed: list = None,
                 encoding=None,

                 # Below are paras for parent class
                 dont_filter: bool = False,
                 ignore_exception: bool = False,
                 meta: dict = None,
                 priority: int = 0,
                 family=None,
                 recrawl=0,
                 exetime=0,
                 **kwargs
                 ):
        super().__init__(dont_filter=dont_filter,
                         ignore_exception=ignore_exception,
                         priority=priority,
                         meta=meta,
                         family=family,
                         recrawl=recrawl,
                         exetime=exetime,
                         **kwargs
                         )

        self.url = URL(url)
        self.method = method
        self.status_allowed = status_allowed
        self.callbacks = []
        if callback:
            self.add_callback(callback)
        self.request_config = request_config if request_config else {}
        self.session = None
        self.response: Response = None
        self.httpfamily = family
        self.encoding = encoding

    @property
    def url_str(self):
        return self.url.human_repr()

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
        fp.update(self.url_str.encode())
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
                encoding = self.encoding or cresp.get_encoding()

                self.response = Response(url=cresp.url,
                                         status=cresp.status,
                                         cookies=cresp.cookies,
                                         headers=cresp.headers,
                                         history=cresp.history,
                                         body=body,
                                         encoding=encoding,
                                         callbacks=self.callbacks,
                                         request=self,
                                         request_info=cresp.request_info,
                                         meta=self.meta,
                                         family=self.httpfamily)
                rt = self.response
                logger.info(rt)
                return rt
        except Exception as e:
            return e
        finally:
            if to_close:
                await self.session.close()

    def __str__(self):
        return "<%s> (%s)" % ('Task Request', self.url)

    def __getstate__(self):
        state = super().__getstate__()
        state.pop('session', None)
        state.pop('response', None)
        return state

    def __setstate__(self, state):
        super().__setstate__(state)
        self.__dict__['response'] = None
        self.__dict__['session'] = None


class Response(Task):
    """Response is a Task that execute parse function.

    Attributes:
        status: HTTP status code of response, e.g. 200.
        url: url as yarl URL
        url_str: url as str
        sel: a ``Selector``. See `Parsel <https://parsel.readthedocs.io/en/latest/>`_ for parsing rules.
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

    def __init__(self,
                 url: URL,
                 status: int,
                 cookies: 'http.cookies.SimpleCookie',
                 headers: CIMultiDictProxy,
                 history: _History,
                 request: Request,
                 request_info,
                 body: bytes,
                 encoding: str,
                 callbacks: _Functions = None,
                 meta: dict = None,
                 **kwargs
                 ):
        dont_filter = kwargs.pop('dont_filter', True)
        ignore_exception = kwargs.pop('ignore_exception', True)
        super().__init__(
            dont_filter=dont_filter,
            ignore_exception=ignore_exception,
            **kwargs
        )
        self.url = url
        self.status = status
        self.cookies = cookies
        self.headers = headers
        self.history = history
        self.body = body
        self.encoding = encoding
        self.meta = meta
        self.request = request
        self.request_info = request_info
        self.callbacks = callbacks
        self.ok = (self.status == 200) or (self.request.status_allowed == []) or (
            (self.request.status_allowed) and (self.status in self.request.status_allowed))
        self.bind_cbs = False

        self._text = None
        self._json = None
        self._sel: Selector = None

    @property
    def text(self):
        if self._text is None:
            try:
                self._text = self.body.decode(self.encoding)
            except Exception as e:
                logger.debug('({}) {}'.format(self.url_str, e))
                self._text = self.body.decode(self.encoding, 'ignore')
        return self._text

    @property
    def json(self):
        if self._json is None:
            try:
                self._json = json.loads(self.body)
            except JSONDecodeError as e:
                logger.error('JSONDecodeError for {}: {}'.format(self, e))
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
    def url_str(self):
        return self.url.human_repr()

    async def _execute(self, **kwargs):
        """Calls every callback function to yield new task."""
        for callback in self.callbacks:
            async for task in to_asyncgen(callback, self):
                yield task

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
        elif isinstance(a, Selector):
            url = a.attrib['href']
        else:
            raise ValueError('urljoin receive bad argument{}'.format(a))
        return urljoin(self.url_str, url)

    def add_callback(self, func: _Function):
        if isinstance(func, Iterable):
            for f in func:
                self.callbacks.append(f)
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
    """ A derived Request to download files.
    """

    file_dir = Path.cwd()
    """Directly set the location the location where the file will save.
    """

    file_dir_key = '_fdir'
    """It will try to call `self.meta.get(file_dir_key)` to get the location where the file will save.
    """

    file_name = ''
    """Directly set the file name. Otherwise name from url will be used as filename.
    """

    file_name_key = '_fname'
    """It will try to call `self.meta.get(file_name_key)` to get the file name to save.
    """

    def __init__(self, url, callback=None, method='GET', request_config=None, dont_filter=False, meta=None, priority=0, family=None, *args, **kwargs):
        if not callback:
            callback = file_save_callback

        super().__init__(url, callback=callback, method=method, request_config=request_config,
                         dont_filter=dont_filter, meta=meta, priority=priority, family=family, *args, **kwargs)

    async def _execute(self, **kwargs):
        if self.file_dir_key in self.meta:
            self.file_dir = Path(self.meta[self.file_dir_key])

        self.file_name = self.url_str.split('/')[-1]
        ext = self.file_name.split('.')[-1]
        if self.file_name_key in self.meta:
            self.file_name = self.meta[self.file_name_key] + '.' + ext

        self.meta['where'] = self.file_dir/self.file_name

        async for task in super()._execute(**kwargs):
            yield task
