import asyncio
from acrawler import Parser, Crawler, ParselItem, Processors


def print_first_twenty_words(values):
    if values:
        return values[0][:20]
    else:
        None


class MovieItem(ParselItem):
    css_rule = {'name': 'h1 > span::text',
                }
    field_processors = {
        'name': [Processors.get_first, Processors.strip],
    }

    def custom_process(self, content):
        print(content)


class MyCrawler(Crawler):
    start_urls = ['https://movie.douban.com/top250']
    max_requests = 2

    main_page = 'movie.douban.com/top250.*'
    sub_page = 'movie.douban.com/subject/\d+/$'
    Parsers = [Parser(in_pattern=main_page,
                      follow_patterns=[main_page, sub_page], ),
               Parser(in_pattern=sub_page, item_type=MovieItem
                      )]


if __name__ == '__main__':
    MyCrawler().run()
