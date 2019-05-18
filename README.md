# aCrawler

[![PyPI](https://img.shields.io/pypi/v/acrawler.svg)](https://pypi.org/project/acrawler/)

 🔍 A simple web-crawling framework, based on aiohttp.



This project is at *early* stage and under quick development. 

## Feature

- Write your crawler in one Python script with asyncio
- Schedule task with priority, fingerprint
- Middleware: add handlers before or after tasks
- Simple shortcuts to speed up coding
- Parse html conveniently with Parsel
- Crawl distributedly with Redis

## Installation

To install, simply use [pipenv](http://pipenv.org/) (or pip):

```bash
$ pipenv install acrawler
```



## Usage

```python
class V2EXCrawler(Crawler):
    config ={
        'LOG_LEVEL' : 'DEBUG'
    }
    
    def start_requests(self):
        yield Request('https://www.v2ex.com/?tab=hot', family='v2ex')

    @callback('v2ex')
    def parse_hot(self, response: Response):
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
```



See [examples](examples/).



## Todo

- Schedule task with recrawl mechanism
- Support JavaScript with pyppeteer
- Crawl periodically and persistently
- Monitor all your crawlers
