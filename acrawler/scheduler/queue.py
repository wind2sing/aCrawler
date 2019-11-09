import asyncio
import time
import dill as pickle


class AsyncQueue:
    """A Priority Queue that uses vanilla :class:`asyncio.PriorityQueue` to store tasks."""

    def __init__(self):
        self.ready = asyncio.PriorityQueue()
        self.waiting = asyncio.PriorityQueue()

    async def start(self):
        pass

    async def close(self):
        pass

    async def push(self, task: "Task"):
        """Push a task into waiting queue"""
        await self.waiting.put((task.exetime, task))

    async def pop(self) -> "Task":
        """Pop a prepared task from ready queue"""
        await self.transfer_waiting()
        while 1:
            try:
                r = (self.ready.get_nowait())[1]
                return r
            except asyncio.QueueEmpty:
                await asyncio.sleep(1)
                await self.transfer_waiting()

    async def transfer_waiting(self):
        """Transfer all prepared task from waiting queue to ready queue"""
        while 1:
            try:
                task = (self.waiting.get_nowait())[1]
                if task.is_ready():
                    self.ready.put_nowait((-task.score, task))
                else:
                    self.waiting.put_nowait((task.exetime, task))
                    break
            except asyncio.QueueEmpty:
                break

    async def get_length(self):
        return self.ready.qsize() + self.waiting.qsize()

    async def get_length_of_ready(self):
        await self.transfer_waiting()
        return self.ready.qsize()

    async def get_length_of_waiting(self):
        await self.transfer_waiting()
        return self.waiting.qsize()

    async def clear(self):
        self.ready = asyncio.PriorityQueue()
        self.waiting = asyncio.PriorityQueue()

    @staticmethod
    def serialize(task):
        return pickle.dumps(task)

    @staticmethod
    def deserialize(message) -> "Task":
        return pickle.loads(message)
