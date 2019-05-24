from acrawler import Crawler, Request, Response, ParselItem, Processors, Handler, register, get_logger
from pprint import pprint


def process_time(value):
    # a self-defined field process function
    # process time to minutes
    # '3h 1min' -> 181
    if value:
        res = 0
        segs = value.split(' ')
        for seg in segs:
            if seg.endswith('min'):
                res += int(seg.replace('min', ''))
            elif seg.endswith('h'):
                res += 60*int(seg.replace('h', ''))
        return res
    else:
        return value


class MovieItem(ParselItem):
    css_rules_first = {
        'title': 'h1::text',
        'date': '.subtext a[href*=releaseinfo]::text',
        'time': '.subtext time::text',
        'rating': 'span[itemprop=ratingValue]::text',
        'rating_count': 'span[itemprop=ratingCount]::text',
        'metascore': '.metacriticScore span::text'
    }

    css_rules = {
        'genres': '.subtext a[href*=genres]::text',
        'director': 'h4:contains(Director) ~ a[href*=name]::text',
        'writers': 'h4:contains(Writer) ~ a[href*=name]::text',
        'stars': 'h4:contains(Star) ~ a[href*=name]::text'
    }

    field_processors = {
        'time': process_time
    }

    def custom_process(self, content):
        pprint(content)
        pass


class IMDBCrawler(Crawler):
    config = {
        'LOG_LEVEL': 'INFO',
        'PERSISTENT': True,
        'PERSISTENT_NAME': 'IMDBv0.1'
    }
    max_requests = 6

    async def start_requests(self):
        yield Request('https://www.imdb.com/chart/moviemeter')

    async def parse(self, response):
        count = 0
        for tr in response.sel.css('.lister-list tr'):
            link = tr.css('.titleColumn a::attr(href)').get()
            if link:
                yield Request(response.urljoin(link), callback=self.parse_movie)
                count += 1
                if count==10:
                    break

    async def parse_movie(self, response):
        url = response.url_str
        yield MovieItem(response.sel, extra={'url': url.split('?')[0]})


@register()
class HorrorHandler(Handler):
    family = 'MovieItem'
    logger = get_logger('horrorlogger')

    async def handle_after(self, item):
        if item['genres'] and 'Horror' in item['genres']:
            self.logger.warning(
                "({}) is a horror movie!!!!".format(item['title']))


if __name__ == "__main__":
    IMDBCrawler().run()
