from .task import Task
from ..utils import to_asyncgen


class Response(Task):
    """Response is a Task that execute parse function.

    Attributes:
        status: HTTP status code of response, e.g. 200.
        url: url as yarl URL
        url_str: url as str
        sel: a ``Selector``. See `Parsel <https://parsel.readthedocs.io/en/latest/>`_ for parsing rules.
        doc: a ``PyQuery`` object.
        meta: a dictionary to deliver information. It comes from :attr:`Request.meta`.
        ok: True if `status==200` or status is allowed from :attr:`Request.status_allowed`
        cookies: HTTP cookies of response (Set-Cookie HTTP header).
        headers: A case-insensitive multidict proxy with HTTP headers of response.
        history: Preceding requests (earliest request first) if there were redirects.
        body: The whole response’s body as `bytes`.
        text: Read response’s body and return decoded `str`
        request: Point to the corresponding request object that generates this response.
        callbacks: list of callback functions
    """

    def __init__(
        self,
        url: "URL",
        status: int,
        cookies: "http.cookies.SimpleCookie",
        headers: "CIMultiDict",
        request: "Request",
        body: bytes,
        encoding: str,
        links_to_abs: bool = False,
        callbacks=None,
        meta: dict = None,
        **kwargs,
    ):
        dont_filter = kwargs.pop("dont_filter", True)
        ignore_exception = kwargs.pop("ignore_exception", True)
        super().__init__(
            dont_filter=dont_filter, ignore_exception=ignore_exception, **kwargs
        )
        self.url = url
        self.status = status
        self.cookies = cookies
        self.headers = headers

        self.body = body
        self.encoding = encoding
        self.links_to_abs = links_to_abs
        self.meta = meta
        self.request = request
        self.callbacks = callbacks
        self.bind_cbs = False

        self._text_raw = None
        self._text_absolute = None
        self._json = None
        self._sel: Selector = None
        self._pq = None

    @property
    def url_str(self):
        return self.url.human_repr()

    @property
    def ok(self) -> bool:
        """ If the response is allowed by the config of request.
        """
        return (
            (self.status == 200)
            or (self.request.status_allowed == [])
            or (
                (self.request.status_allowed)
                and (self.status in self.request.status_allowed)
            )
        )

    async def _execute(self, **kwargs):
        """Calls every callback function to yield new task."""
        if self.ok:
            for callback in self.callbacks:
                async for task in to_asyncgen(callback, self):
                    yield task
        else:
            yield None

    def __str__(self):
        return f"<Task Response> <{self.status}> ({self.url_str})"
