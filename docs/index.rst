.. aCrawler documentation master file, created by
   sphinx-quickstart on Tue May 21 14:24:47 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

================================
aCrawler documentation
================================




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



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   source/tutorial
   source/concept
   source/api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
