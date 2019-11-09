import asyncio
from ..tasks import Task
from ..scheduler import Scheduler
from ..config import config
from ..plugins import middleware
from .worker import Worker


class Crawler:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.config = config
        self._unfinished_tasks = 0
        self._finished = asyncio.Event()
        self._finished.set()
        self.sdl_req = Scheduler()
        self.sdl = Scheduler()
        middleware.crawler = self

    async def run_async(self):
        self.wokers = []

        await middleware.start()
        for _ in range(self.config.max_requests):
            worker = Worker(self, self.sdl_req)
            worker.current_work = self.loop.create_task(worker.work())
            self.wokers.append(worker)

        for _ in range(self.config.max_workers):
            worker = Worker(self, self.sdl)
            worker.current_work = self.loop.create_task(worker.work())
            self.wokers.append(worker)
        await self.join()
        await middleware.close()

    async def join(self):
        if self._unfinished_tasks > 0:
            await self._finished.wait()

    async def add_task(self, new_task):
        for plugin in middleware.iter_plugins(*new_task.families):
            async for t in new_task._sandbox(new_task, plugin.before_add):
                if isinstance(t, Task):
                    await self.add_task(t)
        if new_task._continue:
            await self.sdl.produce(new_task)
            self._unfinished_tasks += 1
            self._finished.clear()

    async def done_task(self):
        if self._unfinished_tasks <= 0:
            raise ValueError("done_task() called too many times")
        self._unfinished_tasks -= 1
        if self._unfinished_tasks == 0:
            self._finished.set()

