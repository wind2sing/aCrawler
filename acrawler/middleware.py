import bisect
import logging
from collections import UserList
from inspect import (
    isclass,
    isgeneratorfunction,
    isasyncgenfunction,
    iscoroutinefunction,
)
from typing import AsyncGenerator, Callable

from acrawler.utils import to_asyncgen

_Function = Callable
_Task = "acrawler.task.Task"
_Request = "acrawler.http.Request"
_Response = "acrawler.http.Response"
_Crawler = "acrawler.crawler.Crawler"
_TaskGenerator = AsyncGenerator["Task", None]
logger = logging.getLogger(__name__)


class HandlerMetaClass(type):
    @classmethod
    def __prepare__(metacls, name, bases, **kwargs):
        return super().__prepare__(name, bases, **kwargs)

    def __new__(
        metacls,
        name,
        bases,
        namespace,
        family=None,
        position=0,
        priority=None,
        func=None,
        **kwargs
    ):
        if family:
            namespace["family"] = family
        if priority:
            namespace["priority"] = priority
        p_d = ["on_start", "handle_before", "handle_after", "on_close"]
        if func:
            if isgeneratorfunction(func):

                def meth(handler, task):
                    yield from func(task)

            elif iscoroutinefunction(func):

                async def meth(handler, task):
                    return await func(task)

            elif isasyncgenfunction(func):

                async def meth(handler, task):
                    async for t in func(task):
                        yield t

            else:

                def meth(handler, task):
                    return func(task)

            namespace[p_d[position]] = meth
        return super().__new__(metacls, name, bases, namespace)


class Handler(metaclass=HandlerMetaClass):
    """A handler wraps functions for a specific task.

    """

    family: str = "_Default"
    """Associated with `Task`'s families. One handler only has one family. If a 
    handler's family is in a task's families, this handler matches the task and then 
    somes fuctions will be called before and after the task.
    """

    priority: int = 500
    """A handler with higher priority will be checked with task earlier.
    A handler with priority 0 will be disabled.
    """

    def __init__(
        self,
        family: str = None,
        func_before: _Function = None,
        func_after: _Function = None,
        func_start: _Function = None,
        func_close: _Function = None,
    ):
        if family:
            self.family = family

        self.funcs = [None] * 4
        self.set_func(0, self.on_start)
        self.set_func(1, self.handle_before)
        self.set_func(2, self.handle_after)
        self.set_func(3, self.on_close)

        self.set_func(0, func_start)
        self.set_func(1, func_before)
        self.set_func(2, func_after)
        self.set_func(3, func_close)

    @property
    def crawler(self):
        return middleware.crawler

    async def on_start(self):
        """When Crawler starts(before :meth:`~acrawler.crawler.Crawler.start_requests`), 
        this method will be called.
        """

    async def handle_before(self, task: _Task):
        """Then function called before the execution of the task.
        """

    async def handle_after(self, task: _Task):
        """Then function called after the execution of the task.
        """

    async def on_close(self):
        """When Crawler closes, this method will be called.
        """

    async def handle(self, position: int, task: _Task = None) -> _TaskGenerator:
        if position == 0 or position == 3:
            async for task in self._call_func(position):
                yield task
        elif position == 1 or position == 2:
            if self.family in task.families:
                async for task in self._call_func(position, task):
                    yield task

    def set_func(self, position: int, func):
        if func:
            self.funcs[position] = func

    async def _call_func(self, position, *args, **kwargs) -> _TaskGenerator:
        func = self.funcs[position]
        async for task in to_asyncgen(func, *args, **kwargs):
            yield task

    def __lt__(self, other):
        return self.priority > other.priority

    def __repr__(self):
        return "{} (family:{} priority:{})".format(
            self.__class__.__name__, self.family, self.priority
        )


class HandlerList(UserList):
    def __init__(self):
        super().__init__()
        self._names = set()

    def append(self, item):
        if item.__class__.__name__ not in self._names:
            bisect.insort(self.data, item)
            self._names.add(item.__class__.__name__)

    def insert(self, item):
        if item.__class__.__name__ not in self._names:
            bisect.insort(self.data, item)
            self._names.add(item.__class__.__name__)


class SingletonMetaclass(type):
    def __init__(self, *args, **kwargs):
        self.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super(SingletonMetaclass, self).__call__(*args, **kwargs)
            return self.__instance
        else:
            return self.__instance


class _Middleware(metaclass=SingletonMetaclass):
    handlers = HandlerList()
    crawler: _Crawler = None

    def register(self, family: str = None, position: int = None, priority: int = None):
        """The factory method for creating decorators to register handlers to middleware.
        Singledispathed for differenct types of targets.

        If you register a function, you must give `position` and `family`.
        If you register a Handler class, you can register it without explicit parameters::

            @register(family='Myfamily', position=1)
            def my_func(task):
                print("This is called before execution")
                print(task)

            @register()
            class MyHandler(Handler):
                family = 'Myfamily'

                def handle(self, task):
                    print("This is called before execution")
                    print(task)

        Args:
            family: received as the :attr:`Handler.family` of the Handler.
            priority: received as the :attr:`Handler.priority` of the Handler.
            position: represents the role of function. Should be a valid int: 0/1/2/3

                0 -  :meth:`Handler.on_start`

                1 -  :meth:`Handler.handle_before`

                2 -  :meth:`Handler.handle_after`

                3 -  :meth:`Handler.on_close`

        """

        def decorator(target):
            if isclass(target):
                self.append_handler_cls(target, family, priority)
            else:
                self.append_func(target, family, position, priority)
            return target

        return decorator

    def append_func(
        self, func, family: str = None, position: int = None, priority: int = None
    ):
        """constructor a handler class from given function and register it.

        :param func:
        :type func: [type]
        :param family: , defaults to None
        :type family: str, optional
        :param position: 0, 1, 2, 3, defaults to None
        :type position: int, optional
        :param priority: , defaults to None
        :type priority: int, optional
        """
        if family is None:
            family = "_Default"
        if priority is None:
            priority = 500
        if position is None:
            position = 2
        if not position in (0, 1, 2, 3):
            raise ValueError("Position for function should be a valid value: 0/1/2/3!")
        else:
            hcls = HandlerMetaClass(
                func.__name__,
                (Handler,),
                {},
                family=family,
                position=position,
                priority=priority,
                func=func,
            )
            self.append_handler_cls(hcls)
        return func

    def append_handler_cls(self, handler_cls, family: str = None, priority: int = None):
        handler = handler_cls()
        if family:
            handler.family = family
        if priority:
            handler.priority = priority
        if handler.priority != 0:
            self.handlers.append(handler)
        return handler_cls

    def get_handler(self, *families):
        tmp = []
        for family in families:
            for hdl in self.handlers:
                if family == hdl.family:
                    tmp.append()

    def __repr__(self):
        return repr(self.handlers)


middleware = _Middleware()
"""The singleton instance to manege middlewares.

Use :meth:`@middleware.register` as a decorator.
"""

register = middleware.register
"""Shortcut for :meth:`middleware.register`
"""
