from pprint import pformat
from acrawler.crawler import Crawler
from acrawler.http import Request, Response
from acrawler.item import ParselItem, Item
from acrawler.utils import check_import, to_asyncgen
from acrawler.middleware import register

from collections.abc import Iterable


class ChainCrawler:
    def __init__(self, concurrency=4, delay=0):
        self.config = {}
        self.middleware_config = {}
        self.request_config = {}

        self.concurrency(concurrency)
        self.delay(delay)

        self.task_pool = []  # storage for ChainRequest
        self._parse_query_func = None  # query parser function for web service
        self._after_query_func = None
        self.crawler: Crawler = None  # Crawler instance

    def conf(
        self, conf: dict = None, middleware_conf: dict = None, request_conf: dict = None
    ):
        if conf:
            self.config.update(conf)
        if middleware_conf:
            self.middleware_config.update(middleware_conf)
        if request_conf:
            self.request_config.update(request_conf)
        return self

    def concurrency(
        self,
        max_requests=4,
        max_requests_per_host=0,
        max_requests_special_host: dict = None,
        max_workers=None,
    ):
        self.config["MAX_REQUESTS"] = max_requests
        self.config["MAX_WORKERS"] = max_workers or max_requests
        self.config["MAX_REQUESTS_PER_HOST"] = max_requests_per_host
        self.config["MAX_REQUESTS_SPECIAL_HOST"] = max_requests_special_host or {}
        return self

    def delay(self, delay=0):
        self.config["DOWNLOAD_DELAY"] = delay
        return self

    def retry(self, retry=3):
        self.config["MAX_TRIES"] = retry
        return self

    def use(self, handler_cls, config: dict = None):
        """Register a handler"""
        self.config.update(config or {})
        register()(handler_cls)
        return self

    def add(self, task):
        """Add a Chain-Task"""
        if isinstance(task, Iterable):
            self.task_pool.extend(task)
        else:
            self.task_pool.append(task)
        return self

    def to_vanilla(self):
        while self.task_pool:
            task = self.task_pool.pop()
            for t in task.to_vanilla():
                yield t

    def run(self):
        """Entry method to initialize the Cralwer instance."""
        self.crawler = Crawler(self.config, self.middleware_config, self.request_config)
        if self._parse_query_func:

            def _web_add_task_query(query):
                self._parse_query_func(query)
                yield from self.to_vanilla()

            self.crawler.web_add_task_query = _web_add_task_query

            if self._after_query_func:
                self.crawler.web_action_after_query = self._after_query_func

        for t in self.to_vanilla():
            self.crawler.add_task_sync(t)

        self.crawler.run()
        return self

    def web(self, host="localhost", port=8079):
        """ decorator, bind web query parser function. """
        self.config.update({"WEB_ENABLE": True, "WEB_HOST": host, "WEB_PORT": 8079})

        def decorator(func=None):
            self._parse_query_func = func
            return func

        return decorator

    def web_after_query(self):
        def decorator(func):
            self._after_query_func = func
            return func

        return decorator


class ChainRequest:
    def __init__(self, family=None):
        self._urls = []
        self.kws = {}
        self.kws["family"] = family
        self.kws["method"] = "GET"
        self.kws["callback"] = []

    def status_allowed(self, allowed):
        self.kws["status_allowed"] = allowed
        return self

    def meta(self, meta: dict):
        m = self.kws.setdefault("meta", {})
        m.update(meta)
        return self

    def request(self, urls, method="GET", **kwargs):
        self.kws["method"] = "GET"
        self.kws.update(kwargs)
        if isinstance(urls, list):
            self._urls.extend(urls)
        else:
            self._urls.append(urls)
        return self

    def get(self, urls, **kwargs):
        return self.request(urls, **kwargs)

    def add_callback(self, func):
        self.kws["callback"].append(func)
        return self

    def spawn(self, item, divider=None, allowed=[200], xpath=False):
        def fn(resp: Response):
            if resp.status in allowed:
                if divider:
                    sels = resp.sel.xpath(divider) if xpath else resp.sel.css(divider)
                    for sel in sels:
                        yield from item.to_vanilla(sel, meta=resp.meta)
                else:
                    yield from item.to_vanilla(resp.sel, meta=resp.meta)

        self.kws["callback"].append(fn)
        return self

    def follow(self, css: str, limit: int = 0, pass_meta=False, **kwargs):
        req = ChainRequest()
        req.meta(kwargs.pop("meta", {}))
        if pass_meta:
            req.meta(self.kws.pop("meta", {}))

        def fn(resp: Response):
            count = 0
            for url in resp.sel.css(css).getall():
                m = req.kws.pop("meta", {})
                if resp.meta:
                    m.update(resp.meta)
                yield Request(url, meta=m, **req.kws, **kwargs)
                count += 1
                if limit and count >= limit:
                    break

        self.kws["callback"].append(fn)
        return req

    def paginate(self, css: str, limit: int = 0, pass_meta=False, **kwargs):
        req = self.follow(css, limit, pass_meta)
        # while paginating, these requests share same callback list
        req.kws["callback"] = self.kws["callback"]
        return req

    def debug(self, css: str):
        def fn(resp: Response):
            print(resp.sel.css(css).get())

        self.kws["callback"].append(fn)
        return self

    def to_vanilla(self, **kwargs):
        while self._urls:
            url = self._urls.pop()
            yield Request(url, **self.kws, **kwargs)

    def callback(self):
        """ decorator, bind callback function. """

        def decorator(func):
            self.kws["callback"].append(func)
            return func

        return decorator


class ChainItem:
    def __init__(self, family=None):
        self.kws = {}
        self.kws["family"] = family
        self.kws["css"] = {}
        self.kws["xpath"] = {}
        self.kws["re"] = {}
        self.primary_family = family or "Item"

    def extra(self, extra: dict):
        m = self.kws.setdefault("extra", {})
        m.update(extra)
        return self

    def extra_from_meta(self):
        self.kws["extra_from_meta"] = True
        return self

    def store(self):
        self.kws["store"] = True
        return self

    def css(self, rules: dict):
        self.kws["css"].update(rules)
        return self

    def xpath(self, rules: dict):
        self.kws["xpath"].update(rules)
        return self

    def re(self, rules: dict):
        self.kws["re"].update(rules)
        return self

    def to_vanilla(self, sel=None, **kwargs):
        yield ParselItem(sel, **self.kws, **kwargs)

    def register(self, position: int = None, priority: int = None):
        """ decorator, register a handler function. """

        family = self.primary_family
        return register(family, position, priority)

    def to_mongo(
        self, db, col, key=None, priority=100, address="mongodb://localhost:27017"
    ):
        mo = check_import("motor.motor_asyncio")
        mongo_client = mo.AsyncIOMotorClient(address)
        mongo_db = mongo_client[db]
        mongo_col = mongo_db[col]

        async def quick_to_mongo(item):
            if key:
                await mongo_col.update_many(
                    {key: item[key]}, {"$set": item.content}, upsert=True
                )
            else:
                await mongo_col.insert_one(item.content)

        register(self.primary_family, priority=priority)(quick_to_mongo)
        return self

    def debug(self, priority=100, pretty=False):
        def quick_debug_item(item):
            if pretty:
                print(pformat(item.content))
            else:
                print(item)

        register(self.primary_family, priority=priority)(quick_debug_item)

        return self

