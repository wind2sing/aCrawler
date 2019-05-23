
aCrawler
========


.. image:: https://img.shields.io/pypi/v/acrawler.svg
   :target: https://pypi.org/project/acrawler/
   :alt: PyPI
.. image:: https://readthedocs.org/projects/acrawler/badge/?version=latest
    :target: https://acrawler.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

🔍 A simple web-crawling framework, based on aiohttp.

This project is at *very early* stage and may face breaking changes in the future.

Feature
-------


* Write your crawler in one Python script with asyncio
* Schedule task with priority, fingerprint, exetime, recrawl...
* Middleware: add handlers before or after tasks
* Simple shortcuts to speed up scripting
* Parse html conveniently with Parsel
* Stop and Resume: crawl periodically and persistently
* Distributed work support with Redis

Installation
------------

To install, simply use `pipenv <http://pipenv.org/>`_ (or pip):

.. code-block:: bash

   $ pipenv install acrawler

   (Optional)
   $ pipenv install uvloop (only Linux/macOS)
   $ pipenv install aioredis (if you need Redis support)
   $ pipenv install motor (if you need MongoDB support)

QuickStart
----------

Your first script
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from acrawler import Crawler, Request, callback, register

   class V2EXCrawler(Crawler):

       def start_requests(self):
           yield Request('https://www.v2ex.com/?tab=hot',
                         family='v2ex',  # Optional
                         callback=None,  # Optional
                         )

       def parse(self, response):
           print('This is default callback function! Auto combined to any request yield from start_requests().')

       @callback('v2ex')
       def parse_hot(self, response):
           aa = response.sel.css('.item_title a')
           for a in aa:
               d = {
                   'url': response.urljoin(a).split('#')[0],
                   'title': a.css('::text').get()
               }
               yield d


   @register('DefaultItem')
   def process_d(d):
       print(d.content)


   if __name__ == "__main__":
       V2EXCrawler().run()


* 
  ``start_requests()`` is the entry point. Default implementaion will yield ``Request`` form Crawler's ``start_urls`` List.

* 
  Any ``Request`` yielded from ``start_requests()`` will combine ``crawler.parse()`` to its callbacks and passes all callbacks to ``Response``

* 
  ``Response`` executes by calling its callbacks. Callback funtion should accepts one argument ``response``. ``response.sel`` is a ``Selector``. See `Parsel <https://parsel.readthedocs.io/en/latest/>`_ for parsing rules.


Sample code
-----------

.. code-block:: python

   # Scrape quotes from http://quotes.toscrape.com/
   from acrawler import Parser, Crawler, Processors, ParselItem, get_logger, Request

   logger = get_logger('quotes')


   def get_twenty_words(value):
       return value[:20]


   class QuoteItem(ParselItem):
       log = True
       default_rules = {'type': 'quote'}
       css_rules_first = {'author': 'small.author::text'}
       xpath_rules_first = {'text': './/span[@class="text"]/text()'}

       field_processors = {
           'text': get_twenty_words,
       }


   class AuthorItem(ParselItem):
       css_rules_first = {'name': 'h3.author-title::text',
                          'born': 'span.author-born-date::text',
                          }
       field_processors = {
           'name': [Processors.strip,],
       }


   class QuoteCrawler(Crawler):
       config = {}

       start_urls = ['http://quotes.toscrape.com/page/1/', ]

       main_page = r'quotes.toscrape.com/page/\d+'
       author_page = r'quotes.toscrape.com/author/.*'
       parsers = [Parser(in_pattern=main_page,
                         follow_patterns=[main_page, author_page],
                         item_type=QuoteItem,
                         css_divider='.quote'
                         ),
                  Parser(in_pattern=author_page, item_type=AuthorItem)
                  ]


   if __name__ == '__main__':
       QuoteCrawler().run()

See `examples <examples/>`_.

Todo
----


* Support JavaScript with pyppeteer
* Absolute links support
* Better logging
* Monitor all your crawlers
* Documentation
