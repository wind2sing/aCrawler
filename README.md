# aCrawler

[![PyPI](https://img.shields.io/pypi/v/acrawler.svg)](https://pypi.org/project/acrawler/)

 🔍 A simple web-crawling framework, based on aiohttp.



This project is at *early* stage and under quick development. 

## Feature

- Write your crawler in one Python script with asyncio
- Schedule task with priority, fingerprint, exetime, recrawl...
- Middleware: add handlers before or after tasks
- Simple shortcuts to speed up scripting
- Parse html conveniently with Parsel
- Stop and Resume: crawl periodically and persistently
- Distributed work support with Redis

## Installation

To install, simply use [pipenv](http://pipenv.org/) (or pip):

```bash
$ pipenv install acrawler
```



## Sample code

```python
# Scrape quotes from http://quotes.toscrape.com/
from acrawler import Parser, Crawler, Processors, ParselItem, get_logger, Request

logger = get_logger('quotes')


def get_twenty_words(value):
    return value[:20]


class QuoteItem(ParselItem):
    log = True
    default_rules = {'type': 'quote'}
    css_rules_first = {'author': 'small.author::text'}
    xpath_rules_first = {'text': './/span[@class="text"]/text()'}

    field_processors = {
        'text': get_twenty_words,
    }


class AuthorItem(ParselItem):
    css_rules_first = {'name': 'h3.author-title::text',
                       'born': 'span.author-born-date::text',
                       }
    field_processors = {
        'name': [Processors.strip,],
    }


class QuoteCrawler(Crawler):
    config = {'LOG_LEVEL': 'DEBUG'}

    start_urls = ['http://quotes.toscrape.com/page/1/', ]

    main_page = r'quotes.toscrape.com/page/\d+'
    author_page = r'quotes.toscrape.com/author/.*'
    parsers = [Parser(in_pattern=main_page,
                      follow_patterns=[main_page, author_page],
                      item_type=QuoteItem,
                      css_divider='.quote'
                      ),
               Parser(in_pattern=author_page, item_type=AuthorItem)
               ]


if __name__ == '__main__':
    QuoteCrawler().run()
```



```python
# Scrape v2ex.com/?tab=hot every 5 seconds
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
```



See [examples](examples/).



## Todo

- Support JavaScript with pyppeteer
- Monitor all your crawlers
