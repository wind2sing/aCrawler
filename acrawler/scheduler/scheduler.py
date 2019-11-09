from .queue import AsyncQueue

import typing
import asyncio


class Scheduler:
    """Scheduler produces & consumes tasks with its priority queue.

    :param q: instance of the priority queue. Defaults to :class:`AsyncQueue`.
    """

    queue_cls = AsyncQueue

    def __init__(self):
        self.q = self.queue_cls()

    async def start(self):
        await self.q.start()

    async def produce(self, task) -> bool:
        """Enqueue a task"""
        await self.q.push(task)
        return True

    async def consume(self) -> "Task":
        """Dequeue a task"""
        return await self.q.pop()

    async def clear(self):
        await self.q.clear()

    async def close(self):
        await self.q.close()
