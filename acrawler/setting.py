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
    'acrawler.handlers.ResponseCheckStatus':800,
    'acrawler.handlers.CrawlerStartAddon': 1000,
}

DOWNLOAD_DELAY = 0

LOG_LEVEL = 'INFO'

STATUS_ALLOWED = None


REDIS_ENABLE = False
REDIS_START_KEY = 'acrawler:start_urls'
REDIS_QUEUE_KEY = 'acrawler:queue'
REDIS_DF_KEY = 'acrawler:df'
REDIS_ADDRESS = 'redis://localhost'

PERSISTENT = False
PERSISTENT_NAME = None
