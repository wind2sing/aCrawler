from acrawler.http import Request
import pytest
import pickle


def test_fp():
    rq = Request("https://httpbin.org/cookies/set?name=crawler&age=18")
    assert rq.fingerprint == "7c6accfd1f05cb417373b9f00f3d9b1bd90bbb78"


def test_same_fp():
    rq1 = Request("https://www.google.com")
    rq2 = Request("https://www.google.com")
    assert rq1.fingerprint == rq2.fingerprint

    rq3 = Request("https://httpbin.org/cookies/set?name=crawler&age=18")
    rq4 = Request("https://httpbin.org/cookies/set?age=18&name=crawler")
    rq5 = Request("https://httpbin.org/cookies/set?age=18&name=crawler#fragment")
    assert rq3.fingerprint == rq4.fingerprint
    assert rq3.fingerprint == rq5.fingerprint


def test_diff_fp():
    rq1 = Request("https://www.google.com")
    rq2 = Request("https://httpbin.org/cookies/set?name=crawler&age=18")
    rq3 = Request("https://httpbin.org/cookies/set")
    assert rq1.fingerprint != rq2.fingerprint
    assert rq2.fingerprint != rq3.fingerprint


@pytest.mark.asyncio
async def test_send():

    rq1 = Request("https://httpbin.org/json")
    resp1 = await rq1.send()
    assert resp1.json == {
        "slideshow": {
            "author": "Yours Truly",
            "date": "date of publication",
            "slides": [
                {"title": "Wake up to WonderWidgets!", "type": "all"},
                {
                    "items": [
                        "Why <em>WonderWidgets</em> are great",
                        "Who <em>buys</em> WonderWidgets",
                    ],
                    "title": "Overview",
                    "type": "all",
                },
            ],
            "title": "Sample Slide Show",
        }
    }


@pytest.mark.asyncio
async def test_parse():
    def cb(resp):
        assert resp.status == 200
        return resp.status

    rq1 = Request("https://httpbin.org/json", callback=cb)
    resp = await rq1.send()
    assert await resp.parse()


@pytest.mark.asyncio
async def test_dumps():
    rq1 = Request("https://httpbin.org/json")
    await rq1.send()
    assert pickle.dumps(rq1)

