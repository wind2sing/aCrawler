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
        self._crawler.add_task_sync(task.to_vanilla())
        return self

    def run(self):
        self._crawler.run()
        return self


class ChainRequest:
    def __init__(self, family=None):
        self._kws = {}
        self._kws["family"] = family
        self._kws["method"] = "GET"
        self._kws["callback"] = []

    def meta(self, meta: dict):
        m = self._kws.setdefault("meta", {})
        m.update(meta)
        return self

    def request(self, url, method="GET"):
        self._kws["method"] = "GET"
        self._kws["url"] = url
        return self

    def get(self, url):
        return self.request(url)

    def callback(self, func):
        self._kws["callback"].append(func)
        return self

    def spawn(self, item, css=None):
        def fn(resp: Response):
            if css:
                for sel in resp.sel.css(css):
                    yield item.to_vanilla(sel)
            else:
                yield item.to_vanilla(resp.sel)

        self._kws["callback"].append(fn)
        return self

    def cb(self, func):
        return self.callback(func)

    def follow(self, css: str, limit: int = 0, **kwargs):
        req = ChainRequest()

        def fn(resp: Response):
            count = 0
            for url in resp.sel.css(css).getall():
                request = req.get(url).to_vanilla()
                yield request
                count += 1
                if limit and count >= limit:
                    break

        self._kws["callback"].append(fn)
        return req

    def paginate(self, css: str, limit: int = 0, **kwargs):
        req = self.follow(css, limit)
        # while paginating, these requests share same callback list
        req._kws["callback"] = self._kws["callback"]
        return req

    def debug(self, css: str):
        def fn(resp: Response):
            print(resp.sel.css(css).get())

        self._kws["callback"].append(fn)
        return self

    def to_vanilla(self, **kwargs):
        return Request(**self._kws, **kwargs)

