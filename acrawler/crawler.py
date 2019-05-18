from typing import List, Dict
import asyncio
import logging
import time
import traceback


from acrawler.task import Task, CrawlerStart, CrawlerFinish
from acrawler.http import Request
from acrawler.scheduler import Scheduler, RedisDupefilter, RedisPQ
from acrawler.middleware import middleware
from acrawler.utils import merge_config, config_from_setting
from acrawler.item import DefaultItem

import acrawler.setting as DEFAULT_SETTING
from importlib import import_module
from collections import defaultdict
from pprint import pformat

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


logger = logging.getLogger(__name__)


class Worker:
    """Worker do the task's work.

    One :class:`Crawler` will create many workers. A worker will
    - calls its scheduler's methods
    - implements task's retry mechanism
    - counts success and error
    """

    def __init__(self, crawler: 'Crawler', sdl: Scheduler = None, ):
        self.crawler = crawler
        self.sdl = sdl or Scheduler()
        self._max_tries = self.crawler.max_tries

    async def work(self):
        try:
            while True:
                task = await self.sdl.consume()
                exception = False
                try:
                    async for new_task in task.execute():
                        added = False
                        if isinstance(new_task, Task):
                            if isinstance(new_task, Request):
                                added = await self.crawler.sdl_req.produce(new_task)
                            else:
                                added = await self.crawler.sdl.produce(new_task)
                        elif isinstance(new_task, dict):
                            item = DefaultItem(extra=new_task)
                            added = await self.crawler.sdl.produce(item)
                        elif isinstance(new_task, Exception):
                            exception = True
                        if added:
                            self.crawler.counter.task_add()
                except Exception:
                    logger.error(traceback.format_exc())
                    exception = True
                if exception:
                    logger.warning(
                        'Task failed %s for %d times.', task, task.tries)
                    if task.tries < self._max_tries:
                        task.dont_filter = True
                        await self.sdl.produce(task)
                        self.crawler.counter.task_add()
                    else:
                        logger.warning(
                            'Drop the task %s', task)
                    self.crawler.counter.task_done(task, 0)
                else:
                    self.crawler.counter.task_done(task, 1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(traceback.format_exc())


class Counter:
    def __init__(self, loop=None):
        self.counts = defaultdict(lambda: [0, 0])
        self._unfinished_tasks = 0
        self._finished = asyncio.Event(loop=loop)
        self._finished.set()
        self.always_lock = False

    def lock_always(self):
        self._finished.clear()
        self.always_lock = True

    async def join(self):
        if self.always_lock:
            await self._finished.wait()
        else:
            if self._unfinished_tasks > 0:
                await self._finished.wait()

    def task_add(self):
        self._unfinished_tasks += 1
        self._finished.clear()

    def task_done(self, task, success: int = 1):
        for family in task.families:
            self.counts[family][success] += 1
        if self.always_lock:
            self._unfinished_tasks -= 1
        else:
            if self._unfinished_tasks <= 0:
                raise ValueError('task_done() called too many times')
            self._unfinished_tasks -= 1
            if self._unfinished_tasks == 0:
                self._finished.set()


class Crawler(object):
    #: Every task will try to execute for `max_tries` times.
    max_tries: int = 3

    #: Every crawler will obtain `max_requests` request concurrently.
    max_requests: int = 5

    #: Ready for vanilla :meth:`start_requests`
    start_urls: List[str] = []

    #: Shortcuts for parsing response, ready for appending middleware.
    Parsers: List['Parser'] = []

    request_config = {}
    config = {}
    middleware_config = {}
    meta = {}

    def __init__(self):

        self.loop = asyncio.get_event_loop()
        if not hasattr(self, 'max_workers'):
            self.max_workers = self.max_requests

        self._form_config()
        self._logging_config()

        self._create_schedulers()
        self.workers: List['Worker'] = []

        self.middleware = middleware
        self.middleware.crawler = self
        self._add_default_middleware_handler_cls()
        logger.info("Initializing middleware's handlers...")
        logger.info(self.middleware)
        self.counter = Counter(loop=self.loop)

    def run(self):
        """Wraps :meth:`manager` and wait until all tasks finish."""

        return self.loop.run_until_complete(self.arun())

    async def arun(self):
        """Wraps :meth:`manager` and wait until all tasks finish."""

        logger.info("Start crawling...")
        await self._on_start()
        await CrawlerStart(self).execute()
        await self.manager()

        await CrawlerFinish(self).execute()
        await self._on_close()
        logger.info("End crawling...")
        self._log_status()
        return True

    async def manager(self):
        """Manages crawler's most important work.

        - ensures status logger coroutine
        - creates multiple workers to do tasks.
        """
        try:
            self.loop.create_task(self._log_status_timer())

            for _ in range(self.max_requests):
                self.workers.append(Worker(self, self.schedulers['Request']))
            for _ in range(self.max_workers):
                self.workers.append(Worker(self, self.schedulers['Default']))
            logger.info('Create %d request workers', self.max_requests)
            logger.info('Create %d workers', self.max_workers)
            self.start_time = time.time()
            self.taskers = []
            for worker in self.workers:
                self.taskers.append(self.loop.create_task(worker.work()))

        except Exception:
            logger.error(traceback.format_exc())

    async def start_requests(self):
        """Should be rewritten for your custom spider.

        Otherwise it will yield every url in :attr:`start_urls`.
        """
        for url in self.start_urls:
            yield Request(url)

    async def add_task(self, task, sdl_name='Request'):
        if await self.schedulers[sdl_name].produce(task):
            self.counter.task_add()

    def _form_config(self):
        d_config, d_rq_config, d_m_config = config_from_setting(
            DEFAULT_SETTING)
        try:
            USER_SETTING = import_module('setting')
            u_config, u_rq_config, u_m_config = config_from_setting(
                USER_SETTING)
        except ModuleNotFoundError:
            u_config, u_rq_config, u_m_config = ({}, {}, {})

        self.config = merge_config(
            d_config, u_config, self.config
        )
        self.request_config = merge_config(
            d_rq_config, u_rq_config, self.request_config
        )
        self.middleware_config = merge_config(
            d_m_config, u_m_config, self.middleware_config
        )

    def _logging_config(self):
        level = self.config.get('LOG_LEVEL')
        logging.getLogger('acrawler').setLevel(level)
        logger.debug("Merging configs...")
        logger.debug(
            f'config: \n{pformat(self.config)}')
        logger.debug(
            f'request_config: \n{pformat(self.request_config)}')
        logger.debug(
            f'middleware_config:\n {pformat(self.middleware_config)}')

    def _create_schedulers(self):
        self.redis_enable = self.config.get('REDIS_ENABLE', False)

        request_df = None
        request_q = None
        if self.redis_enable:
            request_df = RedisDupefilter(
                address=self.config.get('REDIS_ADDRESS'),
                df_key=self.config.get('REDIS_DF_KEY')
            )
            request_q = RedisPQ(
                address=self.config.get('REDIS_ADDRESS'),
                q_key=self.config.get('REDIS_QUEUE_KEY')
            )
        self.schedulers: Dict[str, 'Scheduler'] = {
            'Request': Scheduler(df=request_df, q=request_q),
            'Default': Scheduler()
        }
        self.sdl = self.schedulers['Default']
        self.sdl_req = self.schedulers['Request']

    def _add_default_middleware_handler_cls(self):
        for kv in self.middleware_config.items():
            name = kv[0]
            key = kv[1]
            if key != 0:
                p, h = name.rsplit('.', 1)
                mod = import_module(p)
                mcls = getattr(mod, h)
                mcls.priority = key
                self.middleware.append_handler_cls(mcls)


    async def _on_start(self):
        for sdl in self.schedulers.values():
            await sdl.start()
        logger.info("Call on_start()...")
        for handler in self.middleware.handlers:
            await handler.handle(0)

    async def _on_close(self):
        for sdl in self.schedulers.values():
            await sdl.close()
        logger.info("Call on_close()...")
        for handler in self.middleware.handlers:
            await handler.handle(3)

    async def _log_status_timer(self):
        while True:
            await asyncio.sleep(20)
            self._log_status()

    def _log_status(self):
        time_delta = time.time() - self.start_time
        logger.info(f'Statistic: working {time_delta:.2f}s')
        for family in self.counter.counts.keys():
            success = self.counter.counts[family][1]
            failure = self.counter.counts[family][0]
            logger.info(
                f'Statistic:{family:<15} ~ success {success}, failure {failure}')
        # logger.info(self.sdl_req.q.pq)
        # logger.info(self.sdl.q.pq)
