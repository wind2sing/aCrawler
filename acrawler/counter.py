import asyncio
from collections import defaultdict
from acrawler.exceptions import ReScheduleError


class BaseCounter:

    def __init__(self, crawler):
        self.crawler = crawler

        self.conf = self.crawler.config.get(
            'MAX_REQUESTS_SPECIAL_HOST', {}).copy()
        self.hosts = list(self.conf.keys())
        self.check = len(self.hosts) > 0

        self.uni = self.crawler.config.get('MAX_REQUESTS_PER_HOST', 0)
        self.uniconf = {}
        self.unicheck = self.uni > 0

    async def unfinished_inc(self, task):
        raise NotImplementedError()

    async def unfinished_dec(self, task):
        raise NotImplementedError()

    async def counts_inc(self, task, flag):
        raise NotImplementedError()

    def join(self):
        raise NotImplementedError()

    def join_by_ancestor_unfinished(self):
        raise NotImplementedError()

    async def get_counts(self):
        raise NotImplementedError()

    async def task_add(self, task):
        await self.unfinished_inc(task)

    async def task_done(self, task, flag: int = 1):
        await self.unfinished_dec(task)
        await self.counts_inc(task, flag)

    async def get_counts_dict(self):
        raise NotImplementedError()

    def require_req(self, req):
        if self.unicheck:
            count = self.uniconf.setdefault(req.url.host, self.uni)
            if count > 0:
                self.uniconf[req.url.host] -= 1
            else:
                raise ReScheduleError()

        if self.check:
            req.chosts = []
            for host in self.hosts:
                if host in req.url.host:
                    req.chosts.append(host)
                    if self.conf[host] > 0:
                        self.conf[host] -= 1
                        continue
                    else:
                        raise ReScheduleError()

    def release_req(self, req):
        if self.unicheck:
            self.uniconf[req.url.host] += 1

        if self.check and req.chosts:
            for host in req.chosts:
                self.conf[host] += 1


class Counter(BaseCounter):
    """A normal counter records unfinished count of tasks and manage requests-limits.
    """

    def __init__(self, crawler):
        super().__init__(crawler)
        self.counts = {}
        self.ancestor_unfinished = defaultdict(int)
        self.unfinished = 0
        self._finished = asyncio.Event(loop=crawler.loop)
        self._finished.set()

    async def join(self):
        if self.unfinished > 0:
            await self._finished.wait()

    async def join_by_ancestor_unfinished(self, ancestor):
        while self.ancestor_unfinished[ancestor] != 0:
            await asyncio.sleep(0.5)

    async def counts_inc(self, task, flag):
        if flag != -1:
            rc = self.counts.setdefault(task.primary_family, [0, 0])
            rc[flag] += 1

    async def get_counts_dict(self):
        return self.counts

    async def unfinished_inc(self, task):
        self.ancestor_unfinished[task.ancestor] += 1
        # if not self.crawler.lock_always:
        #     self.unfinished += 1
        #     self._finished.clear()
        self.unfinished += 1
        self._finished.clear()

    async def unfinished_dec(self, task):
        self.ancestor_unfinished[task.ancestor] -= 1
        # if not self.crawler.lock_always:
        if self.unfinished <= 0:
            raise ValueError('task_done() called too many times')
        self.unfinished -= 1
        if self.unfinished == 0:
            self._finished.set()

    def __getstate__(self):
        state = self.__dict__
        state.pop('_finished', None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.__dict__['_finished'] = asyncio.Event()
        if self.unfinished == 0:
            self._finished.set()
        else:
            self._finished.clear()


class RedisCounter(BaseCounter):
    """A counter use redis to store information.
    """

    def __init__(self, crawler):
        super().__init__(crawler)
        self.redis = None
        cname = crawler.__class__.__name__
        # a redis int
        self.unfinished_key = 'acrawler:' + cname + ':c:unfinished'
        # Redis Sorted Set
        self.ancestor_unfinished_key = 'acrawler:' + cname + ':c:ancestor_unfinished'
        # Redis Sorted Set
        self.counts_key_suc = 'acrawler:' + cname + ':c:counts_suc'
        self.counts_key_fail = 'acrawler:' + cname + ':c:counts_fail'

        self._finished = asyncio.Event(loop=crawler.loop)
        self._finished.set()

    async def join(self):
        if await self.get_unfinished() > 0:
            await self._finished.wait()

    async def join_by_ancestor_unfinished(self, ancestor):
        while (await self.redis.zscore(self.ancestor_unfinished_key, ancestor)) != 0:
            await asyncio.sleep(0.5)

    async def counts_inc(self, task, flag):
        if flag != -1:
            if flag == 1:
                await self.redis.zincrby(self.counts_key_suc, 1, task.primary_family)
            elif flag == 0:
                await self.redis.zincrby(self.counts_key_fail, 1, task.primary_family)

    async def get_unfinished(self):
        return int(await self.redis.get(self.unfinished_key) or 0)

    async def get_counts_dict(self):
        res = {}
        async for val, score in self.redis.izscan(self.counts_key_suc):
            rc = res.setdefault(val.decode(), [0, 0])
            rc[1] = int(score)
        async for val, score in self.redis.izscan(self.counts_key_fail):
            rc = res.setdefault(val.decode(), [0, 0])
            rc[0] = int(score)

        return res

    async def unfinished_inc(self, task):
        tr = self.redis.multi_exec()
        tr.zincrby(self.ancestor_unfinished_key, 1, task.ancestor)
        tr.incr(self.unfinished_key)
        await tr.execute()
        self._finished.clear()

    async def unfinished_dec(self, task):
        tr = self.redis.multi_exec()
        tr.zincrby(self.ancestor_unfinished_key, -1, task.ancestor)
        tr.decr(self.unfinished_key)
        _, res = await tr.execute()
        if int(res) == 0:
            self._finished.set()