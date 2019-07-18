from acrawler import Crawler, Request, ParselItem, Handler, register, get_logger


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
    else:
        return value


class MovieItem(ParselItem):
    css_rules_first = {
        "title": "h1::text",
        "date": ".subtext a[href*=releaseinfo]::text",
        "time": ".subtext time::text",
        "rating": "span[itemprop=ratingValue]::text",
        "rating_count": "span[itemprop=ratingCount]::text",
        "metascore": ".metacriticScore span::text",
    }

    css_rules = {
        "genres": ".subtext a[href*=genres]::text",
        "director": "h4:contains(Director) ~ a[href*=name]::text",
        "writers": "h4:contains(Writer) ~ a[href*=name]::text",
        "stars": "h4:contains(Star) ~ a[href*=name]::text",
    }

    field_processors = {"time": process_time}


class IMDBCrawler(Crawler):
    config = {"MAX_REQUESTS": 4, "DOWNLOAD_DELAY": 1}

    async def start_requests(self):
        yield Request("https://www.imdb.com/chart/moviemeter", links_to_abs=True)

    async def parse(self, response):
        for tr in response.sel.css(".lister-list tr"):
            link = tr.css(".titleColumn a::attr(href)").get()
            if link:
                yield Request(link, callback=self.parse_movie)

    async def parse_movie(self, response):
        url = response.url_str
        yield MovieItem(response.sel, extra={"url": url.split("?")[0]})


@register()
class HorrorHandler(Handler):
    family = "MovieItem"
    logger = get_logger("horrorlog")

    async def handle_after(self, item):
        if item["genres"] and "Horror" in item["genres"]:
            self.logger.warning("({}) is a horror movie!!!!".format(item["title"]))

            yield {"singal": "Leaving...", "title": item["title"]}


@register("DefaultItem")
def print_item(item):
    print(item.content)


if __name__ == "__main__":
    IMDBCrawler().run()
