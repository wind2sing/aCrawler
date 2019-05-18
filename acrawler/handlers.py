from acrawler.middleware import Handler, middleware
import importlib
import sys
import functools
import inspect
import json
import logging
from acrawler.http import Request
from acrawler.utils import check_import
import asyncio
from aiohttp import ClientSession

# Typing
import acrawler
from typing import List, Callable

_Function = Callable
_Task = 'acrawler.task.Task'
_Request = 'acrawler.http.Request'
_Response = 'acrawler.http.Response'
_Crawler = 'acrawler.crawler.Crawler'

logger = logging.getLogger(__name__)


class RequestPrepareSession(Handler):
    family = 'Request'

    async def on_start(self):
        self.session = ClientSession()
        self.crawler._session = self.session

    async def handle_before(self, task):
        task.session = self.session

    async def on_close(self):
        await self.session.close()


class ResponseCheckStatus(Handler):
    family = 'Response'

    async def handle_before(self, response):
        if response.status >= 400:
            logger.error('Task failed {}'.format(response))
            task = response.request
            if task.tries < self.crawler.max_tries:
                task.dont_filter = True
                await self.crawler.add_task(response.request)
            else:
                logger.warning(
                    'Drop the task %s', task)


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

    async def handle_after(self, request: _Request):
        await asyncio.sleep(self.crawler.config.get('DOWNLOAD_DELAY'))


class ResponseAddCallback(Handler):
    """a handler (before execution) which add :meth:`Parser.parse` to :attr:`Response.callbacks`."""

    family = 'Response'
    callback_table = {}

    def handle_before(self, response: _Response):
        for parser in self.crawler.Parsers:
            response.add_callback(parser.parse)

        if response.primary_family in self.callback_table:
            for fn in self.callback_table[response.primary_family]:
                sig = inspect.signature(fn)
                if 'self' in sig.parameters:
                    fn = functools.partial(fn, self.crawler)
                response.add_callback(fn)

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

class CrawlerStartAddon(Handler):
    family = 'CrawlerStart'

    async def on_start(self):
        if self.crawler.redis_enable:
            aioredis = check_import('aioredis')
            self.redis = await aioredis.create_redis(address=self.crawler.config.get('REDIS_ADDRESS'))
        else:
            self.redis = None

    async def handle_after(self, task):
        if self.crawler.redis_enable:
            self.crawler.loop.create_task(self._next_request_from_redis())

    async def _next_request_from_redis(self):
        while True:
            _, url = await self.redis.blpop(self.crawler.config.get('REDIS_START_KEY'))
            task = Request(str(url, encoding="utf-8"))
            if await self.crawler.schedulers['Request'].produce(task):
                self.crawler.counter.task_add()


class CrawlerFinishAddon(Handler):
    family = 'CrawlerFinish'

    async def on_start(self):
        if self.crawler.redis_enable:
            self.crawler.counter.lock_always()


class ItemDebug(Handler):
    family = 'Item'

    def handle_after(self, item):
        logger.debug(item.content)


class ItemToRedis(Handler):
    family = 'Item'
    maxsize = 10
    address = 'redis://localhost'
    default_key = 'acrawler:items'

    async def on_start(self):
        aioredis = check_import('aioredis')
        self.redis_key = self.crawler.config.get(
            'REDIS_ITEMS_KEY', self.default_key)
        self.redis = await aioredis.create_redis_pool(
            self.address,
            maxsize=self.maxsize,
            loop=self.crawler.loop)
        logger.info(f'Connecting to Redis... {self.redis}')

    async def handle_after(self, item):
        await self.redis.lpush(self.redis_key, json.dumps(
            item.content, skipkeys='_item_type'))

    async def on_close(self):
        self.redis.close()
        await self.redis.wait_closed()


class ItemToMongo(Handler):
    family = 'Item'
    address = 'mongodb://localhost:27017'
    db_name = ''
    col_name = ''

    async def on_start(self):
        import motor.motor_asyncio
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.address)
        self.db = self.client[self.db_name]
        self.col = self.db[self.col_name]
        logger.info(f'Connecting to MongoDB... {self.col}')

    async def handle_after(self, item):
        self.col.insert_one(item.content)

    async def on_close(self):
        self.client.close()
