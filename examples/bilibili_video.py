from acrawler import Crawler, register
from acrawler.handlers import ItemToMongo
import acrawler


@register()
class MyMongo(ItemToMongo):
    family = "DefaultItem"
    db_name = "bili"
    col_name = "video2"
    primary_key = "aid"


class BiliVideoCrawler(Crawler):
    config = {
        "REDIS_ENABLE": True,
        "REDIS_START_KEY": "bili:vsurls",
        "DOWNLOAD_DELAY": 0,
        "MAX_REQUESTS": 4,
        "MAX_WORKERS": 32,
    }

    async def parse(self, response: acrawler.Response):
        data = response.json
        archives = data["data"]["archives"]
        if archives:
            for info in archives:
                yield info


if __name__ == "__main__":
    BiliVideoCrawler().run()
