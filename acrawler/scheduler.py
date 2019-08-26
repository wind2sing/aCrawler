import asyncio
import logging
import time

import dill as pickle

from acrawler.utils import check_import

# Typing

_Task = "acrawler.task.Task"

logger = logging.getLogger(__name__)


class BaseDupefilter:
    async def start(self):
        pass

    async def seen(self, task: _Task) -> bool:
        return False

    async def has_fp(self, fp):
        pass

    async def add_fp(self, fp):
        pass

    async def clear(self):
        pass

    async def close(self):
        pass

    async def get_length(self):
        return 0


class SetDupefilter(BaseDupefilter):
    """A Dupefilter that uses vanilla `set` to store fingerprints."""

    def __init__(self):
        self.fingerprints = set()

    async def seen(self, task: _Task) -> bool:
        fp = task.fingerprint
        if await self.has_fp(fp):
            return True
        await self.add_fp(fp)
        return False

    async def has_fp(self, fp):
        return fp in self.fingerprints

    async def add_fp(self, fp):
        self.fingerprints.add(fp)

    async def clear(self):
        self.fingerprints = set()

    async def get_length(self):
        return len(self.fingerprints)


class RedisDupefilter(BaseDupefilter):
    def __init__(self, address="redis://localhost", df_key="acrawler:df"):
        self.address = address
        self.df_key = df_key
        self.redis = None

    async def start(self):
        aioredis = check_import("aioredis")
        self.redis = await aioredis.create_redis_pool(self.address)

    async def seen(self, task: _Task):
        fp = task.fingerprint
        return await self.add_fp(fp) == 0

    async def add_fp(self, fp):
        return await self.redis.sadd(self.df_key, fp)

    async def has_fp(self, fp):
        return await self.redis.sismember(self.df_key, fp)

    async def clear(self):
        return await self.redis.delete(self.df_key)

    async def get_length(self):
        return await self.redis.scard(self.df_key)

    async def close(self):
        self.redis.close()
        return await self.redis.wait_closed()


class BaseQueue:
    async def start(self):
        pass

    async def push(self, task):
        raise NotImplementedError

    async def pop(self):
        raise NotImplementedError

    async def get_length(self):
        raise NotImplementedError

    async def clear(self):
        raise NotImplementedError

    async def close(self):
        pass

    @staticmethod
    def serialize(task):
        return pickle.dumps(task)

    @staticmethod
    def deserialize(message) -> _Task:
        return pickle.loads(message)


class AsyncPQ(BaseQueue):
    """A Priority Queue that uses vanilla :class:`asyncio.PriorityQueue` to store tasks."""

    def __init__(self):
        super().__init__()
        self.pq = asyncio.PriorityQueue()
        self.waiting = asyncio.PriorityQueue()

    async def push(self, task: _Task):
        return await self.waiting.put((task.exetime, task))

    def push_nowait(self, task):
        return self.waiting.put_nowait((task.exetime, task))

    async def pop(self):
        await self.transfer_waiting()
        while 1:
            try:
                r = (self.pq.get_nowait())[1]
                return r
            except asyncio.QueueEmpty:
                await asyncio.sleep(1)
                await self.transfer_waiting()

    async def transfer_waiting(self):
        """Transfer all prepared task from waiting queue to ready queue."""
        now = time.time()
        while 1:
            try:
                task = (self.waiting.get_nowait())[1]
                if task.exetime <= now:
                    self.pq.put_nowait((-task.score, task))
                else:
                    self.push_nowait(task)
                    break
            except asyncio.QueueEmpty:
                break

    async def get_length(self):
        return self.pq.qsize() + self.waiting.qsize()

    async def get_length_of_pq(self):
        await self.transfer_waiting()
        return self.pq.qsize()

    async def get_length_of_waiting(self):
        await self.transfer_waiting()
        return self.waiting.qsize()

    async def clear(self):
        self.pq = asyncio.PriorityQueue()
        self.waiting = asyncio.PriorityQueue()


class RedisPQ(BaseQueue):
    def __init__(self, address="redis://localhost", q_key="acrawler:queue"):
        super().__init__()
        self.address = address
        self.pq_key = q_key + ":pq"
        self.waiting_key = q_key + ":waiting"
        self.redis: "aioredis.Redis" = None

    async def start(self):
        aioredis = check_import("aioredis")
        self.redis = await aioredis.create_redis_pool(self.address)

    async def push(self, task: _Task):
        """Push a task directly to the waiting queue.
        """
        return await self.redis.zadd(
            self.waiting_key, task.exetime, self.serialize(task)
        )

    async def push_to_pq(self, task: _Task):
        """Push a task directly to the priority queue.
        """
        return await self.redis.zadd(self.pq_key, -task.score, self.serialize(task))

    async def pop(self):
        """Pop a task from priority queue. Blocking if empty.
        """
        await self.transfer_waiting()
        while True:
            tr = self.redis.multi_exec()
            tr.zrange(self.pq_key, 0, 0)
            tr.zremrangebyrank(self.pq_key, 0, 0)
            eles, _ = await tr.execute()

            if eles:
                return self.deserialize(eles[0])
            else:
                await asyncio.sleep(0.5)
                await self.transfer_waiting()

    async def transfer_waiting(self):
        """Transfer the tasks that are permitted by exetime from waiting queue
        to priority queue
        """
        now = time.time()
        tr = self.redis.multi_exec()
        tr.zrangebyscore(self.waiting_key, max=now)
        tr.zremrangebyscore(self.waiting_key, max=now)
        eles, _ = await tr.execute()
        if eles:
            for ele in eles:
                task = self.deserialize(ele)
                await self.push_to_pq(task)
        else:
            # waiting queue is empty
            pass

    async def clear(self):
        await self.redis.delete(self.pq_key)
        await self.redis.delete(self.waiting_key)

    async def get_length(self):
        tr = self.redis.multi_exec()
        tr.zcard(self.pq_key)
        tr.zcard(self.waiting_key)
        l1, l2 = await tr.execute()
        return l1 + l2

    async def get_length_of_pq(self):
        await self.transfer_waiting()
        l = await self.redis.zcard(self.pq_key)
        return l

    async def get_length_of_waiting(self):
        await self.transfer_waiting()
        l = await self.redis.zcard(self.waiting_key)
        return l

    async def close(self):
        self.redis.close()
        return await self.redis.wait_closed()


class Scheduler:
    """Scheduler produces & consumes tasks with its priority queue.

    :param df: instance of the dupefilter. Defaults to :class:`SetDupefilter`.
    :param q: instance of the priority queue. Defaults to :class:`AsyncPQ`.
    """

    def __init__(self, df: BaseDupefilter = None, q: BaseQueue = None):
        if df:
            self.df = df
        else:
            self.df = SetDupefilter()
        if q:
            self.q = q
        else:
            self.q = AsyncPQ()

    async def start(self):
        await self.df.start()
        await self.q.start()

    async def produce(self, task, dont_filter=False) -> bool:
        if task.dont_filter or dont_filter:
            await self.q.push(task)
            return True
        else:
            if await self.df.seen(task):
                return False
            else:
                await self.q.push(task)
                return True

    async def consume(self) -> _Task:
        task = await self.q.pop()
        return task

    async def clear(self, df=True, q=True):
        if df:
            await self.df.clear()
        if q:
            await self.q.clear()

    async def close(self):
        await self.df.close()
        await self.q.close()
