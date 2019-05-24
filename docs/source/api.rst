##############
Main Interface
##############



Crawler
*******

.. autoclass:: acrawler.crawler.Crawler
    :members:



Base Task
*********

.. autoclass:: acrawler.task.Task
    :members:


HTTP Task
*********

.. autoclass:: acrawler.http.Request
    :members:

.. autoclass:: acrawler.http.Response
    :members:

.. autoclass:: acrawler.http.FileRequest
    :members:


Item Task
*********

.. autoclass:: acrawler.item.Item
    :members:


.. autoclass:: acrawler.item.ParselItem
    :members:

.. autoclass:: acrawler.item.DefaultItem
    :members:

.. autoclass:: acrawler.item.Processors
    :members:

Parser
******

.. automodule:: acrawler.parser
    :members:



Handlers
********

.. autoclass:: acrawler.middleware.Handler
    :members:

.. autofunction:: acrawler.middleware.register

.. autofunction:: acrawler.handlers.callback

.. autoclass:: acrawler.middleware._Middleware
    :members:

.. autoclass:: acrawler.handlers.ItemToRedis
    :members:

.. autoclass:: acrawler.handlers.ItemToMongo
    :members:

.. autoclass:: acrawler.handlers.ResponseAddCallback
    :members:

Setting/Config
***************

.. automodule:: acrawler.setting
    :members:


Utils
*****

.. automodule:: acrawler.utils
    :members:

