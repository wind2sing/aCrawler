from acrawler import Crawler, Request, Response, middleware
from acrawler.http import FileRequest
from acrawler.utils import open_html
from acrawler.handlers import ResponseCheckStatus
from pathlib import Path


def wh_top(page=1,topRange='1w'):
    return 'https://alpha.wallhaven.cc/search?q=&categories=111&purity=110&topRange={}&sorting=toplist&order=desc&page={}'.format(topRange, page)

def wh_fav(page=1):
    return 'https://alpha.wallhaven.cc/search?q=&categories=111&purity=110&topRange=1w&sorting=favorites&order=desc&page={}'.format(page)

def img_dir():
    IMG_DIR = Path.home()/'Downloads'/'tmp_wh'
    if not IMG_DIR.exists():
        IMG_DIR.mkdir()
    return IMG_DIR

class ChangeExt(ResponseCheckStatus):

    async def on_start(self):
        self.fdir = img_dir()

    async def handle_before(self, response):
        # we are guessing the real url of the image
        if response.status == 404 and response.request.family == 'FileRequest':
            old_url = response.request.url_str
            if 'jpg' in old_url:
                url = old_url.replace('jpg','png')
                await self.crawler.add_task(FileRequest(url, meta={'_fdir': self.fdir}))
            elif 'png' in old_url:
                url = old_url.replace('png','jpg')
                await self.crawler.add_task(FileRequest(url, meta={'_fdir': self.fdir}))
        else:
            await super().handle_before(response)


class WHCrawler(Crawler):
    config = {
        'LOG_LEVEL': 'INFO'
    }

    middleware_config = {
        'acrawler.handlers.ResponseCheckStatus': 0, # disable it
    }
    middleware.append_handler_cls(ChangeExt)
    
    max_requests = 10
    

    async def start_requests(self):
        yield Request(wh_fav(1), callback=self.parse_top_search)


    async def parse_top_search(self, response:Response):
        pids = response.sel.css('#thumbs li a.preview::attr(href)').re('.*wallpaper/(\d+).*')
        fdir = img_dir()
        for pid in pids:
            yield FileRequest('https://wallpapers.wallhaven.cc/wallpapers/full/wallhaven-{}.jpg'.format(pid), meta={'_fdir': fdir})



if __name__ == "__main__":
    WHCrawler().run()
