import asyncio
import functools
import inspect
import json
import logging
import time
from typing import Callable

from aiohttp import ClientSession, DummyCookieJar, TCPConnector


from acrawler.counter import RedisCounter
from acrawler.exceptions import ResponseStatusError
from acrawler.http import Request
from acrawler.middleware import Handler
from acrawler.utils import check_import

# typing
_Function = Callable
_Task = "acrawler.task.Task"
_Request = "acrawler.http.Request"
_Response = "acrawler.http.Response"
_Crawler = "acrawler.crawler.Crawler"

logger = logging.getLogger(__name__)

# Request Part


class RequestPrepareSession(Handler):
    family = "Request"

    async def on_start(self):
        self.disable_cookies = self.crawler.config.get("DISABLE_COOKIES", False)

        self.connector = TCPConnector(limit=None)
        if self.disable_cookies:
            self.session = self.session = ClientSession(
                connector=self.connector, cookie_jar=DummyCookieJar()
            )
        else:
            self.session = ClientSession(connector=self.connector)
        self.crawler.session = self.session

    async def handle_before(self, task):
        task.session = self.session

    async def on_close(self):
        await self.session.close()


class RequestPrepareBrowser(Handler):
    family = "BrowserRequest"

    async def on_start(self):
        launch = check_import("aninja.browser").launch
        CookiesManager = check_import("aninja.cookies").CookiesManager
        options = self.crawler.config.get("LAUNCH_OPTIONS", {})

        self.cookies_manager = CookiesManager()
        self.client = await launch(
            cookies_manager=self.cookies_manager, options=options
        )

    async def handle_before(self, req):
        req.client = self.client

    async def handle_after(self, req):
        req.client = None

    async def on_close(self):
        await self.client.close()


class ResponseCheckStatus(Handler):
    """check response's status and will retry the request if it failed.

    If the response is not allowed by crawler AND by request's parameters, it will be considered as failing and then retried.
    By default, any response with status rather than 200 will fail.
    """

    family = "Request"

    def on_start(self):
        self.status_allowed = self.crawler.config.get("STATUS_ALLOWED", None)
        self.allow_all = self.status_allowed == []
        self.deny_all = self.status_allowed is None

    async def handle_after(self, request: Request):
        if request.response:
            status = request.response.status
            ok_by_crawler = (
                self.allow_all
                or status == 200
                or (not self.deny_all and status in self.status_allowed)
            )

            if ok_by_crawler or request.response.ok:
                pass
            else:
                raise ResponseStatusError(status)


class RequestMergeConfig(Handler):
    """(before execution) merge `config` to :attr:`Request.request_config`."""

    family = "Request"

    def handle_before(self, request: _Request):
        h0 = self.crawler.request_config.get("headers", {})
        h1 = request.request_config.get("headers", {})
        h = {**h0, **h1}
        request.request_config = {
            **self.crawler.request_config,
            **request.request_config,
        }
        if h:
            request.request_config["headers"] = h


# Response Part


class ResponseAddCallback(Handler):
    """(before execution) add :meth:`Parser.parse` to :attr:`Response.callbacks`."""

    family = "Response"
    callback_table = {}

    def handle_before(self, response: _Response):
        if not response.bind_cbs:
            for parser in self.crawler.parsers:
                response.add_callback(parser.parse)

            if response.primary_family in self.callback_table:
                for fn in self.callback_table[response.primary_family]:
                    sig = inspect.signature(fn)
                    if "self" in sig.parameters:
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
    family = "Item"
    """Family of this handler."""

    address: str = "redis://localhost"
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

    items_key = "acrawler:items"
    """Key of the list at which item's content is inserted.
    """

    async def on_start(self):
        aioredis = check_import("aioredis")
        self.items_key = self.crawler.config.get("REDIS_ITEMS_KEY", self.items_key)
        self.redis = await aioredis.create_redis_pool(
            self.address, maxsize=self.maxsize, loop=self.crawler.loop
        )
        logger.info(f"Connecting to Redis... {self.redis}")

    async def handle_after(self, item):
        await self.redis.lpush(self.items_key, json.dumps(item.content))

    async def on_close(self):
        self.redis.close()
        await self.redis.wait_closed()


class ItemToMongo(Handler):
    family = "Item"
    """Family of this handler."""

    address = "mongodb://localhost:27017"
    """a full mongodb URI, in addition to a simple hostname"""

    db_name = ""
    """name of targeted database"""

    col_name = ""
    """name of targeted collection"""

    primary_key = ""

    async def on_start(self):
        mo = check_import("motor.motor_asyncio")
        self.client = mo.AsyncIOMotorClient(self.address)
        self.db = self.client[self.db_name]
        self.col = self.db[self.col_name]
        logger.info(f"Connecting to MongoDB... {self.col}")

    async def handle_after(self, item):
        if self.primary_key:
            await self.col.update_many(
                {self.primary_key: item[self.primary_key]},
                {"$set": item.content},
                upsert=True,
            )
        else:
            await self.col.insert_one(item.content)

    async def on_close(self):
        self.client.close()


class ItemCollector(Handler):
    family = "Item"

    async def on_start(self):
        self.do_web = self.crawler.web_enable
        self.crawler.web_items = {}

    async def handle_after(self, item):
        if item.ancestor.startswith("web@"):
            li = self.crawler.web_items.setdefault(item.ancestor, [])
            li.append(item.content)

        if item.store:
            li = self.crawler.storage.setdefault(item.primary_family, [])
            li.append(item)


# Others


class CrawlerStartAddon(Handler):
    family = "CrawlerStart"

    async def on_start(self):
        self.redis = None
        self.do_redis = self.crawler.redis_enable
        self.do_web = self.crawler.web_enable

        if self.do_redis:
            aioredis = check_import("aioredis")
            self.redis = await aioredis.create_redis_pool(
                address=self.crawler.config.get("REDIS_ADDRESS")
            )
            self.crawler.redis = self.redis
            self.crawler.counter = RedisCounter(self.crawler)
            self.crawler.counter.redis = self.redis

        if self.do_web:
            web = check_import("acrawler.web")
            self.web_runner = await web.runweb(self.crawler)

    async def handle_after(self, task):
        if self.do_redis:
            self.redis_start_key = self.crawler.config.get("REDIS_START_KEY")
            self.crawler.create_task(self._next_requests_from_redis_start())

    async def _next_requests_from_redis_start(self):
        start_key = self.crawler.config.get("REDIS_START_KEY")
        if start_key:
            while True:
                url = await self.redis.spop(start_key)
                if url:
                    url = url.decode()
                    task = Request(url, callback=self.crawler.parse)
                    await self.crawler.add_task(task)
                    await asyncio.sleep(0)
                else:
                    await asyncio.sleep(0.5)

    async def on_close(self):
        if self.do_web:
            await self.web_runner.cleanup()


class ExpiredWatcher(Handler):
    """Maintain a expired Event.

    You can set this event and then meth`custom_expired_worker` will be waken up to do
    bypassing work. You should overwrite meth`custom_on_start` if needed rather than
    default one.

    Args:
        expired: a Event to tell the worker that your token is expired.
        last_handle_time: a timestamp when the last work happened.
        ttl: if `set` signal is sent at a time that less than `last_handle_time` + `ttl`,
            it will be ignored.
    """

    last_handle_time = None
    ttl: int = 20
    delay_after_failed: int = 0

    def __init__(self, *args, **kwargs):
        self.expired = asyncio.Event()
        super().__init__(*args, **kwargs)

    async def on_start(self):
        self.crawler.create_task(self.expired_worker())
        await self.custom_on_start()

    async def custom_on_start(self):
        pass

    async def expired_worker(self):
        while True:
            await self.expired.wait()

            if (
                self.last_handle_time
                and time.time() - self.last_handle_time <= self.ttl
            ):
                self.expired.clear()
                continue

            logger.warning("Token is expired. Try to handle...")
            await asyncio.sleep(0)
            success = await self.custom_expired_worker()
            if success:
                self.last_handle_time = time.time()
                logger.warning("Hanling down, clear the Event 'expired'.")
                self.expired.clear()
            else:
                await asyncio.sleep(self.delay_after_failed)

    async def custom_expired_worker(self):
        pass
