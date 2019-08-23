
aCrawler
========


.. image:: https://img.shields.io/pypi/v/acrawler.svg
   :target: https://pypi.org/project/acrawler/
   :alt: PyPI
.. image:: https://readthedocs.org/projects/acrawler/badge/?version=latest
    :target: https://acrawler.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

🔍 A powerful web-crawling framework, based on aiohttp.



Feature
-------


* Write your crawler in one Python script with asyncio
* Schedule task with priority, fingerprint, exetime, recrawl...
* Middleware: add handlers before or after task's execution
* Simple shortcuts to speed up scripting
* Parse html conveniently with `Parsel <https://parsel.readthedocs.io/en/latest/>`_
* Parse with rules and chained processors
* Support JavaScript/browser-automation with `pyppeteer <https://github.com/miyakogi/pyppeteer>`_
* Stop and Resume: crawl periodically and persistently
* Distributed work support with Redis

Installation
------------

To install, simply use `pipenv <http://pipenv.org/>`_ (or pip):

.. code-block:: bash

   $ pipenv install acrawler

   (Optional)
   $ pipenv install uvloop      #(only Linux/macOS, for faster asyncio event loop)
   $ pipenv install aioredis    #(if you need Redis support)
   $ pipenv install motor       #(if you need MongoDB support)
   $ pipenv install aiofiles    #(if you need FileRequest)

Documentation
-------------
Documentation and tutorial are available online at https://acrawler.readthedocs.io/ and in the ``docs``
directory.

Sample Code
-----------



Scrape imdb.com
^^^^^^^^^^^^^^^

.. code-block:: python

   from acrawler import Crawler, Request, ParselItem, Handler, register, get_logger


   class MovieItem(ParselItem):
      log = True
      css = {
         # just some normal css rules
         # see Parsel for detailed information
         "date": ".subtext a[href*=releaseinfo]::text",
         "time": ".subtext time::text",
         "rating": "span[itemprop=ratingValue]::text",
         "rating_count": "span[itemprop=ratingCount]::text",
         "metascore": ".metacriticScore span::text",

         # if you provide a list with additional functions,
         # they are considered as field processor function
         "title": ["h1::text", str.strip],

         # the following four fules is for getting all matching values
         # the rule starts with [ and ends with ] comparing to normal rules
         "genres": "[.subtext a[href*=genres]::text]",
         "director": "[h4:contains(Director) ~ a[href*=name]::text]",
         "writers": "[h4:contains(Writer) ~ a[href*=name]::text]",
         "stars": "[h4:contains(Star) ~ a[href*=name]::text]",
      }


   class IMDBCrawler(Crawler):
      config = {"MAX_REQUESTS": 4, "DOWNLOAD_DELAY": 1}

      async def start_requests(self):
         yield Request("https://www.imdb.com/chart/moviemeter", callback=self.parse)

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



Scrape quotes.toscrape.com
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Scrape quotes from http://quotes.toscrape.com/
   from acrawler import Parser, Crawler, ParselItem, Request


   logger = get_logger("quotes")


   class QuoteItem(ParselItem):
      log = True
      default = {"type": "quote"}
      css = {"author": "small.author::text"}
      xpath = {"text": ['.//span[@class="text"]/text()', lambda s: s.strip("“")[:20]]}


   class AuthorItem(ParselItem):
      log = True
      default = {"type": "author"}
      css = {"name": "h3.author-title::text", "born": "span.author-born-date::text"}

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


See `examples <examples/>`_.


Todo
----

* Add delta_key support for request
* Cralwer's name for distinguishing
* Command Line config support
* Monitor all crawlers in web
* Write detailed Documentation
* Write testing code
