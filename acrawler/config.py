class Config:
    def __init__(self):
        self.max_requests = 2
        self.max_workers = 2

        self.max_retries = 2

        #
        self.request_config = {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
            }
        }

        #
        self.plugins_config = {
            "acrawler.plugins.LoggerPlugin": True,
            "acrawler.plugins.RetryPlugin": True,
        }

        # LoggerPlugin
        self.log_enable = True
        self.log_level = "INFO"
        self.log_to_file = False
        self.log_fmt = "%(asctime)s %(name)-20s%(levelname)-8s %(message)s"
        self.log_datefmt = "%y-%m-%d %H:%M:%S"


config = Config()
