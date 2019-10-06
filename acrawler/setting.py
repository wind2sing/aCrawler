""" There are default settings for aCrawler.

You can providing settings by writing a new `setting.py` in your working directory or writing 
in :class:`~acrawler.crawler.Crawler`'s attributes.
"""
REQUEST_CONFIG = {
    "headers": {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
    }
}


MIDDLEWARE_CONFIG = {
    "acrawler.handlers.RequestPrepareSession": 1800,
    "acrawler.handlers.RequestMergeConfig": 1700,
    "acrawler.handlers.ResponseAddCallback": 1900,
    "acrawler.handlers.ResponseCheckStatus": 1800,
    "acrawler.handlers.CrawlerStartAddon": 2000,
    "acrawler.handlers.ItemCollector": 1700,
}


DOWNLOAD_DELAY = 0
"""Every Request worker will delay some seconds before sending a new Request"""

DOWNLOAD_DELAY_SPECIAL_HOST: dict = {}
"""Every Request worker for specific host will delay some seconds before sending a new Request"""

DISABLE_COOKIES = False

LOG_LEVEL = "INFO"
"""Default log level."""

LOG_TO_FILE: str = None
"""redirect log to a filepath"""

LOG_TIME_DELTA: int = 60
"""how many seconds to log a new crawling statistics. 0: disabled"""

STATUS_ALLOWED = None
"""A list of intergers representing status codes other than 200."""

MAX_TRIES: int = 3
"""A task will try to execute for `max_tries` times before a complete fail."""

MAX_REQUESTS: int = 4
"""A crawler will obtain `MAX_REQUESTS` request concurrently."""

MAX_REQUESTS_PER_HOST: int = 0
"""Limit simultaneous connections to the same host."""

MAX_REQUESTS_SPECIAL_HOST: dict = {}
"""Limit simultaneous connections with a host-limit dictionary."""

REDIS_ENABLE = False
"""Set to True if you want distributed crawling support.
If it is True, the crawler will obtain `crawler.redis` and lock itself always.
"""

REDIS_START_KEY = None
"""And the crawler will try to get url from redis list `REDIS_START_KEY` if 
it is not None and send Request(also bind `crawler.parse` as 
its callback function)"""

REDIS_QUEUE_KEY = None
""""""

REDIS_DF_KEY = None
""""""

REDIS_ADDRESS = "redis://localhost"
""""""

WEB_ENABLE = False
"""Set to True if you want web service support.
If it is True, the crawler will lock itself always."""

WEB_HOST = "localhost"
"""Host for the web service."""

WEB_PORT = 8079
"""Port for the web service."""

LOCK_ALWAYS = False
"""Set to True if you don't want the crawler exits after finishing tasks."""

PERSISTENT = False
"""Set to True if you want stop-resume support. If you enable distributed support, this conf will be ignored."""

PERSISTENT_NAME = None
"""A name tag for file-storage of persistent support"""
