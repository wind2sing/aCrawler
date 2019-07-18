# Scrape quotes from http://quotes.toscrape.com/
from acrawler import get_logger
from acrawler import Parser, Crawler, ParselItem, Request


logger = get_logger("quotes")


class QuoteItem(ParselItem):
    log = True
    default_rules = {"type": "quote"}
    css_rules_first = {"author": "small.author::text"}
    xpath_rules_first = {"text": './/span[@class="text"]/text()'}

    field_processors = {"text": lambda s: s.strip("“")[:20]}


class AuthorItem(ParselItem):
    log = True
    default_rules = {"type": "author"}
    css_rules_first = {
        "name": "h3.author-title::text",
        "born": "span.author-born-date::text",
    }


class QuoteCrawler(Crawler):

    main_page = r"quotes.toscrape.com/page/\d+"
    author_page = r"quotes.toscrape.com/author/.*"
    parsers = [
        Parser(
            in_pattern=main_page,
            follow_patterns=[main_page, author_page],
            item_type=QuoteItem,
            css_divider=".quote",
        ),
        Parser(in_pattern=author_page, item_type=AuthorItem),
    ]

    async def start_requests(self):
        yield Request(url="http://quotes.toscrape.com/page/1/")


if __name__ == "__main__":
    QuoteCrawler().run()
