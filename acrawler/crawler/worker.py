import typing
from ..tasks import Task
import traceback

if typing.TYPE_CHECKING:
    from .crawler import Crawler
    from ..scheduler import Scheduler


class Worker:
    def __init__(self, crawler: "Crawler", sdl: "Scheduler"):
        self.sdl = sdl
        self.crawler = crawler
        self.current_work = None

    async def work(self):
        """Execute tasks"""
        try:
            while True:
                task: "Task" = await self.sdl.consume()
                async for new_task in task.execute():
                    if isinstance(new_task, Task):
                        new_task.meta = {**task.meta}
                        new_task.ancestor = task.ancestor
                        await self.crawler.add_task(new_task)

                await self.crawler.done_task()
        except Exception as e:
            print(traceback.format_exc())
