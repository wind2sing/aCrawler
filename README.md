# aCrawler

[![PyPI](https://img.shields.io/pypi/v/acrawler.svg)](https://pypi.org/project/acrawler/)

 🔍 A simple web-crawling framework, based on aiohttp.



This project is at *very early* stage.

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

(Optional)
$ pipenv install uvloop (only Linux/Mac)
$ pipenv install aioredis (if you need Redis support)
$ pipenv install motor (if you need MongoDB support)
```



## QuickStart



### Your first script

```python
from acrawler import Crawler, Request, callback, register

class V2EXCrawler(Crawler):

    def start_requests(self):
        yield Request('https://www.v2ex.com/?tab=hot',
                      family='v2ex',  # Optional
                      callback=None,  # Optional
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


@register('DefaultItem')
def process_d(d):
    print(d.content)


if __name__ == "__main__":
    V2EXCrawler().run()

```

- `start_requests()` is the entry point. Default implementaion will yield `Request` form Crawler's `start_urls` List.

- Any `Request` yielded from `start_requests()` will combine `crawler.parse()` to its callbacks and passes all callbacks to `Response`

- `Response` executes by calling its callbacks. Callback funtion should accepts one argument `response`. `response.sel` is a `Selector`. See [Parsel](https://parsel.readthedocs.io/en/latest/).

  

### About Tasks

Anything in aCrawler is a `Task`, which `executes` and then may yield new `Tasks`. 

There are several basic `Tasks` defined here.

- `Request` task executes its default `fetch()` method and automatically  yield a corresponding  `Response` task. You can pass a function to its `callback` argument.
- `Response` task executes its `callback` function and may yield new `Task`. A `Response` may have several callback functions (which are passed from request)
- `Item` task executes its `custom_process` method.
- `ParselItem` extends from `Item` . It accepts a `Selector` and uses `Parsel` to parse content.
- Any new `Task` yielded from an existing `Task`'s execution will be catched and delivered to scheduler.
- Any new `dictionary` yielded from an existing `Task`'s execution will be catched as `DefaultItem`.



### About family

- Each handler has only one family
- Each tasks has `families` (defaults to names of all base classes and itself). If you pass `family` to a task, it will be added to task's families. Specially, a `Request`'s user-passed `family` will be passed to its `Response`'s family.
- `family` is used for `handler` and `callback`
  - You can use decorator `@register()` to add a `handler` to crawler. If a `handler`'s family is in a `task`'s families, then `handler` matches `task`. It will start work on this `task`.
- You can use decorator `@callback()` to add a callback to `response`. If `family` in `@callback()` is in a `response`'s families, then callback will be combined to this `response`.



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

See [examples](examples/).



## Todo

- Support JavaScript with pyppeteer
- Monitor all your crawlers
