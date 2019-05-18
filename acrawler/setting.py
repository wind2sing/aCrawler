REQUEST_CONFIG = {
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    },
}


MIDDLEWARE_CONFIG = {
    'acrawler.handlers.RequestPrepareSession': 100,
    'acrawler.handlers.ResponseAddCallback': 100,
    'acrawler.handlers.RequestMergeConfig': 100,
    'acrawler.handlers.RequestDelay': 100,
    'acrawler.handlers.ResponseCheckStatus':100,
    'acrawler.handlers.CrawlerStartAddon': 100,
    'acrawler.handlers.CrawlerFinishAddon': 100
}

DOWNLOAD_DELAY = 0

LOG_LEVEL = 'INFO'

REDIS_ENABLE = False
REDIS_START_KEY = 'acrawler:start_urls'
REDIS_QUEUE_KEY = 'acrawler:queue'
REDIS_DF_KEY = 'acrawler:df'
REDIS_ADDRESS = 'redis://localhost'
