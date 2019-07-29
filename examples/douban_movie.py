from acrawler import Crawler, ParselItem, Parser, Processors


def print_first_twenty_words(values):
    if values:
        return values[0][:20]


class MovieItem(ParselItem):
    css_rules_first = {"name": "h1 > span::text"}
    field_processors = {"name": [Processors.strip]}

    def custom_process(self, content):
        print(content)


class MyCrawler(Crawler):
    start_urls = ["https://movie.douban.com/top250"]
    config = {"MAX_REQUESTS": 2}

    main_page = r"movie.douban.com/top250.*"
    sub_page = r"movie.douban.com/subject/\d+/$"
    parsers = [
        Parser(in_pattern=main_page, follow_patterns=[main_page, sub_page]),
        Parser(in_pattern=sub_page, item_type=MovieItem),
    ]


if __name__ == "__main__":
    MyCrawler().run()
