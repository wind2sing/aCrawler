import bisect
from importlib import import_module
from collections import UserList
from ..utils import to_asyncgen
from inspect import (
    isclass,
    isgeneratorfunction,
    isasyncgenfunction,
    iscoroutinefunction,
)

import typing

if typing.TYPE_CHECKING:
    from .. import Task
    from .. import Crawler
    from ..config import Config


class PluginMetaClass(type):
    def __new__(
        metacls,
        name,
        bases,
        namespace,
        family=None,
        priority=None,
        func=None,
        meth_name=None,
        **kwargs
    ):
        if family:
            namespace["family"] = family
        if priority:
            namespace["priority"] = priority
        if func and meth_name:
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

            namespace[meth_name] = meth

        return super().__new__(metacls, name, bases, namespace, **kwargs)


class Plugin(metaclass=PluginMetaClass):
    family: str = "Default"
    """Associated with `Task`'s families. One handler only has one family. If a
    handler's family is in a task's families, this handler matches the task and then
    somes fuctions will be called before and after the task.
    """

    priority: int = 500
    """A plugin with higher priority will be processed with task earlier.
    A plugin with priority 0 will be disabled.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def middleware(self) -> "_Middleware":
        return middleware

    @property
    def crawler(self) -> "Crawler":
        return middleware.crawler

    @property
    def config(self) -> "Config":
        return middleware.crawler.config

    async def start(self):
        pass

    async def before_add(self, task):
        pass

    async def before(self, task):
        pass

    async def after(self, task):
        pass

    async def on_error(self, task):
        pass

    async def close(self):
        pass

    def __lt__(self, other):
        return self.priority > other.priority

    def __repr__(self):
        return "{} (family:{} priority:{})".format(
            self.__class__.__name__, self.family, self.priority
        )


class PluginList(UserList):
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


class _Middleware:
    def __init__(self):
        self.plugins: List[Plugin] = PluginList()
        self.crawler: "Crawler" = None

    async def start(self):
        for name, key in self.crawler.config.plugins_config.items():
            if key:
                p, h = name.rsplit(".", 1)
                mod = import_module(p)
                mcls = getattr(mod, h)
                if key is True:
                    pass
                else:
                    mcls.priority = key
                self.append_plugin_cls(mcls)
        for plugin in self.plugins:
            async for t in to_asyncgen(plugin.start):
                pass

    def register(self, family: str = None, priority: int = None):
        """The decorator to register plugin class.
        """

        def decorator(target):
            self.append_plugin_cls(target, family, priority)
            return target

        return decorator

    def before(self, family: str = None, priority: int = None):
        """The decorator to register `before` hook function as plugin
        """

        def decorator(target):
            self.append_func(target, "before", family, priority)
            return target

        return decorator

    def after(self, family: str = None, priority: int = None):
        """The decorator to register `after` hook function as plugin
        """

        def decorator(target):
            self.append_func(target, "after", family, priority)
            return target

        return decorator

    def before_add(self, family: str = None, priority: int = None):
        """The decorator to register `before_add` hook function as plugin
        """

        def decorator(target):
            self.append_func(target, "before_add", family, priority)
            return target

        return decorator

    def on_error(self, family: str = None, priority: int = None):
        """The decorator to register `on_error` hook function as plugin
        """

        def decorator(target):
            self.append_func(target, "on_error", family, priority)
            return target

        return decorator

    def append_func(self, func, meth_name, family: str = None, priority: int = None):
        """constructor a plugin class from given function and register it.
        """

        hcls = PluginMetaClass(
            func.__name__,
            (Plugin,),
            {},
            family=family,
            priority=priority,
            func=func,
            meth_name=meth_name,
        )
        self.append_plugin_cls(hcls)
        return func

    def append_plugin_cls(self, plugin_cls, family: str = None, priority: int = None):
        plugin = plugin_cls()

        if family:
            plugin.family = family
        if priority:
            plugin.priority = priority
        if plugin.priority != 0:
            self.plugins.append(plugin)
        return plugin_cls

    def iter_plugins(self, *families):
        tmp = []
        for family in families:
            for plugin in self.plugins:
                if family == plugin.family:
                    yield plugin

    async def close(self):
        for plugin in self.plugins:
            await plugin.close()

    def __repr__(self):
        return repr(self.plugins)


middleware = _Middleware()
"""The singleton instance to manege middlewares.

Use :meth:`@middleware.register` as a decorator.
"""

register = middleware.register
"""Shortcut for :meth:`middleware.register`
"""
