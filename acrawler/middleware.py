from collections import defaultdict
from inspect import iscoroutinefunction
import logging

# Typing
import acrawler
from typing import List, Callable

_Function = Callable
_Task = 'acrawler.task.Task'
_Request = 'acrawler.http.Request'
_Response = 'acrawler.http.Response'
_Crawler = 'acrawler.crawler.Crawler'

logger = logging.getLogger(__name__)


class HandlerMetaClass(type):
    @classmethod
    def __prepare__(metacls, name, bases, **kwargs):
        return super().__prepare__(name, bases, **kwargs)

    def __new__(metacls, name, bases, namespace, family=None, position=0, func=None, **kwargs):
        if family:
            namespace['family'] = family
        p_d = ['on_start', 'handle_before', 'handle_after', 'on_close']
        if func:
            def meth(handler, task):
                return func(task)

            namespace[p_d[position]] = meth
        return super().__new__(metacls, name, bases, namespace)


class Handler(metaclass=HandlerMetaClass):
    """A handler wraps functions for a specific task.

    :param family: associated with `Task`'s family.
    :param position: 0 means that function is called before
        task's execution. 1 means after task's execution.
    :param func: a callable function or coroutine function
    """
    family = '_Default'

    def __init__(self,
                 family: str = None,
                 func_before: _Function = None,
                 func_after: _Function = None,
                 func_start: _Function = None,
                 func_close: _Function = None,
                 crawler: _Crawler = None):
        if family:
            self.family = family
        self.crawler = crawler
        self.logger = logger

        self.funcs = [None] * 4
        self.is_coro = [True] * 4
        self.set_func(0, self.on_start)
        self.set_func(1, self.handle_before)
        self.set_func(2, self.handle_after)
        self.set_func(3, self.on_close)

        self.set_func(0, func_start)
        self.set_func(1, func_before)
        self.set_func(2, func_after)
        self.set_func(3, func_close)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler=crawler)

    async def on_start(self):
        pass

    async def handle_before(self, task: _Task):
        pass

    async def handle_after(self, task: _Task):
        pass

    async def on_close(self):
        pass

    async def handle(self, position: int, task: _Task = None):
        if position == 0 or position == 3:
            await self._call_func(position)
        elif position == 1 or position == 2:
            if task and task.family == self.family:
                await self._call_func(position, task)

    def set_func(self, position: int, func):
        if func:
            self.funcs[position] = func
            self.is_coro[position] = iscoroutinefunction(func)

    async def _call_func(self, position, *args, **kwargs):
        func = self.funcs[position]
        if self.is_coro[position]:
            await func(*args, **kwargs)
        else:
            func(*args, **kwargs)


class SingletonMetaclass(type):
    def __init__(self, *args, **kwargs):
        self.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super(
                SingletonMetaclass, self).__call__(*args, **kwargs)
            return self.__instance
        else:
            return self.__instance


class _Middleware(metaclass=SingletonMetaclass):
    handlers: List[Handler] = []
    handlers_cls = []
    crawler = None

    def before_execute(self, family):
        def decorator(func):
            self.append_func(family, 1, func)

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def after_execute(self, family):
        def decorator(func):
            self.append_func(family, 2, func)

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def append_func(self, family: str, position: int, func):
        hcls = HandlerMetaClass(
            'ShortHandler', (Handler,), {}, family=family, position=position, func=func)
        self.append_handler_cls(hcls)

    def append_handler_cls(self, handler_cls):
        self.handlers_cls.append(handler_cls)

    def spawn_handler(self, crawler):
        for hcls in self.handlers_cls:
            self.handlers.append(hcls.from_crawler(crawler))

    def __str__(self):
        return str([handler.__class__.__name__ for handler in self.handlers])

middleware = _Middleware()
"""The singleton instance to manege middlewares.

Use :meth:`@middleware.before_execute` or :meth:`@middleware.after_execute` as a decorator.
The decorator receive a parameter as the family key to store middleware functions.
"""
