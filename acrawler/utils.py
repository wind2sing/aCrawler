"""
This module provides utility functions that are used by aCrawler.
Some are used for external consumption.

"""

import sys
import asyncio
import logging
import webbrowser
from functools import partial
from importlib import import_module
from pathlib import Path
from inspect import isasyncgenfunction, isgeneratorfunction, \
    isfunction, iscoroutinefunction, ismethod, isgenerator

# typing
from typing import Tuple, Dict, Any
_Config = Dict[str, Any]


def config_from_setting(module) -> Tuple[_Config, _Config, _Config]:
    # Generate three types of config from `setting.py`.
    context = {}
    for key in dir(module):
        if not key.startswith('__'):
            context[key] = getattr(module, key)
    request_config = context.pop('REQUEST_CONFIG', {})
    middleware_config = context.pop('MIDDLEWARE_CONFIG', {})
    config = context
    return config, request_config, middleware_config


def merge_config(*configs: _Config) -> _Config:
    # Merge different configs in order.
    r = {}
    for config in configs:
        r = {**r, **config}
    return r


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
        raise TypeError('Callback {} not valid!'.format(fn))


def check_import(name: str):
    """Safely import module only if it's not imported
    """
    if not name in sys.modules:
        mod = import_module(name)
        return mod
    else:
        return sys.modules[name]


def open_html(html, path=None):
    """A helper function to debug your response. Usually called with `open_html(response.text)`.
    """
    if not path:
        path = Path.home()/'.temp.html'
    url = 'file://' + str(path)
    with open(path, 'w') as f:
        f.write(html)
    webbrowser.open(url)


def get_logger(name: str = 'user'):
    """Get a logger which has the same configuration as crawler's logger.
    """
    if not name.startswith('acrawler.'):
        name = 'acrawler.'+name
    return logging.getLogger(name)


def redis_push_start_urls(key: str, url: str = None, address: str = 'redis://localhost'):
    """ When you are using redis_based distributed crawling, you can use this function to feed start_urls to redis. 
    """
    asyncio.get_event_loop().run_until_complete(
        redis_push_start_urls_coro(key, url, address))


async def redis_push_start_urls_coro(key: str, url: str = None, address: str = 'redis://localhost'):
    """Coroutine version of :func:`resid_push_start_urls`
    """
    aioredis = import_module('aioredis')
    redis = await aioredis.create_redis_pool(address)
    if isinstance(url, list):
        for u in url:
            await redis.sadd(key, u)
    else:
        await redis.sadd(key, url)
    redis.close()
    await redis.wait_closed()
