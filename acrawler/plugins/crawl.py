from .base import Plugin
from ..utils import to_asyncgen


class CrawlStartPlugin(Plugin):
    priority = 1900

    async def start(self):
        async for task in to_asyncgen(self.crawler.start_requests):
            await self.crawler.add_task(task)

        async def watch():
            async for task in to_asyncgen(self.crawler.next_requests):
                await self.crawler.add_task(task)

        await self.crawler.create_task(watch())
