from acrawler import Crawler, Request, callback, register, ReScheduleError


class V2EXCrawler(Crawler):
    K = 1

    def start_requests(self):
        yield Request('https://www.v2ex.com/?tab=hot',
                      family='v2ex',  # Optional
                      callback=None,  # Optional
                      recrawl=10
                      )

    def parse(self, response):
        print('This is default callback function! Auto combined to any request yield from start_requests().')

    @callback('v2ex')
    def parse_hot(self, response):
        aa = response.sel.css('.item_title a')
        for a in aa:
            d = {
                'url': response.urljoin(a).split('#')[0],
                'title': a.css('::text').get()
            }
            yield d
            if self.K == 1:
                self.K = 0
                print('Reschedule...')
                raise ReScheduleError(defer=5)


@register('DefaultItem')
def process_d(d):
    print(d.content)


if __name__ == "__main__":
    V2EXCrawler().run()
