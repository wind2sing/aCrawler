import time
import logging
from inspect import iscoroutinefunction
from acrawler.middleware import middleware
from acrawler.utils import to_asyncgen
import asyncio


# Typing
from typing import Union, Optional, Any, AsyncGenerator, Callable, Dict, List
import acrawler

_Middleware = 'acrawler.middleware._Middleware'
_Crawler = 'acrawler.crawler.Crawler'
_Function = Callable
_TaskGenerator = AsyncGenerator['Task', None]

logger = logging.getLogger(__name__)

class Task:
    """Task is scheduled by crawler to execute.

    :param dont_filter: if True, every instance of the Task will be considered
        as new task. Otherwise fingerprint will be checked to prevent duplication.
    :param fingerprint_func: A function that receives Task as parameter.
    :param priority: Tasks are scheduled in priority order (higher first). 
        If priorities are same, the one initialized earlier executes first.(FIFO)
    :param meta: additional information about a task. It can be used with
        :attr:`fingerprint`, :meth:`execute` or middleware's methods. If a task's
        execution yields new task, old task's meta should be passed to the new one.
    :param family: used to distinguish task's type.
        Defaults to `__class__.__name__`.
    """

    def __init__(self,
                 dont_filter: bool = False,
                 priority: int = 0,
                 meta: dict = None,
                 family=None,
                 _middleware=None):

        self.dont_filter = dont_filter
        self.priority = priority
        self.meta = meta or {}


        self.families = set(b.__name__ for b in self.__class__.__bases__)
        self.families.add(self.__class__.__name__)
        if family:
            self.families.add(family)
        self.primary_family = family or self.__class__.__name__

        self.middleware = _middleware or middleware
        self.crawler = self.middleware.crawler

        #: Every execution increase it by 1. If a task's :attr:`tries` is
        #: larger than scheduler's :attr:`max_tries`, it will fail.
        #: Defaults to 0.
        self.tries = 0

        #: The timestamp of task's initializing time.
        self.initime = time.time()

        #: The timestamp of task'last execution time.
        self.exetime = None

    @property
    def score(self):
        """Implements its real priority based on :attr:`initime` and :attr:`priority`"""
        return self._score()

    def _score(self):
        return self.priority*10000000000 - self.initime

    @property
    def fingerprint(self):
        """returns value of :meth:`_fingerprint`."""
        return self._fingerprint()

    async def execute(self,
                      **kwargs: Any)->_TaskGenerator:
        """main entry for a task to start working.

        :param middleware: needed to call custom functions before or after executing work.
        :param kwargs: additional keyword args will be passed to :meth:`_execute`
        :return: an asyncgenerator yields Task.
        """
        self.exetime = time.time()
        self.tries += 1

        for handler in self.middleware.handlers:
            await handler.handle(position=1, task=self)

        async for task in self._execute(**kwargs):
            yield task

        for handler in self.middleware.handlers:
            await handler.handle(position=2, task=self)

    async def _execute(self, **kwargs: Any)->_TaskGenerator:
        """should be rewritten as a generator in the subclass."""
        raise NotImplementedError

    def _fingerprint(self):
        """should be rewritten as a fingerprint calculator in the subclass."""
        raise NotImplementedError

    def __getstate__(self):
        state = self.__dict__
        del state['middleware']
        del state['crawler']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.__dict__['middleware'] = middleware
        self.__dict__['crawler'] = middleware.crawler


class DummyTask(Task):

    def __init__(self, val, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.val = val

    def _fingerprint(self):
        return self.val

    def _execute(self):
        print(self.val)
        yield None


class SpecialTask(Task):
    """Task that is special and not generate new tasks.
    """
    async def execute(self,
                      **kwargs: Any)->None:
        self.exetime = time.time()
        self.tries += 1

        for handler in self.middleware.handlers:
            await handler.handle(position=1, task=self)

        await self._execute(**kwargs)

        for handler in self.middleware.handlers:
            await handler.handle(position=2, task=self)


class CrawlerStart(SpecialTask):

    def __init__(self, crawler: _Crawler):
        self.crawler = crawler
        super().__init__()

    async def _execute(self):
        await self._produce_tasks()

    async def _produce_tasks(self):
        logger.info("Produce initial tasks...")
        async for task in to_asyncgen(self.crawler.start_requests):
            if await self.crawler.schedulers['Request'].produce(task):
                self.crawler.counter.task_add()

class CrawlerFinish(SpecialTask):

    def __init__(self, crawler: _Crawler):
        self.crawler = crawler
        super().__init__()

    async def _execute(self):
        await self._wait_finished()

    async def _wait_finished(self):
        await self.crawler.counter.join()
        for tasker in self.crawler.taskers:
            tasker.cancel()

        logger.info('All tasks finished!')
        logger.info(f'{self.crawler.counter.counts}')
