from acrawler import Crawler, Request, ParselItem, Handler, register, get_logger


class MovieItem(ParselItem):
    log = True
    css = {
        # just some normal css rules
        "date": ".subtext a[href*=releaseinfo]::text",
        "time": ".subtext time::text",
        "rating": "span[itemprop=ratingValue]::text",
        "rating_count": "span[itemprop=ratingCount]::text",
        "metascore": ".metacriticScore span::text",
        # if you provide a list with additional functions,
        # they are considered as field processor function
        "title": ["h1::text", str.strip],
        # the following four fules is get all matching values
        # the rule starts with [ and ends with ] comparing to normal rules
        "genres": "[.subtext a[href*=genres]::text]",
        "director": "[h4:contains(Director) ~ a[href*=name]::text]",
        "writers": "[h4:contains(Writer) ~ a[href*=name]::text]",
        "stars": "[h4:contains(Star) ~ a[href*=name]::text]",
    }


class IMDBCrawler(Crawler):
    config = {"MAX_REQUESTS": 4, "DOWNLOAD_DELAY": 1}

    async def start_requests(self):
        yield Request("https://www.imdb.com/chart/moviemeter")

    def parse(self, response):
        yield from response.follow(
            ".lister-list tr .titleColumn a::attr(href)", callback=self.parse_movie
        )

    def parse_movie(self, response):
        url = response.url_str
        yield MovieItem(response.sel, extra={"url": url.split("?")[0]})


@register()
class HorrorHandler(Handler):
    family = "MovieItem"
    logger = get_logger("horrorlog")

    async def handle_after(self, item):
        if item["genres"] and "Horror" in item["genres"]:
            self.logger.warning(f"({item['title']}) is a horror movie!!!!")


@MovieItem.bind()
def process_time(value):
    # a self-defined field processing function
    # process time to minutes
    # '3h 1min' -> 181
    if value:
        res = 0
        segs = value.split(" ")
        for seg in segs:
            if seg.endswith("min"):
                res += int(seg.replace("min", ""))
            elif seg.endswith("h"):
                res += 60 * int(seg.replace("h", ""))
        return res
    return value


if __name__ == "__main__":
    IMDBCrawler().run()
