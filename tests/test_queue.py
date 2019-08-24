import pytest

from acrawler.http import Request
from acrawler.scheduler import AsyncPQ, RedisPQ
from acrawler.task import DummyTask


async def pq_push_pop(q):
    await q.start()
    await q.clear()

    task3 = DummyTask("I am task 3.", priority=3)
    await q.push(task3)
    task1 = DummyTask("I am task 1.", priority=1)
    await q.push(task1)
    task4 = DummyTask("I am task 4.", priority=3)
    await q.push(task4)
    task2 = DummyTask("I am task 2.", priority=2)
    await q.push(task2)

    t = await q.pop()
    assert t.val == task3.val
    await q.pop()
    await q.pop()
    t = await q.pop()
    assert t.val == task1.val
    assert await q.get_length() == 0

    req = Request(
        "http://httpbin.org/user-agent",
        request_config={"headers": {"User-Agent": "TestClient"}},
        priority=1,
    )
    await q.push(req)
    task = await q.pop()
    resp = await task.fetch()
    assert "TestClient" in resp.text
    await q.close()


@pytest.mark.asyncio
async def test_AsyncPQ():
    q = AsyncPQ()
    await pq_push_pop(q)


@pytest.mark.asyncio
async def test_RedisPQ():
    q = RedisPQ()
    await pq_push_pop(q)
