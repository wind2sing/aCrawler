import logging
import collections
from acrawler.task import Task
from acrawler.utils import to_asyncgen
from parsel import Selector
from inspect import isfunction, iscoroutinefunction, ismethod, isgeneratorfunction

# Typing
from typing import Union, Optional, Any, AsyncGenerator, Callable, Dict, List
_Function = Callable
_TaskGenerator = AsyncGenerator[Task, None]

logger = logging.getLogger(__name__)


class Item(Task, collections.MutableMapping):
    """Item is a Task that execute :meth:`custom_process` work. Extending from MutableMapping 
    so it provide a dictionary interface. Also you can use `Item.content` to directly access content.

    Attributes:
        extra: During initialing, :attr:`content` will be updated from extra at first.
        content: Item stores information in the `content`, which is a dictionary.
    """
    log = False

    def __init__(self, extra: dict = None, **kwargs
                 ):
        dont_filter = kwargs.pop('dont_filter', True)
        ignore_exception = kwargs.pop('ignore_exception', True)
        super().__init__(
            dont_filter=dont_filter,
            ignore_exception=ignore_exception,
            **kwargs
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
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)
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

    def __str__(self):
        return "<%s> (%s)" % ('Task Item', self.__class__.__name__)


class DefaultItem(Item):
    """ Any python dictionary yielded from a task's execution will be cathed as :class:`DefaultItem`.

    It's the same as :class:`Item`. But its families has one more member 'DefaultItem'.
    """


class Processors(object):
    """ Processors are used to process field values for ParselItem
    """

    @staticmethod
    def get_first(values):
        if values:
            return values[0]
        else:
            return None

    @staticmethod
    def strip(value):
        if isinstance(value, list):
            value = [str.strip(v) for v in value]
        elif value:
            value = str.strip(value)
        return value

    @staticmethod
    def drop_false(values):
        return [v for v in values if v]


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

    default_processors = [Processors.strip]
    field_processors = {}

    def __init__(self, selector,
                 css_rules=None,
                 xpath_rules=None,
                 re_rules=None,
                 css_rules_first=None,
                 xpath_rules_first=None,
                 re_rules_first=None,
                 default_rules=None,
                 field_processors=None,
                 extra=None,
                 **kwargs):
        super().__init__(extra=extra, **kwargs)
        self.sel = selector

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
        item = {}
        for field, default in self.default_rules.items():
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

        self.content.update(self.process(item))
        return self.content

    def process(self, item):
        # Call field processors.
        for processor in self.default_processors:
            for field in item.keys():
                item[field] = processor(item[field])

        for field, processors in self.field_processors.items():
            if isinstance(processors, list):
                for processor in processors:
                    item[field] = processor(item[field])
            else:
                item[field] = processors(item[field])

        return item
