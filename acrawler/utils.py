"""
This module provides utility functions that are used by aCrawler.
Some are used for external consumption.

"""

import sys
import re
import asyncio
import logging
import webbrowser
from functools import partial
from urllib.parse import urljoin
from importlib import import_module
from pathlib import Path
from inspect import (
    isasyncgenfunction,
    isgeneratorfunction,
    isfunction,
    iscoroutinefunction,
    ismethod,
    isgenerator,
)

# typing
from typing import Tuple, Dict, Any

_Config = Dict[str, Any]


def config_from_setting(module) -> Tuple[_Config, _Config, _Config]:
    # Generate three types of config from `setting.py`.
    context = {}
    for key in dir(module):
        if not key.startswith("__"):
            context[key] = getattr(module, key)
    request_config = context.pop("REQUEST_CONFIG", {})
    middleware_config = context.pop("MIDDLEWARE_CONFIG", {})
    config = context
    return config, request_config, middleware_config


def merge_config(*configs: _Config) -> _Config:
    # Merge different configs in order.
    r = {}
    for config in configs:
        r = {**r, **config}
    return r


def merge_dicts(a, b):
    """Merges b into a"""
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts(a[key], b[key])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a


async def to_asyncgen(fn, *args, **kwargs):
    if type(fn) == partial:
        judge = fn.func
    else:
        judge = fn
    if isasyncgenfunction(judge):
        async for task in fn(*args, **kwargs):
            yield task
    elif isgeneratorfunction(judge):
        for task in fn(*args, **kwargs):
            yield task
    elif iscoroutinefunction(judge):
        yield await fn(*args, **kwargs)
    elif callable(judge):
        yield fn(*args, **kwargs)
    else:
        raise TypeError("function {} not valid!".format(fn))


class FakeModule:
    def __init__(self, error):
        self._error = error

    def __getattribute__(self, name):
        if name.startswith("__"):
            return super().__getattribute__(name)
        else:
            raise self.__dict__["_error"]


def check_import(name: str, allow_import_error=False):
    """Safely import module only if it's not imported
    """

    if not name in sys.modules:
        try:
            mod = import_module(name)
        except ImportError as e:
            if not allow_import_error:
                raise e
            else:
                mod = FakeModule(e)
    else:
        mod = sys.modules[name]

    return mod


def open_html(html, path=None):
    """A helper function to debug your response. Usually called with `open_html(response.text)`.
    """
    if not path:
        path = Path.home() / ".temp.html"
    url = "file://" + str(path)
    with open(path, "w") as f:
        f.write(html)
    webbrowser.open(url)


LINK_PATTERN = re.compile(r"<(.*?)(src|href)=(\"|')(.*?)(\"|')(.*?)>", re.S)


def _srcrepl(match, base_url):
    href = match.group(4)
    new_url = href
    if (
        href
        and not href.startswith("#")
        and not href.startswith(("javascript:", "mailto:"))
    ):
        new_url = urljoin(base_url, href)

    return (
        "<"
        + match.group(1)
        + match.group(2)
        + "="
        + match.group(3)
        + new_url
        + match.group(5)
        + match.group(6)
        + ">"
    )


def make_text_links_absolute(text, base_url):
    updated_text = LINK_PATTERN.sub(partial(_srcrepl, base_url=base_url), text)
    return updated_text


def get_logger(name: str = "user"):
    """Get a logger which has the same configuration as crawler's logger.
    """
    if not name.startswith("acrawler."):
        name = "acrawler." + name
    return logging.getLogger(name)


def redis_push_start_urls(
    key: str, url: str = None, address: str = "redis://localhost"
):
    """ When you are using redis_based distributed crawling, you can use this function to feed start_urls to redis. 
    """
    asyncio.get_event_loop().run_until_complete(
        redis_push_start_urls_coro(key, url, address)
    )


async def redis_push_start_urls_coro(
    key: str, url: str = None, address: str = "redis://localhost"
):
    """Coroutine version of :func:`redis_push_start_urls`
    """
    aioredis = import_module("aioredis")
    redis = await aioredis.create_redis_pool(address)
    if isinstance(url, list):
        for u in url:
            await redis.sadd(key, u)
    else:
        await redis.sadd(key, url)
    redis.close()
    await redis.wait_closed()


def sync_coroutine(coro, loop=None):
    """Run a coroutine in synchronized way."""
    return (loop or asyncio.get_event_loop()).run_until_complete(coro)


def partial(func, *args, new_args_before=False, **keywords):
    def newfunc(*fargs, **fkeywords):
        if new_args_before:
            newkeywords = {**fkeywords, **keywords}
            newargs = [*fargs, *args]
        else:
            newkeywords = {**keywords, **fkeywords}
            newargs = [*args, *fargs]
        return func(*newargs, **newkeywords)

    newfunc.func = func
    newfunc.args = args
    newfunc.keywords = keywords
    return newfunc
