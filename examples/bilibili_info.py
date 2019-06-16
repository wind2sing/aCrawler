# scrape Bilibili video info
from acrawler import Crawler, Request, Item, middleware, Handler, register
from pprint import pprint as print

from acrawler.handlers import ItemToRedis, ItemToMongo
import json

MIN_TID = 1
MAX_TID = 250


class ChannelItem(Item):
    log = True
    pass


class OneItem(Item):
    pass


class BiliInfoCrawler(Crawler):

    config = {
        'DOWNLOAD_DELAY': 0.2,
        'MAX_REQUESTS': 3,
        'MAX_WORKERS': 20,
    }

    async def start_requests(self):
        for tid in range(MIN_TID, MAX_TID+1):
            url = 'http://api.bilibili.com/x/web-interface/newlist?rid={}&pn=1&ps=1'.format(
                tid)
            yield Request(url, callback=self.parse_json, meta={'tid': tid})

    def parse_json(self, response):
        tid = response.meta['tid']
        info = response.json
        data = info['data']
        page = data['page']
        count = page['count']
        if count > 1:
            v_info = data['archives'][0]
            new_tid = v_info['tid']
            if new_tid == tid:
                tname = v_info['tname']
                item = {'tid': tid,
                        'tname': tname,
                        'count': count, 'url': f'http://api.bilibili.com/x/web-interface/newlist?rid={tid}'}
                yield ChannelItem(extra=item)

                for pn, ps in self.get_pn_ps(count):
                    url = f'http://api.bilibili.com/x/web-interface/newlist?rid={tid}&pn={pn}&ps={ps}'
                    yield OneItem(extra={'url': url})

    def get_pn_ps(self, count):
        ps = 50
        max_n = count//50+1
        for pn in range(1, max_n+1):
            yield pn, ps


@register()
class BiliToRedis(ItemToRedis):
    family = 'OneItem'
    items_key = 'bili:vsurls'

    async def handle_after(self, item):
        url = item['url']
        await self.redis.sadd(self.items_key, url)


@register()
class BiliToMongo(ItemToMongo):
    family = 'ChannelItem'
    db_name = 'bili'
    col_name = 'channel'
    primary_key = 'tid'


if __name__ == "__main__":
    BiliInfoCrawler().run()
