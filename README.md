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
import time

logger = get_logger('quotes')

def get_twenty_words(value):
    return value[:20]

class QuoteItem(ParselItem):
    default_rules = {'type': 'quote'}
    css_rules_first = {'author': 'small.author::text'}
    xpath_rules_first = {'text': './/span[@class="text"]/text()'}

    field_processors = {
        'text': get_twenty_words,
    }

    def custom_process(self, content):
        logger.info(content)


class AuthorItem(ParselItem):
    css_rules_first = {'name': 'h3.author-title::text',
                'born': 'span.author-born-date::text',
                'desc': 'div.author-description::text'
                }
    field_processors = {
        'name': [Processors.strip],
        'desc': [Processors.strip, get_twenty_words]
    }

    def custom_process(self, content):
        logger.info(content)


class QuoteCrawler(Crawler):
    config = {
        'LOG_LEVEL': 'INFO',
        'PERSISTENT': True,
        'PERSISTENT_NAME': 'Quote',
    }

    start_urls = ['http://quotes.toscrape.com/page/1/',
                    'http://quotes.toscrape.com/page/5/',
                    'http://quotes.toscrape.com/page/10/',
                    'http://quotes.toscrape.com/page/15/',
                  ]
    max_requests = 5

    main_page = r'quotes.toscrape.com/page/\d+'
    author_page = r'quotes.toscrape.com/author/.*'
    Parsers = [Parser(in_pattern=main_page,
                      follow_patterns=[main_page, author_page],
                      item_type=QuoteItem,
                      css_divider='.quote'
                      ),
               Parser(in_pattern=author_page, item_type=AuthorItem)
               ]

    async def start_requests(self):
        for url in self.start_urls:
            yield Request(url, exetime=time.time()+5)


if __name__ == '__main__':
    QuoteCrawler().run()
```



See [examples](examples/).



## Todo

- Support JavaScript with pyppeteer
- Monitor all your crawlers
