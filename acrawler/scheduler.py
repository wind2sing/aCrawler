import logging
import hashlib
import asyncio
import pickle
from acrawler.utils import check_import
import traceback

# Typing
import acrawler

_Task = 'acrawler.task.Task'

logger = logging.getLogger(__name__)


class BaseDupefilter:

    async def start(self):
        pass

    async def seen(self, task: _Task)->bool:
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

    async def seen(self, task: _Task)->bool:
        fp = task.fingerprint
        if await self.has_fp(fp):
            # logger.debug('Duplicated task found! %s', task)

            return True
        else:
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
    def __init__(self, address='redis://localhost', df_key='acrawler:df'):
        self.address = address
        self.df_key = df_key
        self.redis = None

    async def start(self):
        aioredis = check_import('aioredis')
        self.redis = await aioredis.create_redis_pool(self.address)

    async def seen(self, task: _Task):
        fp = task.fingerprint
        if await self.add_fp(fp) == 0:
            # logger.debug('Duplicated task found! %s', task)
            return True
        else:
            return False

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
        pass

    async def pop(self):
        pass

    async def get_length(self):
        pass

    async def clear(self):
        pass

    async def close(self):
        pass

    def serialize(self, task):
        return pickle.dumps(task)

    def deserialize(self, message)->_Task:
        return pickle.loads(message)


class AsyncPQ(BaseQueue):
    """A Priority Queue that uses vanilla :class:`asyncio.PriorityQueue` to store tasks."""

    def __init__(self):
        self.pq = asyncio.PriorityQueue()

    async def push(self, task: _Task):
        return await self.pq.put((-task.score, task))

    async def pop(self):
        return (await self.pq.get())[1]

    async def get_length(self):
        return self.pq.qsize()

    async def clear(self):
        self.pq = asyncio.PriorityQueue()


class RedisPQ(BaseQueue):
    def __init__(self, address='redis://localhost', q_key='acrawler:queue'):
        self.address = address
        self.q_key = q_key
        self.redis = None

    async def start(self):
        aioredis = check_import('aioredis')
        self.redis = await aioredis.create_redis_pool(self.address)

    async def push(self, task: _Task):
        return await self.redis.zadd(self.q_key,
                                     task.score,
                                     self.serialize(task))

    async def pop(self):
        while True:
            tr = self.redis.multi_exec()
            tr.zrange(self.q_key, -1, -1)
            tr.zremrangebyrank(self.q_key, -1, -1)
            eles, count = await tr.execute()

            if eles:
                return self.deserialize(eles[0])
            else:
                await asyncio.sleep(3)

    async def clear(self):
        return await self.redis.delete(self.q_key)

    async def get_length(self):
        return await self.redis.zcard(self.q_key)

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


    async def produce(self, task) -> bool:
        if task.dont_filter:
            await self.q.push(task)
            logger.debug(f'Produce a new task {task}')
            return True
        else:
            if await self.df.seen(task):
                return False
            else:
                await self.q.push(task)
                logger.debug(f'Produce a new task {task}')
                return True

    async def consume(self) -> _Task:
        task = await self.q.pop()
        return task

    async def close(self):
        await self.df.close()
        await self.q.close()
