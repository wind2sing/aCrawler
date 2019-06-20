from acrawler import Crawler, Request, Response, middleware, register, callback
from acrawler.http import FileRequest
from acrawler.utils import open_html
from acrawler.handlers import ResponseCheckStatus
from pathlib import Path


def wh_top(page=1, topRange='1w'):
    return 'https://wallhaven.cc/search?q=&categories=111&purity=110&topRange={}&sorting=toplist&order=desc&page={}'.format(topRange, page)


def wh_fav(page=1):
    return 'https://wallhaven.cc/search?q=&categories=111&purity=110&topRange=1w&sorting=favorites&order=desc&page={}'.format(page)


def img_dir():
    IMG_DIR = Path.home()/'Downloads'/'tmp_wh'
    if not IMG_DIR.exists():
        IMG_DIR.mkdir()
    return IMG_DIR


class WHCrawler(Crawler):
    config = {
        'LOG_LEVEL': 'INFO',
        'MAX_REQUESTS': 8,
        'MAX_RETRIES': 5,
    }

    async def start_requests(self):
        yield Request(wh_top(1), callback=self.parse_top_search)

    def gen_req(self, url):
        return FileRequest(url, meta={'_fdir': self.fdir}, family='wh', status_allowed=[404])

    async def parse_top_search(self, response: Response):
        pids = response.sel.css('#thumbs li a.preview::attr(href)').re(
            r'.*wallhaven\.cc/w/(\w+).*')

        self.fdir = img_dir()
        for pid in pids:
            pre = pid[0:2]
            yield self.gen_req('https://w.wallhaven.cc/full/{}/wallhaven-{}.jpg'.format(pre, pid))

    @callback('wh')
    async def redirect_png(self, response: Response):
        if response.status == 404:
            old_url = response.request.url_str
            if 'jpg' in old_url:
                url = old_url.replace('jpg', 'png')
                yield self.gen_req(url)
            elif 'png' in old_url:
                url = old_url.replace('png', 'jpg')
                yield self.gen_req(url)


if __name__ == "__main__":
    WHCrawler().run()
