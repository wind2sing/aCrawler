from acrawler import Parser, Crawler, Processors, ParselItem


def print_first_twenty_words(values):
    if values:
        return values[0][:20]
    else:
        None


class QuoteItem(ParselItem):
    xpath_rules = {'text': './/span[@class="text"]/text()'}
    css_rules = {'author': 'small.author::text'}
    default_rules = {'spider': 'default one'}
    field_processors = {
        'text': print_first_twenty_words,
        'author': Processors.get_first
    }

    def custom_process(self, content):
        self.logger.info(content)


class AuthorItem(ParselItem):
    css_rules = {'name': 'h3.author-title::text',
                'born': 'span.author-born-date::text',
                # 'desc': 'div.author-description::text'
                }
    field_processors = {
        'name': [Processors.get_first, Processors.strip],
        'born': Processors.get_first,
    }


class CrawlerA(Crawler):
    config = {
        'REDIS_ENABLE': False,
        'LOG_LEVEL': 'INFO',
    }

    start_urls = ['http://quotes.toscrape.com/page/1/',
                    'http://quotes.toscrape.com/page/5/',
                    'http://quotes.toscrape.com/page/10/',
                    'http://quotes.toscrape.com/page/15/',
                  ]
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
    CrawlerA().run()
