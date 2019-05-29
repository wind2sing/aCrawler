""" There are default settings for aCrawler.

You can providing settings by writing a new `setting.py` in your working directory or writing 
in :class:`~acrawler.crawler.Crawler`'s attributes.
"""
REQUEST_CONFIG = {
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    },
}


MIDDLEWARE_CONFIG = {
    'acrawler.handlers.RequestPrepareSession': 900,
    'acrawler.handlers.RequestMergeConfig': 800,
    'acrawler.handlers.RequestDelay': 700,
    'acrawler.handlers.ResponseAddCallback': 900,
    'acrawler.handlers.ResponseCheckStatus': 800,
    'acrawler.handlers.CrawlerStartAddon': 1000,
}


DOWNLOAD_DELAY = 0
"""Every Request worker will delay some seconds before sending a new Request"""

LOG_LEVEL = 'INFO'
"""Default log level."""

STATUS_ALLOWED = None
"""A list of intergers representing status codes other than 200."""

MAX_TRIES: int = 3
"""A task will try to execute for `max_tries` times before a complete fail."""

MAX_REQUESTS: int = 4
"""A crawler will obtain `MAX_REQUESTS` request concurrently."""

MAX_REQUESTS_PER_HOST: dict = {}
"""Limit simultaneous connections to the same endpoint(host, port, is_ssl)."""

REDIS_ENABLE = False
"""Set to True if you want distributed crawling support."""

REDIS_START_KEY = 'acrawler:start_urls'
""""""

REDIS_QUEUE_KEY = 'acrawler:queue'
""""""

REDIS_DF_KEY = 'acrawler:df'
""""""

REDIS_ADDRESS = 'redis://localhost'
""""""

PERSISTENT = False
"""Set to True if you want stop-resume support. If you enable distributed support, this conf will be ignored."""

PERSISTENT_NAME = None
"""A name tag for file-storage of persistent support"""
