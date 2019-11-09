import time
import logging
from inspect import iscoroutinefunction, isabstract
from ..utils import to_asyncgen
import asyncio
from collections import defaultdict
from ..plugins import middleware
from ..exceptions import SkipTaskError, ReScheduleError

# Typing
from typing import Union, Optional, Any, AsyncGenerator, Callable, Dict, List
import typing

if typing.TYPE_CHECKING:
    from .. import Crawler, Plugin
_TaskGenerator = AsyncGenerator["Task", None]

logger = logging.getLogger(__name__)


class Task:
    """Task is scheduled to execute.

    :param priority: Tasks are scheduled in priority order (higher first).
        If priorities are same, the one initialized earlier executes first.(FIFO)
    :param meta: additional information about a task. It can be used with
        :attr:`fingerprint`, :meth:`execute` or middleware's methods. If a task's
        execution yields new task, old task's meta should be passed to the new one.
    :param family: used to distinguish task's type
    :param options: additional keyword arguments will be stored in this defaultdict.
    """

    def __init__(
        self,
        priority: int = 0,
        meta: dict = None,
        family: str = None,
        exetime=0,
        **kwargs,
    ):
        self.priority: int = priority

        #: passing information between tasks
        self.meta: "dict" = meta or {}

        #: store status information, used for various plugins
        self.status: "dict" = defaultdict(lambda: None)

        #: store additional configuration, used for various plugins
        self.options: "dict" = defaultdict(lambda: None)
        self.options.update(kwargs)

        #: families are a set from class cls’s base classes, including cls
        self.families: "set" = set(
            cls.__name__ for cls in self.__class__.mro() if not isabstract(cls)
        )
        if family:
            self.families.add(family)

        #: primary family, from argument, defaults to `__class__.__name__`.
        self.family: str = family or self.__class__.__name__

        #: tasks generated from a same root task will have same ancestor value
        self.ancestor: str = ""

        #: The timestamp of task' expected execution time.
        if exetime > 0:
            self.exetime = exetime
        else:
            self.exetime = time.time()

        #: a list to store exceptions occurs during execution
        self.exceptions: "list" = []
        self._continue = True

    @property
    def score(self):
        """Calculate its real priority based on :attr:`expecttime` and :attr:`priority`"""
        return self._score()

    def _score(self):
        return self.priority * 10000000000 - self.exetime

    def is_ready(self):
        """Called by scheduler's queue to check if the task is ready"""
        return self.exetime <= time.time()

    @property
    def middleware(self):
        return middleware

    @property
    def crawler(self):
        return self.middleware.crawler

    async def execute(self, *args, **kwargs) -> _TaskGenerator:
        """main entry for a task to start working.
        """
        self.last_crawl_time = time.time()
        self.exceptions = []

        for plugin in self.middleware.iter_plugins(*self.families):
            async for task in self._sandbox(self, plugin.before):
                yield task

        async for task in self._sandbox(self, self.__class__._execute, *args, **kwargs):
            yield task

        for plugin in self.middleware.iter_plugins(*self.families):
            async for task in self._sandbox(self, plugin.after):
                yield task

    async def _sandbox(self, task, func, *args, **kwargs):
        """Wrap the func to async generator and catch the exceptions during work."""
        if task._continue:
            try:
                async for new_task in to_asyncgen(func, self, *args, **kwargs):
                    yield new_task
            except Exception as e:
                task.exceptions.append(e)
                for plugin in self.middleware.iter_plugins(*self.families):
                    async for task in self._sandbox(self, plugin.on_error):
                        yield task

    def has_exception(self, exception_cls=None):
        if not exception_cls:
            return bool(self.exceptions)
        else:
            for exc in self.exceptions:
                if isinstance(exc, exception_cls):
                    return True
        return False

    async def _execute(self, **kwargs: Any) -> _TaskGenerator:
        """should be rewritten as a generator in the subclass."""
        raise NotImplementedError

    def __lt__(self, other):
        return self.score < other.score

    def __getstate__(self):
        state = self.__dict__
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __str__(self):
        return f"<Task {self.family}>"


class DummyTask(Task):
    def __init__(
        self,
        val,
        spawn=None,
        sleep=0,
        priority=0,
        meta=None,
        family=None,
        err=None,
        exetime=0,
        **kwargs,
    ):
        super().__init__(
            priority=priority, meta=meta, family=family, exetime=exetime, **kwargs
        )
        self.val = val
        self.spawn = spawn
        self.sleep = sleep
        self.err = err

    def _fingerprint(self):
        return self.val

    async def _execute(self):
        if self.err:
            raise self.err
        await asyncio.sleep(self.sleep)
        print(self.val)

        if self.spawn:
            yield self.spawn

