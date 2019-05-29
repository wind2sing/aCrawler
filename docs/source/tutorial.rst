########
Tutorial
########

In this tutorial, we will scrape information of popular movies from `IMDB <https://www.imdb.com/chart/moviemeter>`_

Code is avaliable at `Examples <https://github.com/pansenlin30/aCrawler/blob/master/examples>`_.


Start Requests
**************

First, we start our script with rewritting :meth:`~acrawler.acrawler.Crawler.start_requests`::

    from acrawler import Crawler, Request
    class IMDBCrawler(Crawler):
        config = {'MAX_REQUESTS': 6}

        async def start_requests(self):
            yield Request('https://www.imdb.com/chart/moviemeter')

Here we don't explictly pass ``callback`` parameter to :class:`~acrawler.http.Request` because the default :meth:`~acrawler.crawler.Crawler.parse` will automatically be binded as callback function to it for any request yielded from :meth:`~acrawler.crawler.Crawler.start_requests`.


First Callback Parse
********************

Then we rewrite :meth:`~acrawler.acrawler.Crawler.parse` to parse the response::

    class IMDBCrawler(Crawler):

        async def parse(self, response):
            for tr in response.sel.css('.lister-list tr'):
                link = tr.css('.titleColumn a::attr(href)').get()
                if link:
                    yield Request(response.urljoin(link), callback=self.parse_movie)

During parsing, the most important attribute is :attr:`acrawler.http.Response.sel`. It is a `Parsel <https://parsel.readthedocs.io/en/latest/>`_ ``Selector``. In this callback function, we also yield many new tasks :class:`~acrawler.http.Request` and we explictly pass ``callback`` parameter to them.

Define MovieItem
****************

Then we need to define a new :class:`~acrawler.item.ParselItem` to store results::

    from acrawler import ParselItem
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
                    res += int(seg.replace('min',''))
                elif seg.endswith('h'):
                    res += 60*int(seg.replace('h',''))
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


Parse Movie Page
****************

Then we write our callback function for movie page::

    class IMDBCrawler(Crawler):

        async def parse_movie(self, response):
            url = response.url_str
            yield MovieItem(response.sel, extra={'url': url.split('?')[0]})

Here in this callback function, we yield a new task `MovieItem`, which will execute and collect all information from the page.

We also pass a dictionary to `extra`. During initialing, item's content will be updated from `extra` at first.

Start Crawling
**************

To start crawling, simply write::

    if __name__ == "__main__":
        IMDBCrawler().run()

Here is one of the items::

    {'date': '26 April 2019 (USA)',
    'director': ['Anthony Russo', 'Joe Russo'],
    'genres': ['Action', 'Adventure', 'Sci-Fi'],
    'metascore': '78',
    'rating': '8.8',
    'rating_count': '407,691',
    'stars': ['Robert Downey Jr.', 'Chris Evans', 'Mark Ruffalo'],
    'time': 181,
    'title': 'Avengers: Endgame',
    'url': 'https://www.imdb.com/title/tt4154796/',
    'writers': ['Christopher Markus', 'Stephen McFeely']}

Register a Handler
******************

We can define a dummy handler to send a warning if the movie is a horror movie::

    @register()
    class HorrorHandler(Handler):
        family = 'MovieItem'
        logger = get_logger('horrorlogger')

        async def handle_after(self, item):
            if item['genres'] and 'Horror' in item['genres']:
                self.logger.warning(
                    "({}) is a horror movie!!!!".format(item['title']))


In this case, handler is register to `MovieItem` with a specific family provided::

    2019-05-24 18:37:22,888 acrawler.horrorlogger WARNING  (Midsommar) is a horror movie!!!!


Periodical & Persistent
***********************

If we want the crawler supports keyboard interupt(Ctrl-C) and resumes crawling next time, the config `PERSISTENT` should be set.

If we want to recrawl the index page every 4 hour starting from a specific time, we can provide ``recrawl`` and ``exetime`` parameters::

    import time
    class IMDBCrawler(Crawler):
        config = {
            'MAX_REQUESTS': 6,
            'PERSISTENT': True,
            'PERSISTENT_NAME': 'IMDBv0.1'
        }

        async def start_requests(self):
            yield Request('https://www.imdb.com/chart/moviemeter', 
                          exetime=time.mktime((2019,5,24,18,30,0,0,0,0)), 
                          recrawl=4*60*60)

