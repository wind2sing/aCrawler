import asyncio
import logging
import dill as pickle
import signal
import sys
import time
import traceback
from copy import deepcopy
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, List

import acrawler
import acrawler.setting as DEFAULT_SETTING
from acrawler.counter import Counter
from acrawler.exceptions import ReScheduleError, SkipTaskError
from acrawler.http import Request
from acrawler.item import DefaultItem
from acrawler.middleware import middleware
from acrawler.scheduler import RedisDupefilter, RedisPQ, Scheduler
from acrawler.task import SpecialTask, Task
from acrawler.utils import (
    config_from_setting,
    merge_config,
    sync_coroutine,
    to_asyncgen,
)

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass


_Config = Dict[str, Any]
_Response = acrawler.http.Response

logger = logging.getLogger(__name__)


class Worker:
    """Worker execute the task.

    One :class:`Crawler` will create many workers. A worker will
    - calls its scheduler's methods
    - implements task's retry mechanism
    - catch the result of a task's execution
    """

    def __init__(self, crawler: "Crawler", sdl: Scheduler = None, is_req=False):
        self.crawler = crawler
        self.is_req = is_req
        self.sdl = sdl or Scheduler()
        self._max_tries = self.crawler.max_tries
        self.current_task = None

    async def work(self):
        try:
            while True:
                retry = False
                exception = False

                self.current_task = await self.sdl.consume()
                task = self.current_task

                try:
                    if self.is_req:
                        await self.crawler.counter.require_req(task)
                    async for new_task in task.execute():
                        await self.crawler.add_task(new_task, ancestor=task.ancestor)
                except asyncio.CancelledError as e:
                    if self.is_req:
                        await self.crawler.counter.release_req(task)
                    raise e
                except SkipTaskError:
                    logger.debug("Skip task {}".format(task))
                except ReScheduleError as e:
                    task.exetime = time.time() + e.defer
                    if e.recrawl:
                        task.recrawl = e.recrawl
                    await self.crawler.counter.task_done(task, -2)
                    await self.crawler.add_task(task, dont_filter=True, flag=-2)
                    if self.is_req:
                        await self.crawler.counter.release_req(task)
                    self.current_task = None
                    await asyncio.sleep(0.5)
                    continue
                except Exception as e:
                    exception = True
                    if not task.ignore_exception and task.tries < self._max_tries:
                        task.exetime = time.time()
                        await self.crawler.add_task(task, dont_filter=True)
                        retry = True
                        logger.error(
                            "{}->Retry...\n{}".format(
                                task, traceback.format_exc(chain=False)
                            )
                        )
                        await self.crawler.counter.task_done(task, -1)
                    else:
                        logger.error(
                            "{}->Drop!\n{}".format(
                                task, traceback.format_exc(chain=False)
                            )
                        )
                        await self.crawler.counter.task_done(task, 0)

                if not exception:
                    await self.crawler.counter.task_done(task, 1)

                if self.is_req:
                    await self.crawler.counter.release_req(task)

                if task.recrawl > 0 and not retry:
                    task.tries = 0
                    task.init_time = time.time()
                    task.exetime = task.last_crawl_time + task.recrawl
                    await self.crawler.add_task(task, dont_filter=True)
                self.current_task = None
        except asyncio.CancelledError as e:
            if self.current_task:
                self.current_task.tries -= 1
                task.dont_filter = True
                logger.info("During shutdown, put back {}".format(task))
                await self.sdl.produce(task)
            raise e
        except Exception as e:
            logger.error(traceback.format_exc())


class Crawler(object):
    """This is the base crawler, from which all crawlers that you write yourself must inherit.

    Attributes:

    """

    start_urls: List[str] = []
    """Ready for vanilla :meth:`start_requests`"""

    parsers: List["acrawler.Parser"] = []
    """Shortcuts for parsing response.

    Crawler will automatically append :meth:`acrawler.parser.Parser.parse` to response's
    callbacks list for each parser in parsers.
    """

    request_config: _Config = {}
    """Key-Value pairs will be passed as keyword arguments to every sended `aiohttp.request`.

    acceptable keyword
        params - Dictionary or bytes to be sent in the query string of the new request

        data - Dictionary, bytes, or file-like object to send in the body of the request

        json - Any json compatible python object

        headers - Dictionary of HTTP Headers to send with the request

        cookies - Dict object to send with the request

        allow_redirects - If set to False, do not follow redirects

        timeout - Optional ClientTimeout settings structure, 5min total timeout by default.
    """

    middleware_config: _Config = {}
    """Key-value pairs for handler-priority.

    Examples:
        Handler with higer priority handles the task earlier. Priority 0 will disable the handler::

            {
                'some_old_handler': 0,
                'myhandler_first': 1000,
                'myhandler': 500
            }

    """

    config: _Config = {}
    """Config dictionary for this crawler. See avaliable options in `setting`.
    """

    name = None

    def __init__(self, config:dict=None, middleware_config:dict=None, request_config:dict=None):
        """Initialization will:
        - load setting and configs
        - create scheduler/counter (may load from file)
        - spawn handlers with middleware_config

        """

        if self.__class__.name is None:
            self.__class__.name = self.__class__.__name__

        self.loop = asyncio.get_event_loop()

        self.config = config or self.config
        self.middleware_config = middleware_config or self.middleware_config
        self.request_config = request_config or self.request_config
        self._form_config()

        self.counter: Counter = None
        self.redis: "aioredis.Redis" = None
        self.workers: List["Worker"] = []
        self.taskers = {"Request": [], "Default": [], "Others": []}
        self.shedulers: Dict[str, "Scheduler"] = {}
        self._initialize_counter()
        self._initialize_schedulers()

        self.storage: dict = {}

        self.middleware = middleware
        """Singleton object :class:`acrawler.middleware.middleware`"""

        self.middleware.crawler = self
        self._add_default_middleware_handler_cls()
        self.config_logger()

    def run(self):
        """Core method of the crawler. Usually called to start crawling."""

        signals = (signal.SIGTERM, signal.SIGINT)
        for s in signals:
            self.loop.add_signal_handler(
                s, lambda s=s: self.loop.create_task(self.ashutdown(s))
            )

        self.run_task = self.loop.create_task(self.arun())
        self.loop.run_forever()

    async def arun(self):
        # Wraps main works and wait until all tasks finish.
        try:
            await self._persist_load()
            logger.debug("Checking middleware's handlers...")
            logger.info(self.middleware)
            logger.info("Start crawling...")
            await self._on_start()
            await CrawlerStart(self).execute()
            await self.manager()

            await CrawlerFinish(self).execute()
            await self.ashutdown()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.error(traceback.format_exc())

    async def manager(self):
        """Create multiple workers to execute tasks.
        """
        self.initial_counts = deepcopy(await self.counter.get_counts_dict())
        logger.info(
            "Normal tasks -> queue:{} waiting:{}".format(
                await self.sdl.q.get_length_of_pq(),
                await self.sdl.q.get_length_of_waiting(),
            )
        )
        logger.info(
            "Request tasks -> queue:{} waiting:{}".format(
                await self.sdl_req.q.get_length_of_pq(),
                await self.sdl_req.q.get_length_of_waiting(),
            )
        )
        self.max_requests = self.config.get("MAX_REQUESTS", 4)
        self.max_workers = self.config.get("MAX_WORKERS", self.max_requests)
        self.max_tries = self.config.get("MAX_TRIES", 3)
        try:
            self.loop.create_task(self._log_status_timer())
            for _ in range(self.max_requests):
                self.workers.append(Worker(self, self.sdl_req, is_req=True))
            for _ in range(self.max_workers):
                self.workers.append(Worker(self, self.sdl, is_req=False))
            logger.info(
                f"Create {self.max_requests} request workers, {self.max_workers} normal workers"
            )
            self.start_time = time.time()
            for worker in self.workers:
                self.taskers["Default"].append(self.loop.create_task(worker.work()))

        except Exception:
            logger.error(traceback.format_exc())

    async def start_requests(self):
        """Should be rewritten for your custom spider.

        Otherwise it will yield every url in :attr:`start_urls`. Any Request yielded from :meth:`start_requests`
        will combine :meth:`parse` to its callbacks and passes all callbacks to Response
        """
        for url in self.start_urls:
            yield Request(url)

    async def parse(self, response: _Response):
        """ Default callback function for Requests generated by default :meth:`start_requests`.

        Args:
            response: the response task generated from corresponding request.
        """
        yield None

    def web_add_task_query(self, query: dict):
        """ This method is to deal with web requests if you enable the web service. New tasks should be
        yielded in this method. And Crawler will finish tasks to send response. Should be overwritten.

        Args:
            query: a multidict.
        """
        url = query.pop("url", "")
        if url:
            task = Request(url=url, **query)
            yield task
        else:
            raise Exception("Not valid url from web request!")
        yield None

    def web_action_after_query(self, items):
        """ Action to be done after the web service finish the query and tasks. Should be overwritten.
        """
        return items

    async def add_then_wait(self, *tasks):
        ancestor = "web@" + str(time.time())
        for task in tasks:
            await self.add_task(task, dont_filter=True, ancestor=ancestor)

        await self.counter.join_by_ancestor_unfinished(ancestor)
        items = self.web_items.pop(ancestor, [])
        return items

    async def add_task(
        self, new_task: "acrawler.task.Task", dont_filter=False, ancestor=None, flag=1
    ) -> bool:
        """ Interface to add new Task to scheduler.

        Args:
            new_task: a Task or a dictionary which will be catched as :class:`~acrawler.item.DefaultItem` task.

        Returns:
            True if the task is successfully added.
        """
        added = False
        if isinstance(new_task, Task):
            if ancestor:
                new_task.ancestor = ancestor
            if isinstance(new_task, Request):
                added = await self.sdl_req.produce(new_task, dont_filter=dont_filter)
            else:
                added = await self.sdl.produce(new_task, dont_filter=dont_filter)
        elif isinstance(new_task, dict):
            new_task = DefaultItem(extra=new_task)
            if ancestor:
                new_task.ancestor = ancestor
            added = await self.sdl.produce(new_task, dont_filter=dont_filter)
        if added:
            await self.counter.task_add(new_task, flag=flag)
            return new_task
        else:
            return False

    def add_task_sync(
        self, new_task: "acrawler.task.Task", dont_filter=False, ancestor=None
    ):
        return sync_coroutine(self.add_task(new_task, dont_filter, ancestor))

    def _form_config(self):
        # merge configs from three levels of sources
        d_config, d_rq_config, d_m_config = config_from_setting(DEFAULT_SETTING)
        try:
            path = (Path.cwd() / sys.argv[0]).parent / "setting.py"
            spec = spec_from_file_location("acrawler.usersetting", path)
            USER_SETTING = module_from_spec(spec)
            spec.loader.exec_module(USER_SETTING)
            u_config, u_rq_config, u_m_config = config_from_setting(USER_SETTING)
        except (FileNotFoundError):
            u_config, u_rq_config, u_m_config = ({}, {}, {})

        self.config = merge_config(d_config, u_config, self.config)
        self.request_config = merge_config(
            d_rq_config, u_rq_config, self.request_config
        )
        self.middleware_config = merge_config(
            d_m_config, u_m_config, self.middleware_config
        )

    def config_logger(self):
        # log three types of config
        level = self.config.get("LOG_LEVEL", "INFO")
        to_file = self.config.get("LOG_TO_FILE", None)
        fmt = self.config.get("LOGGER_FMT", "%(asctime)s %(name)-20s%(levelname)-8s %(message)s")
        datefmt = self.config.get("LOGGER_DATE_FMT", "%Y-%m-%d %H:%M:%S")
        LOGGER = logging.getLogger("acrawler")
        LOGGER.handlers = []

        if to_file:
            handler = logging.FileHandler(to_file)
        else:
            handler = logging.StreamHandler()
        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
        handler.setFormatter(formatter)

        LOGGER.addHandler(handler)
        LOGGER.setLevel(level)

        logger.debug("Merging configs...")
        logger.debug(f"config: \n{pformat(self.config)}")
        logger.debug(f"request_config: \n{pformat(self.request_config)}")
        logger.debug(f"middleware_config:\n {pformat(self.middleware_config)}")

    @property
    def redis_enable(self):
        return self.config.get("REDIS_ENABLE", False)

    @property
    def web_enable(self):
        return self.config.get("WEB_ENABLE", False)

    @property
    def lock_always(self):
        return (
            self.redis_enable
            or self.web_enable
            or self.config.get("LOCK_ALWAYS", False)
        )

    @property
    def persistent(self):
        return self.config.get("PERSISTENT", False)

    def _initialize_counter(self):
        self.counter = Counter(crawler=self)

    def _initialize_schedulers(self):
        request_df = None
        request_q1 = None
        request_q2 = None
        if self.redis_enable:
            request_df = RedisDupefilter(
                address=self.config.get("REDIS_ADDRESS"),
                df_key=self.config.get("REDIS_DF_KEY")
                or "acrawler:" + self.name + ":df",
            )
            request_q1 = RedisPQ(
                address=self.config.get("REDIS_ADDRESS"),
                q_key=(self.config.get("REDIS_QUEUE_KEY") or ("acrawler:" + self.name))
                + ":q1",
            )
            request_q2 = RedisPQ(
                address=self.config.get("REDIS_ADDRESS"),
                q_key=(self.config.get("REDIS_QUEUE_KEY") or ("acrawler:" + self.name))
                + ":q2",
            )

        self.sdl_req = Scheduler(df=request_df, q=request_q1)
        self.sdl = Scheduler(df=request_df, q=request_q2)

    def _add_default_middleware_handler_cls(self):
        # append handlers from middleware_config.
        for kv in self.middleware_config.items():
            name = kv[0]
            key = kv[1]
            if key:
                p, h = name.rsplit(".", 1)
                mod = import_module(p)
                mcls = getattr(mod, h)
                if key is True:
                    pass
                else:
                    mcls.priority = key
                self.middleware.append_handler_cls(mcls)

    async def next_requests(self):
        """This method will be binded to the event loop as a task. You can add task manually in this method."""
        pass

    def create_task(self, coro):
        async def wrapper(awaitable):
            try:
                return await awaitable
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(traceback.format_exc())

        task = self.loop.create_task(wrapper(coro))
        self.taskers["Others"].append(task)
        return task

    async def _on_start(self):
        # call handlers's on_start()
        await self.sdl.start()
        await self.sdl_req.start()
        logger.debug("Call on_start()...")
        for handler in self.middleware.handlers:
            async for task in handler.handle(0):
                await self.add_task(task)

    async def _on_close(self):
        # call handlers's on_close()
        await self.sdl.close()
        await self.sdl_req.start()
        logger.debug("Call on_close()...")
        for handler in self.middleware.handlers:
            async for task in handler.handle(3):
                await self.add_task(task)

    async def ashutdown(self, sig=None):
        # shutdown method.
        #
        # - cancel all Request workers
        # - wait for all nonRequest workers
        # - deal with keyboardinterrupt.
        # - save current status if persistent

        logger.info("Start shutdown...")
        try:
            for tasker in self.taskers["Others"]:
                tasker.cancel()

            for tasker in self.taskers["Others"]:
                try:
                    await tasker
                except Exception:
                    pass

            for tasker in self.taskers["Default"]:
                tasker.cancel()

            for tasker in self.taskers["Default"]:
                try:
                    await tasker
                except Exception:
                    pass

            await self._log_status()
            await self._on_close()
            await self._persist_save()
            if sig:
                self.run_task.cancel()

            logger.debug("Shutdown crawler gracefully!")
            logger.info("End crawling...")
            self.loop.stop()
        except Exception as e:
            logger.warning("Errors during shutdown: {}".format(e))
            logger.error(traceback.format_exc())
            self.loop.stop()
        finally:
            signals = (signal.SIGTERM, signal.SIGINT)
            for s in signals:
                self.loop.remove_signal_handler(s)

    async def _persist_load(self):
        if self.persistent and not self.redis_enable:
            tag = self.config.get("PERSISTENT_NAME", None) or ".acrawler." + self.name
            fname = tag
            self.fi_counter: Path = Path.cwd() / (fname + ".counter")
            self.fi_tasks: Path = Path.cwd() / (fname + ".tasks")
            self.fi_reqs: Path = Path.cwd() / (fname + ".reqs")
            self.fi_df: Path = Path.cwd() / (fname + ".df")
            self.fi_store: Path = Path.cwd() / (fname + ".store")
            if self.fi_counter.exists():
                with open(self.fi_counter, "rb") as f:
                    self.counter = pickle.load(f)

            tasks = []
            if self.fi_tasks.exists():
                with open(self.fi_tasks, "rb") as f:
                    tasks = pickle.load(f)
                for t in tasks:
                    self.sdl.q.push_nowait(t)

            reqs = []
            if self.fi_reqs.exists():
                with open(self.fi_reqs, "rb") as f:
                    reqs = pickle.load(f)
                for t in reqs:
                    self.sdl_req.q.push_nowait(t)

            logger.info(f"Load {len(reqs)} requests from local file.")
            logger.info(f"Load {len(tasks)} normal tasks from local file.")

            if self.fi_df.exists():
                with open(self.fi_df, "rb") as f:
                    self.sdl.df = pickle.load(f)

            if self.fi_store.exists():
                with open(self.fi_store, "rb") as f:
                    self.storage = pickle.load(f)

    async def _persist_save(self):
        if self.persistent and not self.redis_enable:
            with open(self.fi_counter, "wb") as f:
                pickle.dump(self.counter, f)
            tasks = []
            with open(self.fi_tasks, "wb") as f:
                while 1:
                    try:
                        t = self.sdl.q.pq.get_nowait()[1]
                        tasks.append(t)
                    except asyncio.QueueEmpty:
                        break
                while 1:
                    try:
                        t = self.sdl.q.waiting.get_nowait()[1]
                        tasks.append(t)
                    except asyncio.QueueEmpty:
                        break
                pickle.dump(tasks, f)

            reqs = []
            with open(self.fi_reqs, "wb") as f:
                while 1:
                    try:
                        t = self.sdl_req.q.pq.get_nowait()[1]
                        reqs.append(t)
                    except asyncio.QueueEmpty:
                        break
                while 1:
                    try:
                        t = self.sdl_req.q.waiting.get_nowait()[1]
                        reqs.append(t)
                    except asyncio.QueueEmpty:
                        break
                pickle.dump(reqs, f)
            logger.info(f"Dump {len(reqs)} requests into local file.")
            logger.info(f"Dump {len(tasks)} normal tasks from local file.")

            with open(self.fi_df, "wb") as f:
                pickle.dump(self.sdl.df, f)

            with open(self.fi_store, "wb") as f:
                pickle.dump(self.storage, f)

    async def _log_status_timer(self):
        delta = self.config["LOG_TIME_DELTA"]
        if delta:
            while True:
                await asyncio.sleep(delta)
                await self._log_status()

    async def _log_status(self):
        time_delta = time.time() - self.start_time
        logger.info(f"Statistic: working {time_delta:.2f}s")
        counts_dict = await self.counter.get_counts_dict()
        for family in counts_dict.keys():
            success = counts_dict[family][1]
            failure = counts_dict[family][0]
            speed = (
                int((success - self.initial_counts.get(family, (0, 0))[1]) / 30) * 60
            )
            logger.info(
                f"Statistic: {family:<13} ~ success {success:<5}, fail {failure:<4} ~ {speed}/min in the past 30s"
            )
        self.initial_counts = deepcopy(counts_dict)
        logger.info(
            "Normal tasks left--- queue:{} waiting:{}".format(
                await self.sdl.q.get_length_of_pq(),
                await self.sdl.q.get_length_of_waiting(),
            )
        )
        logger.info(
            "Request tasks left--- queue:{} waiting:{}".format(
                await self.sdl_req.q.get_length_of_pq(),
                await self.sdl_req.q.get_length_of_waiting(),
            )
        )

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        self.__dict__.update(middleware.crawler.__dict__)


class CrawlerStart(SpecialTask):
    """ A special task that executes when crawler starts.
    It will call :meth:`Crawler.start_requests` to yield tasks.
    """

    def __init__(self, crawler):
        self.crawler: Crawler = crawler
        self.loop = self.crawler.loop
        super().__init__()

    async def _execute(self):
        await self._produce_tasks_from_start_requests()
        self.crawler.create_task(self.crawler.next_requests())

    async def _produce_tasks_from_start_requests(self):
        logger.debug("Produce initial tasks...")
        async for task in to_asyncgen(self.crawler.start_requests):
            if isinstance(task, Request):
                if not task.callbacks:
                    task.add_callback(self.crawler.parse)
                await self.crawler.add_task(task)
            elif isinstance(task, Task):
                await self.crawler.add_task(task)


class CrawlerFinish(SpecialTask):
    """A special task that executes after creating all workers.
    It will block the crawler from shutdown until all tasks finish.
    """

    def __init__(self, crawler):
        self.crawler: Crawler = crawler
        super().__init__()
        self.dummy = asyncio.Event(loop=self.crawler.loop)
        self.dummy.clear()

    async def _execute(self):
        await self._wait_finished()

    async def _wait_finished(self):
        if self.crawler.lock_always:
            await self.dummy.wait()
        else:
            await self.crawler.counter.join()
