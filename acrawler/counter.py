import asyncio
from collections import defaultdict
from random import randint

from acrawler.exceptions import ReScheduleError


class BaseCounter:
    def __init__(self, crawler):
        self.crawler = crawler

        # Checking log by special host
        self.conf = (self.crawler.config.get("MAX_REQUESTS_SPECIAL_HOST") or {}).copy()
        self.hosts = list(self.conf.keys())
        self.check = len(self.hosts) > 0

        # Checking log by per host
        self.uni = self.crawler.config.get("MAX_REQUESTS_PER_HOST", 0)
        self.uniconf = {}
        self.unicheck = self.uni > 0

        # Delay config
        self.delay = self.crawler.config.get("DOWNLOAD_DELAY", 0)
        self.conf_delay = self.crawler.config.get(
            "DOWNLOAD_DELAY_SPECIAL_HOST", {}
        ).copy()
        self.hosts_delay = list(self.conf_delay.keys())

    async def unfinished_inc(self, task):
        raise NotImplementedError()

    async def unfinished_dec(self, task):
        raise NotImplementedError()

    async def required_inc(self):
        """Called in delay handler to record current requests"""
        raise NotImplementedError()

    async def required_dec(self):
        """Called in delay handler to record current requests"""
        raise NotImplementedError()

    async def counts_inc(self, task, flag):
        raise NotImplementedError()

    def join(self):
        raise NotImplementedError()

    def join_by_ancestor_unfinished(self):
        raise NotImplementedError()

    async def task_add(self, task, flag: int = 1):
        if flag != -2:
            await self.unfinished_inc(task)

    async def task_done(self, task, flag: int = 1):
        if flag != -2:
            await self.unfinished_dec(task)
        await self.counts_inc(task, flag)

    async def get_counts_dict(self):
        raise NotImplementedError()

    async def get_required(self):
        raise NotImplementedError()

    async def require_req(self, req):

        # Check limit
        req.chosts = []  # this contains hosts for special check
        req.cuni = False  # this flags its state for unicheck

        to_unicheck = True  # special-host-check has higher priority than unicheck
        if self.check:
            for host in self.hosts:
                if host in req.url.host:
                    to_unicheck = False
                    if self.conf[host] > 0:
                        req.chosts.append(host)
                        self.conf[host] -= 1
                        continue
                    else:
                        raise ReScheduleError()

        if self.unicheck and to_unicheck:
            count = self.uniconf.setdefault(req.url.host, self.uni)
            if count > 0:
                self.uniconf[req.url.host] -= 1
                req.cuni = True
            else:
                raise ReScheduleError()

        # Start delay
        origin = True
        target = 0
        for host in self.hosts_delay:
            if host in req.url.host:
                target += self.conf_delay[host]
                origin = False

        if origin:
            target = self.delay

        delay = randint(int(target * 8), (target * 12)) / 10
        await asyncio.sleep(delay)
        await self.required_inc()
        req.inprogress = True

    async def release_req(self, req):

        # Release limit
        if self.unicheck and req.cuni:
            self.uniconf[req.url.host] += 1

        if self.check and req.chosts:
            for host in req.chosts:
                self.conf[host] += 1
        if req.inprogress:
            await self.required_dec()
            req.inprogress = False


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

        # Counts of concurrent requests
        self.required = 0

    async def join(self):
        if self.unfinished > 0:
            await self._finished.wait()

    async def join_by_ancestor_unfinished(self, ancestor):
        while self.ancestor_unfinished[ancestor] != 0:
            await asyncio.sleep(0.5)

    async def counts_inc(self, task, flag):
        if flag >= 0:
            rc = self.counts.setdefault(task.primary_family, [0, 0])
            rc[flag] += 1

    async def get_counts_dict(self):
        return self.counts

    async def get_required(self):
        return self.required

    async def unfinished_inc(self, task):
        if task.ancestor:
            self.ancestor_unfinished[task.ancestor] += 1
        self.unfinished += 1
        self._finished.clear()

    async def unfinished_dec(self, task):
        if task.ancestor:
            self.ancestor_unfinished[task.ancestor] -= 1
        if self.unfinished <= 0:
            raise ValueError("task_done() called too many times")
        self.unfinished -= 1
        if self.unfinished == 0:
            self._finished.set()

    async def required_inc(self):
        self.required += 1

    async def required_dec(self):
        self.required -= 1

    def __getstate__(self):
        state = self.__dict__
        state.pop("_finished", None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.__dict__["_finished"] = asyncio.Event()
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
        cname = crawler.name
        # a redis int
        self.unfinished_key = "acrawler:" + cname + ":c:unfinished"
        self.required_key = "acrawler:" + cname + ":c:required"

        # Redis Sorted Set
        self.ancestor_unfinished_key = "acrawler:" + cname + ":c:ancestor_unfinished"
        # Redis Sorted Set
        self.counts_key_suc = "acrawler:" + cname + ":c:counts_suc"
        self.counts_key_fail = "acrawler:" + cname + ":c:counts_fail"

        self._finished = asyncio.Event(loop=crawler.loop)
        self._finished.set()

    async def join(self):
        if await self.get_unfinished() > 0:
            await self._finished.wait()

    async def join_by_ancestor_unfinished(self, ancestor):
        while (await self.redis.zscore(self.ancestor_unfinished_key, ancestor)) != 0:
            await asyncio.sleep(0.5)

    async def counts_inc(self, task, flag):
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

    async def get_required(self):
        return await self.redis.get(self.required_key)

    async def unfinished_inc(self, task):
        if task.ancestor:
            tr = self.redis.multi_exec()
            tr.zincrby(self.ancestor_unfinished_key, 1, task.ancestor)
            tr.incr(self.unfinished_key)
            await tr.execute()
        else:
            await self.redis.incr(self.unfinished_key)
        self._finished.clear()

    async def unfinished_dec(self, task):
        if task.ancestor:
            tr = self.redis.multi_exec()
            tr.zincrby(self.ancestor_unfinished_key, -1, task.ancestor)
            tr.decr(self.unfinished_key)
            _, res = await tr.execute()
        else:
            res = await self.redis.decr(self.unfinished_key)
        if int(res) == 0:
            self._finished.set()

    async def required_inc(self):
        await self.redis.incr(self.required_key)

    async def required_dec(self):
        await self.redis.decr(self.required_key)
