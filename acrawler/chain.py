from acrawler.crawler import Crawler
from acrawler.http import Request, Response
from acrawler.item import ParselItem


class ChainCrawler:
    def __init__(
        self,
        concurrency=4,
        delay=0,
        config: dict = None,
        middleware_config: dict = None,
        request_config: dict = None,
    ):
        config = config or {}
        config["MAX_REQUESTS"] = concurrency
        config["DOWNLOAD_DELAY"] = delay
        self._crawler = Crawler(config, middleware_config, request_config)

    def add(self, task):
        for t in task.to_vanilla():
            self._crawler.add_task_sync(t)
        return self

    def run(self):
        self._crawler.run()
        return self


class ChainRequest:
    def __init__(self, family=None):
        self._urls = []
        self._kws = {}
        self._kws["family"] = family
        self._kws["method"] = "GET"
        self._kws["callback"] = []

    def meta(self, meta: dict):
        m = self._kws.setdefault("meta", {})
        m.update(meta)
        return self

    def request(self, urls, method="GET"):
        self._kws["method"] = "GET"
        if isinstance(urls, list):
            self._urls.extend(urls)
        else:
            self._urls.append(urls)
        return self

    def get(self, urls):
        return self.request(urls)

    def callback(self, func):
        self._kws["callback"].append(func)
        return self

    def spawn(self, item, css=None):
        def fn(resp: Response):
            if css:
                for sel in resp.sel.css(css):
                    yield from item.to_vanilla(sel)
            else:
                yield from item.to_vanilla(resp.sel)

        self._kws["callback"].append(fn)
        return self

    def cb(self, func):
        return self.callback(func)

    def follow(self, css: str, limit: int = 0, pass_meta=False, **kwargs):
        req = ChainRequest()
        if pass_meta:
            req.meta(self._kws.get("meta", {}))
            if "meta" in kwargs:
                req.meta(kwargs.pop("meta"))

        def fn(resp: Response):
            count = 0
            for url in resp.sel.css(css).getall():
                m = req._kws.pop("meta", {})
                if resp.meta:
                    m.update(resp.meta)
                yield Request(url, meta=m, **req._kws, **kwargs)
                count += 1
                if limit and count >= limit:
                    break

        self._kws["callback"].append(fn)
        return req

    def paginate(self, css: str, limit: int = 0, pass_meta=False, **kwargs):
        req = self.follow(css, limit, pass_meta)
        # while paginating, these requests share same callback list
        req._kws["callback"] = self._kws["callback"]
        return req

    def debug(self, css: str):
        def fn(resp: Response):
            print(resp.sel.css(css).get())

        self._kws["callback"].append(fn)
        return self

    def to_vanilla(self, **kwargs):
        for url in self._urls:
            yield Request(url, **self._kws, **kwargs)

    def bind(self):
        """ decorator, bind callback function. """

        def decorator(func):
            self._kws["callback"].append(func)
            return func

        return decorator


class ChainItem:
    def __init__(self, family=None):
        self._kws = {}
        self._kws["family"] = family
        self._kws["css"] = {}
        self._kws["xpath"] = {}
        self._kws["re"] = {}

    def extra(self, extra: dict):
        m = self._kws.setdefault("extra", {})
        m.update(extra)
        return self

    def css(self, rules: dict):
        self._kws["css"].update(rules)
        return self

    def xpath(self, rules: dict):
        self._kws["xpath"].update(rules)
        return self

    def re(self, rules: dict):
        self._kws["re"].update(rules)
        return self

    def to_vanilla(self, sel, **kwargs):
        yield ParselItem(sel, **self._kws, **kwargs)

