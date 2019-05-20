from acrawler import Crawler, Request, Response, callback, register
import time

class V2EXCrawler(Crawler):

    def start_requests(self):
        yield Request('https://www.v2ex.com/?tab=hot', family='v2ex', exetime=time.time()+10, recrawl=5)


    def parse(self, response: Response):
        print('hello page!')

    @callback('v2ex')
    def parse_hot2(self, response: Response):
        aa = response.sel.css('.item_title a')
        for a in aa:
            d = {
                'url': response.urljoin(a).split('#')[0],
                'title': a.css('::text').get()
            }
            yield d


@register('DefaultItem')
def process_d(d):
    print(d.content)

if __name__ == "__main__":
    V2EXCrawler().run()
