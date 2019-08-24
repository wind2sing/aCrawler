import pytest

from acrawler.http import Request
from acrawler.scheduler import Scheduler


@pytest.mark.asyncio
async def test_queue():
    sdl = Scheduler()
    rq1 = Request("https://www.baidu.com")
    rq2 = Request("https://www.bing.com")
    assert await sdl.produce(rq1)
    assert await sdl.produce(rq2)
    assert not await sdl.produce(rq1)


@pytest.mark.asyncio
async def test_dont_filter():
    sdl = Scheduler()
    rq1 = Request("https://www.baidu.com")
    rq2 = Request("https://www.bing.com", dont_filter=True)
    assert await sdl.produce(rq1)
    assert not await sdl.produce(rq1)
    assert await sdl.produce(rq2)
    assert await sdl.produce(rq2)


@pytest.mark.asyncio
async def test_consume():
    sdl = Scheduler()
    rq1 = Request("https://www.baidu.com")
    rq2 = Request("https://www.bing.com")
    assert await sdl.produce(rq1)
    assert await sdl.produce(rq2)
    assert await sdl.consume() is rq1
