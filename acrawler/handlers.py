import traceback
from acrawler.middleware import Handler, middleware
from acrawler.counter import RedisCounter
import importlib
import sys
import functools
import inspect
import json
import pickle
import logging
from acrawler.http import Request
from acrawler.utils import check_import
import asyncio
from aiohttp import ClientSession, TCPConnector

# Typing
import acrawler
from typing import List, Callable

_Function = Callable
_Task = 'acrawler.task.Task'
_Request = 'acrawler.http.Request'
_Response = 'acrawler.http.Response'
_Crawler = 'acrawler.crawler.Crawler'

logger = logging.getLogger(__name__)

# Request Part


class RequestPrepareSession(Handler):
    family = 'Request'

    async def on_start(self):
        self.connector = TCPConnector(limit=None)
        self.session = ClientSession(connector=self.connector)
        self.crawler._session = self.session

    async def handle_before(self, task):
        task.session = self.session

    async def on_close(self):
        await self.session.close()


class ResponseCheckStatus(Handler):
    """a handler check response's status and will retry the request if it failed.

    If the response is not allowed by crawler and by request's parameters, it will be considered as failing and then retried.
    By default, any response with status rather than 200 will fail.
    """
    family = 'Response'

    def on_start(self):
        self.status_allowed = self.crawler.config.get('STATUS_ALLOWED', None)
        self.allow_all = (self.status_allowed == [])
        self.deny_all = self.status_allowed is None

    async def handle_before(self, response):
        if self.allow_all:
            return
        if response.status != 200:
            if self.deny_all or not response.status in self.status_allowed:
                if not response.ok:
                    task = response.request
                    if task.tries < self.crawler.max_tries:
                        await self.crawler.add_task(response.request, dont_filter=True)
                        logger.warning(
                            'Retry the task {}'.format(response.request))
                    else:
                        pass
                        # logger.warning(
                        # 'Drop the task {}'.format(response.request))


class RequestMergeConfig(Handler):
    """a handler (before execution) which merge `config` to :attr:`Request.request_config`."""
    family = 'Request'

    def handle_before(self, request: _Request):
        h0 = self.crawler.request_config.get('headers', {})
        h1 = request.request_config.get('headers', {})
        h = {**h0, **h1}
        request.request_config = {
            **self.crawler.request_config, **request.request_config}
        if h:
            request.request_config['headers'] = h


class RequestDelay(Handler):
    family = 'Request'

    async def handle_before(self, request: _Request):
        await asyncio.sleep(self.crawler.config.get('DOWNLOAD_DELAY'))


# Response Part

class ResponseAddCallback(Handler):
    """a handler (before execution) which add :meth:`Parser.parse` to :attr:`Response.callbacks`."""

    family = 'Response'
    callback_table = {}

    def handle_before(self, response: _Response):
        if not response.bind_cbs:
            for parser in self.crawler.parsers:
                response.add_callback(parser.parse)

            if response.primary_family in self.callback_table:
                for fn in self.callback_table[response.primary_family]:
                    sig = inspect.signature(fn)
                    if 'self' in sig.parameters:
                        fn = functools.partial(fn, self.crawler)
                    response.add_callback(fn)
            response.bind_cbs = True

    @classmethod
    def callback(cls, family):

        def decorator(func):
            li = cls.callback_table.setdefault(family, [])
            li.append(func)
            return func

        return decorator


callback = ResponseAddCallback.callback
""" The decorator to add callback function.
"""

# Item Part


class ItemToRedis(Handler):
    family = 'Item'
    """Family of this handler."""

    address: str = 'redis://localhost'
    """
    An address where to connect.
        Can be one of the following:

        * a Redis URI --- ``"redis://host:6379/0?encoding=utf-8"``;

        * a (host, port) tuple --- ``('localhost', 6379)``;

        * or a unix domain socket path string --- ``"/path/to/redis.sock"``.
    """

    maxsize = 10
    """Maximum number of connection to keep in pool.
    """

    items_key = 'acrawler:items'
    """Key of the list at which item's content is inserted.
    """

    async def on_start(self):
        aioredis = check_import('aioredis')
        self.items_key = self.crawler.config.get(
            'REDIS_ITEMS_KEY', self.items_key)
        self.redis = await aioredis.create_redis_pool(
            self.address,
            maxsize=self.maxsize,
            loop=self.crawler.loop)
        logger.info(f'Connecting to Redis... {self.redis}')

    async def handle_after(self, item):
        await self.redis.lpush(self.items_key, json.dumps(item.content))

    async def on_close(self):
        self.redis.close()
        await self.redis.wait_closed()


class ItemToMongo(Handler):
    family = 'Item'
    """Family of this handler."""

    address = 'mongodb://localhost:27017'
    """a full mongodb URI, in addition to a simple hostname"""

    db_name = ''
    """name of targeted database"""

    col_name = ''
    """name of targeted collection"""

    primary_key = ''

    async def on_start(self):
        mo = check_import('motor.motor_asyncio')
        self.client = mo.AsyncIOMotorClient(self.address)
        self.db = self.client[self.db_name]
        self.col = self.db[self.col_name]
        logger.info(f'Connecting to MongoDB... {self.col}')

    async def handle_after(self, item):
        if self.primary_key:
            await self.col.update_one({self.primary_key: item[self.primary_key]},
                                      {'$set': item.content},
                                      upsert=True
                                      )
        else:
            await self.col.insert_one(item.content)

    async def on_close(self):
        self.client.close()


class ItemCollector(Handler):
    family = 'Item'

    async def on_start(self):
        self.do_web = self.crawler.web_enable
        if self.do_web:
            self.crawler.web_items = {}

    async def handle_after(self, task):
        if self.do_web and task.ancestor.startswith('@web'):
            li = self.crawler.web_items.setdefault(task.ancestor, [])
            li.append(task.content)


# Others

class CrawlerStartAddon(Handler):
    family = 'CrawlerStart'

    async def on_start(self):
        self.redis = None
        self.do_redis = self.crawler.redis_enable
        self.do_web = self.crawler.web_enable

        if self.do_redis:
            aioredis = check_import('aioredis')
            self.redis = await aioredis.create_redis_pool(address=self.crawler.config.get('REDIS_ADDRESS'))
            self.crawler.redis = self.redis
            self.crawler.counter = RedisCounter(self.crawler)
            self.crawler.counter.redis = self.redis

        if self.do_web:
            web = check_import('acrawler.web')
            self.web_runner = await web.runweb(self.crawler)

    async def handle_after(self, task):
        if self.do_redis:
            self.redis_start_key = self.crawler.config.get('REDIS_START_KEY')
            self.crawler.create_task(
                self._next_requests_from_redis_start())

    async def _next_requests_from_redis_start(self):
        start_key = self.crawler.config.get('REDIS_START_KEY')
        if start_key:
            while True:
                url = await self.redis.spop(start_key)
                if url:
                    url = url.decode()
                    task = Request(url,
                                   callback=self.crawler.parse)
                    await self.crawler.add_task(task)
                else:
                    await asyncio.sleep(0.5)

    async def on_close(self):
        if self.do_web:
            await self.web_runner.cleanup()
