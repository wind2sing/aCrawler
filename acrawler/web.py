import time
from inspect import iscoroutinefunction

from aiohttp import web

from acrawler.crawler import Crawler
from acrawler.utils import get_logger

logger = get_logger(__name__)


class Routes(web.RouteTableDef):
    def __init__(self):
        super().__init__()
        self.crawler: Crawler = None


routes = Routes()
app = web.Application()


async def runweb(crawler: Crawler = None):
    routes.crawler = crawler

    @routes.get("/")
    async def hello(request):
        return web.Response(text="Hello, this is {}".format(crawler.name))

    @routes.get("/add")
    async def add_task(request):
        try:
            query = request.query.copy()
            logger.info(request.rel_url)
            items = await crawler.add_then_wait(*crawler.web_add_task_query(query))
            if items:
                res = {"error": None}
                res["content"] = crawler.web_action_after_query(items)
                return web.json_response(res)
            else:
                raise Exception("Not found")

        except Exception as e:
            logger.error(e)
            res = {"error": str(e)}
            return web.json_response(res, status=400)

    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    host = crawler.config.get("WEB_HOST", "localhost")
    port = crawler.config.get("WEB_PORT", 8079)
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Web server start on http://{host}:{port}")
    return runner
