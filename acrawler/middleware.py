import types
from collections import UserList
import bisect
from inspect import iscoroutinefunction
import logging
import functools

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

    def __new__(metacls, name, bases, namespace, family=None, position=0, priority=None, func=None, **kwargs):
        if family:
            namespace['family'] = family
        if priority:
            namespace['priority'] = priority
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
    :param func: a callable function or coroutine function, cannot be a generator
    """
    family = '_Default'
    priority = 100

    def __init__(self,
                 family: str = None,
                 func_before: _Function = None,
                 func_after: _Function = None,
                 func_start: _Function = None,
                 func_close: _Function = None,
                 crawler: _Crawler = None):
        if family:
            self.family = family

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

    @property
    def crawler(self):
        return middleware.crawler

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
            if task and self.family in task.families:
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

    def __lt__(self, other):
        return self.priority > other.priority

    def __repr__(self):
        return '{} (family:{} priority:{})'.format(self.__class__.__name__, self.family, self.priority)


class HandlerList(UserList):
    def append(self, item):
        bisect.insort(self.data, item)

    def insert(self, item):
        bisect.insort(self.data, item)


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
    handlers = HandlerList()
    crawler = None

    def register(self, family: str = None, position: int = None, priority: int = None):
        """The factory method for creating decorators to register handlers to middleware.
        Singledispathed for differenct types of targets.
        """
        @functools.singledispatch
        def decorator(target):
            return target

        @decorator.register(types.FunctionType)
        def _(func):
            nonlocal priority
            nonlocal family
            self.append_func(func, family, position, priority)
            return func

        @decorator.register(HandlerMetaClass)
        def _(cls):
            self.append_handler_cls(cls, family, priority)
            return cls

        return decorator

    def append_func(self, func, family: str = None, position: int = None, priority: int = None):
        if family is None:
            family = '_Default'
        if priority is None:
            priority = 100
        if position is None:
            position = 2
        if not position in (0, 1, 2, 3):
            raise ValueError(
                'Position for function should be a valid value: 0/1/2/3!')
        else:
            hcls = HandlerMetaClass(
                'ShortHandler', (Handler,), {}, family=family, position=position, priority=priority, func=func)
            self.append_handler_cls(hcls)
        return func

    def append_handler_cls(self, handler_cls, family: str = None, priority: int = None):
        handler = handler_cls()
        if family:
            handler.family = family
        if priority:
            handler.priority = priority
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
The decorator receive a parameter as the family key to store middleware functions.
"""

register = middleware.register
