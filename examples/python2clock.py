from acrawler.http import BrowserRequest
from acrawler import Crawler, get_logger

logger = get_logger("pyclock")


class ClockCrawler(Crawler):

    middleware_config = {
        # you should enable this handler to support BrowserRequest
        "acrawler.handlers.RequestPrepareBrowser": 800
    }

    async def start_requests(self):
        yield BrowserRequest(
            url="https://pythonclock.org", page_callback=self.operate_page
        )

    async def operate_page(self, page, response):
        logger.info(await response.text())
        logger.info(await page.text())
        assert not "countdown-amount" in (await response.text())
        assert "countdown-amount" in (await page.text())
        await page.screenshot(show=True)


if __name__ == "__main__":
    ClockCrawler().run()
