from acrawler import Crawler, ParselItem, Parser, Processors as x


class MovieItem(ParselItem):
    css = {"name": ["h1 > span::text", x.strip()]}

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
