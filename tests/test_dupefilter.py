import pytest
from acrawler.task import DummyTask
from acrawler.scheduler import SetDupefilter


@pytest.mark.asyncio
async def test_setdf():
    df = SetDupefilter()
    await df.start()
    for i in range(1000):
        await df.seen(DummyTask(i))
    assert await df.get_length() == 1000
    assert await df.seen(DummyTask(999)) is True
    assert await df.seen(DummyTask(1000)) is False
    assert await df.seen(DummyTask(1000)) is True
    await df.clear()
    assert await df.get_length() == 0
    await df.close()

