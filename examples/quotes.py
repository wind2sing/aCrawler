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
