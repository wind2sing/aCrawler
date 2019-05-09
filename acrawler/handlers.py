from acrawler.middleware import Handler
import importlib
import sys

import json
import logging
from acrawler.http import Request
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

    async def handle_before(self, task: _Task):
        task.session = self.session

    async def on_close(self):
        await self.session.close()


class ResponseAddParser(Handler):
    """a handler (before execution) which add :meth:`Parser.parse` to :attr:`Response.callbacks`."""

    family = 'Response'

    def handle_before(self, response: _Response):
        for parser in self.crawler.Parsers:
            response.add_callback(parser.parse)


class RequestMergeConfig(Handler):
    """a handler (before execution) which merge `config` to :attr:`Request.request_config`."""
    family = 'Request'

    def handle_before(self, request: _Request):
        h0 = self.crawler.request_config.get('headers',{})
        h1 = request.request_config.get('headers',{})
        h = {**h0, **h1}
        request.request_config = {
            **self.crawler.request_config, **request.request_config}
        if h:
            request.request_config['headers'] = h


class RequestDelay(Handler):
    family = 'Request'

    async def handle_after(self, request: _Request):
        await asyncio.sleep(self.crawler.config.get('DOWNLOAD_DELAY'))


class CrawlerStartAddon(Handler):
    family = 'CrawlerStart'

    async def on_start(self):
        if self.crawler.redis_enable:
            if 'aioredis' not in sys.modules:
                importlib.import_module('aioredis')
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
        item.logger.debug(item.content)


class ItemToRedis(Handler):
    family = 'Item'
    maxsize = 10
    address = 'redis://localhost'
    default_key = 'acrawler:items'

    async def on_start(self):
        if 'aioredis' not in sys.modules:
            importlib.import_module('aioredis')
        self.redis_key = self.crawler.config.get(
            'redis_items_key', self.default_key)
        self.redis = await aioredis.create_redis_pool(
            self.address,
            maxsize=self.maxsize,
            loop=self.crawler.loop)
        self.logger.info(f'Connecting to Redis... {self.redis}')

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
        self.logger.info(f'Connecting to MongoDB... {self.col}')

    async def handle_after(self, item):
        self.col.insert_one(item.content)

    async def on_close(self):
        self.client.close()
