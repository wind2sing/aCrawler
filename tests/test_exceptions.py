from acrawler.exceptions import ReScheduleError, SkipTaskError
from acrawler import Crawler


class SkipCrawler(Crawler):
    config = {"LOG_LEVEL": "ERROR"}

    start_urls = ["http://quotes.toscrape.com/page/1/"]
    count = 0

    async def parse(self, response):
        raise SkipTaskError()
        self.count += 1


class ReScheduleCrawler(Crawler):
    config = {"LOG_LEVEL": "ERROR"}

    start_urls = ["http://quotes.toscrape.com/page/1/"]
    count = 0

    async def parse(self, response):
        if self.count == 0:
            self.count += 1
            raise ReScheduleError()


def test_skiptask():
    crawler = SkipCrawler()
    crawler.run()
    assert crawler.count == 0


def test_reschedule():
    crawler = ReScheduleCrawler()
    crawler.run()
    assert crawler.count == 1
