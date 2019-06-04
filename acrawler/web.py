from aiohttp import web
from acrawler.crawler import Crawler
from acrawler.http import Request
from acrawler.utils import get_logger
import asyncio
import json
import time

logger = get_logger(__name__)


async def runweb(crawler: Crawler = None):
    routes = web.RouteTableDef()

    @routes.get('/')
    async def hello(request):
        return web.Response(text="Hello, this is {}".format(crawler.__class__.__name__))

    @routes.get('/add_task')
    async def add_task(request):
        try:
            query = request.query.copy()
            ancestor = '@web' + str(time.time())
            async for task in crawler.web_add_task_query(query):
                await crawler.add_task(task, dont_filter=True, ancestor=ancestor)

            await crawler.counter.join_by_ancestor_unfinished(ancestor)

            items = crawler.web_items.pop(ancestor, [])
            if items:
                res = {'error': None}
                res['items'] = items
                return web.json_response(res)
            else:
                raise Exception('Items not found!')

        except Exception as e:
            logger.error(e)
            res = {'error': str(e)}
            return web.json_response(res, status=400)

    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    host = crawler.config.get('WEB_HOST', 'localhost')
    port = crawler.config.get('WEB_PORT', 8079)
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner
