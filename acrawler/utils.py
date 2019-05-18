import sys
import asyncio
import logging
import webbrowser
from functools import partial
from importlib import import_module
from pathlib import Path
from inspect import isasyncgenfunction, isgeneratorfunction, \
    isfunction, iscoroutinefunction, ismethod, isgenerator


def config_from_setting(module):
    context = {}
    for key in dir(module):
        if not key.startswith('__'):
            context[key] = getattr(module, key)
    request_config = context.pop('REQUEST_CONFIG', {})
    middleware_config = context.pop('MIDDLEWARE_CONFIG', {})
    config = context
    return config, request_config, middleware_config


def merge_config(*configs):
    r = {}
    for config in configs:
        r = {**r, **config}
    return r


async def to_asyncgen(fn, *args, **kwargs):
    if type(fn)==partial:
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
    if not name in sys.modules:
        mod = import_module(name)
        return mod
    else:
        return sys.modules[name]


def open_html(html, path=None):
    if not path:
        path = Path.home()/'.temp.html'
    url = 'file://' + str(path)
    with open(path, 'w') as f:
        f.write(html)
    webbrowser.open(url)


def get_logger(name: str = 'user'):
    if not name.startswith('acrawler.'):
        name = 'acrawler.'+name
    return logging.getLogger(name)


def redis_push_start_urls(key, url=None, address='redis://localhost'):
    asyncio.get_event_loop().run_until_complete(
        redis_push_start_urls_coro(key, url, address))


async def redis_push_start_urls_coro(key, url=None, address='redis://localhost'):
    aioredis = import_module('aioredis')
    redis = await aioredis.create_redis_pool(address)
    if isinstance(url, list):
        for u in url:
            await redis.rpush(key, u)
    else:
        await redis.rpush(key, url)
    redis.close()
    await redis.wait_closed()
