
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
* Middleware: add handlers before or after tasks
* Simple shortcuts to speed up scripting
* Parse html conveniently with `Parsel <https://parsel.readthedocs.io/en/latest/>`_
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

Documentation
-------------
Documentation and tutorial are available online at https://acrawler.readthedocs.io/ and in the ``docs``
directory.

Sample Code
-----------

Scrape quotes.toscrape.com
^^^^^^^^^^^^^^^^^^^^^^^^^^

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



Scrape v2ex.com
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


See `examples <examples/>`_.

Todo
----

* Correct default fingerprint function
* Add delta_key support
* Enhance item handlers
* Cralwer's name to distinguish
* Command Line config support
* Enhance Counter for better monitoring
* Promethues monitor as command
* Monitor all your crawlers
* Write detailed Documentation
* Write testing code
