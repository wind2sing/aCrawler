from acrawler.handlers import ItemDebug
from acrawler import Crawler, Request, ParselItem, Parser, middleware

import re
import random

PATTERN = re.compile(
    r'\b((?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9]))\D*([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])')

WEBSITES = [
    {
        'name': 'xicidaili.com',
        'resource': ['http://www.xicidaili.com/nn/%s' % i for i in range(1, 6)] +
                    ['http://www.xicidaili.com/wn/%s' % i for i in range(1, 6)] +
                    ['http://www.xicidaili.com/wt/%s' %
                        i for i in range(1, 6)],
        'enable':1,

    },
    {
        'name': 'kuaidaili.com',
        'resource': ['https://www.kuaidaili.com/free/inha/%s' % i for i in range(1, 6)] +
                    ['https://www.kuaidaili.com/proxylist/%s' %
                        i for i in range(1, 11)],
        'enable':1,
    },
    {
        'name': 'mrhinkydink.com',
        'resource': ['http://www.mrhinkydink.com/proxies.htm'],
        'enable':1,
    },
]


class ProxyItem(ParselItem):

    def custom_process(self, content):
        match = PATTERN.search(self.sel.extract())
        if match:
            ip = match.groups()[0]
            port = match.groups()[1]
            content['proxy'] = ip+':'+port
            self.logger.info(content)


class ProxyCrawler(Crawler):

    config = {
        'DOWNLOAD_DELAY': 1,
    }

    max_requests = 2

    Parsers = [Parser(css_divider='table tr', item_type=ProxyItem)]

    async def start_requests(self):
        urls = []
        for web in WEBSITES:
            if web['enable']:
                for url in web['resource']:
                    urls.append(url)

        random.shuffle(urls)
        for url in urls:
            yield Request(url, callback=self.par)

    def par(self, response):
        print(response)


if __name__ == "__main__":
    ProxyCrawler().run()
