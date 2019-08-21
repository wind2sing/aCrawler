import logging
import re
from datetime import datetime
from collections import MutableMapping
from typing import AsyncGenerator, Callable

from parsel import Selector

from acrawler.exceptions import DropFieldError, SkipTaskImmediatelyError
from acrawler.task import Task
from acrawler.utils import to_asyncgen

_Function = Callable
_TaskGenerator = AsyncGenerator[Task, None]

logger = logging.getLogger(__name__)


class Item(Task, MutableMapping):
    """Item is a Task that execute :meth:`custom_process` work. Extending from MutableMapping
    so it provide a dictionary interface. Also you can use `Item.content` to directly access content.

    Attributes:
        extra: During initialing, :attr:`content` will be updated from extra at first.
        content: Item stores information in the `content`, which is a dictionary.
    """

    log = False
    store = False

    def __init__(self, extra: dict = None, **kwargs):
        dont_filter = kwargs.pop("dont_filter", True)
        ignore_exception = kwargs.pop("ignore_exception", True)
        super().__init__(
            dont_filter=dont_filter, ignore_exception=ignore_exception, **kwargs
        )
        self.extra = extra or {}

        # Item stores information in the `content`, which is a dictionary.
        self.content: dict = {}
        self.content.update(self.extra)

        # self.content.update({'_item_type': self.__class__.__name__})

    def __len__(self):
        return len(self.content)

    def __getitem__(self, key):
        if key in self.content:
            return self.content[key]
        raise KeyError(key)

    def __setitem__(self, key, item):
        self.content[key] = item

    def __delitem__(self, key):
        del self.content[key]

    def __iter__(self):
        return iter(self.content)

    def __contains__(self, key):
        return key in self.content

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    @classmethod
    def drop(cls):
        raise SkipTaskImmediatelyError()

    async def _execute(self, **kwargs) -> _TaskGenerator:
        async for task in self._process():
            yield task
        yield None
        if self.log:
            logger.info(self.content)

    async def _process(self):
        async for task in to_asyncgen(self.custom_process, self.content):
            yield task

    def custom_process(self, content):
        """can be rewritten for customed futhur processing of the item.
        """
        pass

    def __getstate__(self):
        state = super().__getstate__()
        sel = state.pop("sel", None)
        if sel:
            state["__sel_text"] = sel.get()
        return state

    def __setstate__(self, state):
        sel_text = state.pop("__sel_text", None)
        if sel_text:
            sel = Selector(sel_text)
        else:
            sel = None
        super().__setstate__(state)
        self.__dict__["sel"] = sel


class DefaultItem(Item):
    """ Any python dictionary yielded from a task's execution will be cathed as :class:`DefaultItem`.

    It's the same as :class:`Item`. But its families has one more member 'DefaultItem'.
    """


class Processors(object):
    """ Processors are used to process field values for ParselItem
    """

    @staticmethod
    def first(values):
        """ get the first element from the values
        """
        if len(values) > 0:
            return values[0]
        else:
            return None

    @staticmethod
    def strip(value):
        """ strip every string in values
        """
        if isinstance(value, list):
            return [Processors.strip(v) for v in value]
        elif isinstance(value, dict):
            return {k: Processors.strip(v) for k, v in value.items()}
        elif isinstance(value, str):
            return str.strip(value)
        else:
            return value

    @staticmethod
    def drop_false(values):
        if isinstance(values, list):
            return [v for v in values if v]
        return values

    @staticmethod
    def map(func):
        """ apply function to every item of filed's values list
        """

        def _f(values):
            return [func(v) for v in values]

        return _f

    @staticmethod
    def filter(func):
        """ pick from those elements of the values list for which function returns true
        """

        def _f(values):
            return [v for v in values if func(v)]

        return _f

    @staticmethod
    def re(regex, group_index=0):
        def _f(value):
            match = re.search(regex, value)
            if match:
                return match.group(group_index)
            return None

        return _f

    @staticmethod
    def parse_datetime(text, drop_error=True):
        if text:
            match = re.search(r"(?P<year>\d{4}).*(?P<month>\d{2}).*(?P<day>\d{2})日", text)
            if match:
                date = datetime(**{k: int(v) for k, v in match.groupdict().items()})
                return date
        else:
            if drop_error:
                ParselItem.drop_field()
            else:
                return text


class Field:
    def __init__(self, default=None, drop_false=True):
        if callable(default):
            self.value = default()
        else:
            self.value = default
        self._rules = []
        self.drop_false = drop_false

    def css(self, rule: str):
        self._rules.append(("css", rule))
        return self

    def xpath(self, rule: str):
        self._rules.append(("xpath", rule))
        return self

    def re(self, rule: str):
        self._rules.append(("re", rule))
        return self

    def re_first(self, rule: str):
        self._rules.append(("re_first", rule))
        return self

    def get(self):
        self._rules.append(("get", None))
        return self

    def getall(self):
        self._rules.append(("getall", None))
        return self

    def filter(self, func):
        self._rules.append(("filter", func))
        return self

    def map(self, func):
        self._rules.append(("map", func))
        return self

    def process(self, func):
        self._rules.append(("process", func))
        return self

    def drop(self, func=lambda x: not bool(x)):
        self._rules.append(("drop", func))
        return self

    def first(self):
        self._rules.append(("first", None))
        return self

    def parse(self, sel: Selector):
        target = sel
        for rkey, rule in self._rules:
            if rkey == "filter":
                target = [t for t in target if rule(t)]
            elif rkey == "map":
                target = [rule(t) for t in target]
            elif rkey == "process":
                target = rule(target)
            elif rkey == "drop":
                if rule(target):
                    raise DropFieldError
            elif rkey == "first":
                if len(target) > 0:
                    target = target[0]
                else:
                    target = None
            else:
                # call parsel to parse
                if rule is None:
                    v = getattr(target, rkey)()
                else:
                    v = getattr(target, rkey)(rule)
                if self.drop_false and not v:
                    raise DropFieldError
                else:
                    target = v
        self.value = target
        return self.value


class ParselItem(Item):
    """The item working with Parser.

    The item receive Parsel's selector and several rules.
    The selector will process item's fields with these rules.
    Finally, it will call processors to process each field.

    Args:
        selector: Parsel's selector
        default_rules: default value for item field
        field_processors:  functions to process item field after scraping by rules
        css_rules_first: use css selector and get the first result.
        xpath_rules_first: use xpath selector and get the first result.
        re_rules_first: use re selector and get the first result.
        css_rules: use css selector and get a list with all results.
        xpath_rules: use xpath selector and get a list with all results.
        re_rules: use re selector and get a list with all results.

    Examples:
        A simple example to extract title and upper the title::

            class MyItem(ParselItem):
                default_rules = {'spider':'this'}
                css_rules_first = {'title': 'title::text'}
                field_processors = {'title': [str.upper,]}

    """

    default_rules = {}

    css_rules_first = {}
    xpath_rules_first = {}
    re_rules_first = {}

    css_rules = {}
    xpath_rules = {}
    re_rules = {}

    field_processors = {}

    def __init__(
        self,
        selector,
        css_rules=None,
        xpath_rules=None,
        re_rules=None,
        css_rules_first=None,
        xpath_rules_first=None,
        re_rules_first=None,
        default_rules=None,
        field_processors=None,
        extra=None,
        **kwargs,
    ):
        super().__init__(extra=extra, **kwargs)
        self.sel = selector

        if default_rules:
            self.default_rules = default_rules
        if css_rules_first:
            self.css_rules_first = css_rules_first
        if xpath_rules_first:
            self.xpath_rules_first = xpath_rules_first
        if re_rules_first:
            self.re_rules_first = re_rules_first

        if css_rules:
            self.css_rules = css_rules
        if xpath_rules:
            self.xpath_rules = xpath_rules
        if re_rules:
            self.re_rules = re_rules

        if field_processors:
            self.field_processors = field_processors

    async def _execute(self, **kwargs) -> _TaskGenerator:
        self.load()
        async for task in super()._execute(**kwargs):
            yield task
        yield None

    def load(self):
        # Main function to return an item.
        item = self.content
        for field, default in self.default_rules.items():
            if field not in self.extra:
                if callable(default):
                    item.update({field: default()})
                else:
                    item.update({field: default})

        for field, rule in self.css_rules_first.items():
            item.update({field: self.sel.css(rule).get()})

        for field, rule in self.xpath_rules_first.items():
            item.update({field: self.sel.xpath(rule).get()})

        for field, rule in self.re_rules_first.items():
            item.update({field: self.sel.re_first(rule)})

        for field, rule in self.css_rules.items():
            item.update({field: self.sel.css(rule).getall()})

        for field, rule in self.xpath_rules.items():
            item.update({field: self.sel.xpath(rule).getall()})

        for field, rule in self.re_rules.items():
            item.update({field: self.sel.re(rule)})

        for key, field in self.__class__.__dict__.items():
            if isinstance(field, Field):
                self._on_field(field, dest_field=key)

        self.process(item)
        return self.content

    def process(self, item):
        # Call field processors.

        for field, processors in self.field_processors.items():
            if isinstance(processors, list):
                for processor in processors:
                    self._on_field(field, processor)
            else:
                self._on_field(field, processors)

    def _on_field(self, field, processor=lambda x: x, dest_field: str = None):
        try:
            if isinstance(field, str):
                dest_field = dest_field or field
                val = processor(self[field])
            elif isinstance(field, Field):
                val = field.parse(self.sel)
            self[dest_field] = val
        except DropFieldError:
            self.pop(dest_field, None)

    @classmethod
    def drop_field(cls):
        raise DropFieldError()

    @classmethod
    def bind(cls, field: str = None, map=False):
        """ Bind field processor. """

        def decorator(func):
            nonlocal field
            nonlocal map
            if not field:
                func_name = func.__name__
                if func_name.startswith("process_"):
                    field = func_name.replace("process_", "", 1)
                else:
                    field = func_name
            lis = cls.field_processors.setdefault(field, [])
            if not isinstance(lis, list):
                lis = [lis]
            if map:
                lis.append(Processors.map(func))
            else:
                lis.append(func)
            return func

        return decorator
