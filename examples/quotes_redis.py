from acrawler import Parser, Crawler, Processors, ParselItem, get_logger
from acrawler.setting import REDIS_START_KEY
from acrawler.utils import redis_push_start_urls


logger = get_logger('quotes')

def get_twenty_words(value):
    return value[:20]


class QuoteItem(ParselItem):
    xpath_rules = {'text': './/span[@class="text"]/text()'}
    css_rules = {'author': 'small.author::text'}
    default_rules = {'spider': 'default one'}
    field_processors = {
        'text': [Processors.get_first, get_twenty_words],
        'author': Processors.get_first
    }

    def custom_process(self, content):
        logger.info(content)


class AuthorItem(ParselItem):
    css_rules = {'name': 'h3.author-title::text',
                'born': 'span.author-born-date::text',
                'desc': 'div.author-description::text'
                }
    field_processors = {
        'name': [Processors.get_first, Processors.strip],
        'born': Processors.get_first,
        'desc': [Processors.get_first, Processors.strip, get_twenty_words]
    }

    def custom_process(self, content):
        logger.info(content)


class QuoteCrawler(Crawler):
    config = {
        'LOG_LEVEL': 'INFO',
        'REDIS_ENABLE': True,
        'REDIS_START_KEY': REDIS_START_KEY,
        'REDIS_ITEMS_KEY': 'acrawler.quotes.items',
    }

    middleware_config = {
        'acrawler.handlers.ItemToRedis': 100
    }

    max_requests = 10

    main_page = r'quotes.toscrape.com/page/\d+'
    author_page = r'quotes.toscrape.com/author/.*'
    Parsers = [Parser(in_pattern=main_page,
                      follow_patterns=[main_page, author_page],
                      item_type=QuoteItem,
                      css_divider='.quote'
                      ),
               Parser(in_pattern=author_page, item_type=AuthorItem)
               ]


if __name__ == '__main__':
    print('Adding start urls to Redis, key: {}'.format(REDIS_START_KEY))
    start_urls = ['http://quotes.toscrape.com/page/1/',
                    'http://quotes.toscrape.com/page/5/',
                    'http://quotes.toscrape.com/page/10/',
                    'http://quotes.toscrape.com/page/15/',
                  ]
    redis_push_start_urls(REDIS_START_KEY, start_urls)

    QuoteCrawler().run()
    # Crawler always listen to redis and won't finish.
    # This behaviour is determined by acrawler.handlers.CrawlerFinishAddon
