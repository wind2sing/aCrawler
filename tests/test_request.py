from acrawler.http import Request
import asyncio
import pytest
import json
from aiohttp import ClientSession


def test_fp():
    rq = Request('www.google.com')
    assert rq.fingerprint == 'd8b99f68b208b5453b391cb0c6c3d6a9824f3c3a'


def test_same_fp():
    rq1 = Request('www.google.com')
    rq2 = Request('www.google.com')
    assert rq1.fingerprint == rq2.fingerprint


def test_diff_fp():
    rq1 = Request('www.google.com')
    rq2 = Request('www.youtube.com')
    assert rq1.fingerprint != rq2.fingerprint

@pytest.mark.asyncio
async def test_fetch():
    s = ClientSession()
    
    rq1 = Request('https://httpbin.org/json', session=s)
    assert json.loads((await rq1.fetch()).text) == {'slideshow': {'author': 'Yours Truly', 'date': 'date of publication', 'slides': [{'title': 'Wake up to WonderWidgets!', 'type': 'all'}, {
        'items': ['Why <em>WonderWidgets</em> are great', 'Who <em>buys</em> WonderWidgets'], 'title': 'Overview', 'type': 'all'}], 'title': 'Sample Slide Show'}}
