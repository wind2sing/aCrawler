import time
import logging
from inspect import iscoroutinefunction, isabstract
from acrawler.middleware import middleware
from acrawler.utils import to_asyncgen
import asyncio


# Typing
from typing import Union, Optional, Any, AsyncGenerator, Callable, Dict, List
import acrawler

_Middleware = "acrawler.middleware._Middleware"
_Crawler = "acrawler.crawler.Crawler"
_Function = Callable
_TaskGenerator = AsyncGenerator["Task", None]

logger = logging.getLogger(__name__)


class Task:
    """Task is scheduled by crawler to execute.

    :param dont_filter: if True, every instance of the Task will be considered
        as new task. Otherwise fingerprint will be checked to prevent duplication.
    :param ignore_exception: if True, any exception catched from the task's 
        execution will not retry the task.
    :param fingerprint_func: A function that receives Task as parameter.
    :param priority: Tasks are scheduled in priority order (higher first). 
        If priorities are same, the one initialized earlier executes first.(FIFO)
    :param meta: additional information about a task. It can be used with
        :attr:`fingerprint`, :meth:`execute` or middleware's methods. If a task's
        execution yields new task, old task's meta should be passed to the new one.
    :param family: used to distinguish task's type.
        Defaults to `__class__.__name__`.
    """

    def __init__(
        self,
        dont_filter: bool = False,
        ignore_exception: bool = False,
        priority: int = 0,
        meta: dict = None,
        family=None,
        recrawl: int = 0,
        exetime=0,
    ):

        self.dont_filter = dont_filter
        self.ignore_exception = ignore_exception
        self.priority = priority
        self.meta = meta or {}

        self.families = set(
            cls.__name__ for cls in self.__class__.mro() if not isabstract(cls)
        )
        if family:
            self.families.add(family)
        self.primary_family = family or self.__class__.__name__
        self._ancestor = ""

        self.crawler = self.middleware.crawler

        #: Every execution increase it by 1. If a task's :attr:`tries` is
        #: larger than scheduler's :attr:`max_tries`, it will fail.
        #: Defaults to 0.
        self.tries = 0

        self.recrawl = recrawl

        #: The timestamp of task's initializing time.
        self.init_time = time.time()

        #: The timestamp of task' expected execution time.
        if exetime > 0:
            self.exetime = exetime
        else:
            self.exetime = self.init_time

        #: The timestamp of task' last execution time.
        self.last_crawl_time = None

        #: a list to store exceptions occurs during execution
        self.exceptions = None

    @property
    def score(self):
        """Implements its real priority based on :attr:`expecttime` and :attr:`priority`"""
        return self._score()

    def _score(self):
        return self.priority * 10000000000 - self.exetime

    @property
    def fingerprint(self):
        """returns value of :meth:`_fingerprint`."""
        return self._fingerprint()

    @property
    def ancestor(self):
        return self._ancestor

    @ancestor.setter
    def ancestor(self, value: str):
        self._ancestor = value

    @property
    def middleware(self):
        return middleware

    async def execute(self, **kwargs: Any) -> _TaskGenerator:
        """main entry for a task to start working.

        :param middleware: needed to call custom functions before or after executing work.
        :param kwargs: additional keyword args will be passed to :meth:`_execute`
        :return: an asyncgenerator yields Task.
        """
        self.last_crawl_time = time.time()
        self.tries += 1
        self.exceptions = []

        # for handler in self.middleware.handlers:
        #     await handler.handle(position=1, task=self)

        # async for task in self._execute(**kwargs):
        #     if isinstance(task, Exception):
        #         if 'Immediately' in task.__class__.__name__:
        #             raise task
        #         self.exceptions.append(task)
        #     else:
        #         yield task

        # for handler in self.middleware.handlers:
        #     await handler.handle(position=2, task=self)

        for handler in self.middleware.handlers:
            async for task in self._sandbox(handler.handle, position=1, task=self):
                yield task

        async for task in self._sandbox(self._execute, **kwargs):
            yield task

        for handler in self.middleware.handlers:

            async for task in self._sandbox(handler.handle, position=2, task=self):
                yield task

        for exception in self.exceptions:
            raise exception

    async def _sandbox(self, func, *args, **kwargs) -> _TaskGenerator:
        """Wrap to the async generator and catch the exceptions during work."""
        try:
            async for task in to_asyncgen(func, *args, **kwargs):
                yield task
        except Exception as e:
            if "Immediately" in e.__class__.__name__:
                raise e
            else:
                self.exceptions.append(e)

    async def _execute(self, **kwargs: Any) -> _TaskGenerator:
        """should be rewritten as a generator in the subclass."""
        raise NotImplementedError

    def _fingerprint(self):
        """should be rewritten as a fingerprint calculator in the subclass."""
        return self.__hash__()

    def __lt__(self, other):
        return self.score < other.score

    def __getstate__(self):
        state = self.__dict__
        state.pop("crawler", None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.__dict__["crawler"] = self.middleware.crawler

    def __str__(self):
        return f"<Task {self.primary_family}>"


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

    async def execute(self, **kwargs: Any) -> None:
        self.exetime = time.time()
        self.tries += 1
        self.exceptions = []

        for handler in self.middleware.handlers:
            async for _ in self._sandbox(handler.handle, position=1, task=self):
                pass

        async for _ in self._sandbox(self._execute, **kwargs):
            pass

        for handler in self.middleware.handlers:
            async for _ in self._sandbox(handler.handle, position=2, task=self):
                pass

        for exception in self.exceptions:
            raise exception
