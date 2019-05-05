import logging
from acrawler.task import Task
from parsel import Selector
from inspect import isfunction, iscoroutinefunction, ismethod, isgeneratorfunction
# Typing
from typing import Union, Optional, Any, AsyncGenerator, Callable, Dict, List
_Function = Callable
_TaskGenerator = AsyncGenerator['Task', None]

logger = logging.getLogger(__name__)


class Item(Task):
    """Item is a Task that execute :meth:`custom_process` work.

    :param extra: During initialing, :attr:`content` will be updated from `extra`.
    """
    logger = logger
    

    def __init__(self, extra: dict = None, **kwargs
                 ):
        dont_filter = kwargs.pop('dont_filter', True)
        super().__init__(
            dont_filter=dont_filter,
            **kwargs
        )
        self.extra = extra or {}

        # Item stores information in the `content`, which is a dictionary.
        self.content: dict = {}
        self.content.update(self.extra)
        # self.content.update({'_item_type': self.__class__.__name__})

    def __getitem__(self, key):
        return self.get(key)

    def get(self, k, d=None):
        return self.content.get(k, d)

    async def _execute(self, **kwargs)->_TaskGenerator:
        for task in self._process():
            yield task
        yield None

    def _process(self):
        if isgeneratorfunction(self.custom_process):
            yield from self.custom_process(self.content)
        elif ismethod(self.custom_process) or isfunction(self.custom_process):
            yield self.custom_process(self.content)

    def custom_process(self, content):
        """can be rewritten for futhur processing of the item.
        """
        pass

    def __str__(self):
        return "<%s> (%s)" % ('Task Item', self.__class__.__name__)


class DebugItem(Item):
    def custom_process(self, item):
        logger.debug(item)


class ParselItem(Item):
    """An item working with Parser.

    A item receive Parsel's selector and several rules.
    The selector will process item's fields with these rules.
    Finally, it will call processors to process each field.


    :param css_rule:
    :param xpath_rule:
    :param re_rule:
    """
    css_rule = {}
    xpath_rule = {}
    re_rule = {}
    default_rule = {}

    divide_sel = ''
    field_processors = {}

    def __init__(self, selector,
                 css_rule=None,
                 xpath_rule=None,
                 re_rule=None,
                 default_rule=None,
                 field_processors=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.sel = selector
        if css_rule:
            self.css_rule = css_rule
        if xpath_rule:
            self.xpath_rule = xpath_rule
        if re_rule:
            self.re_rule = re_rule
        if field_processors:
            self.field_processors = field_processors

    async def _execute(self, **kwargs)->_TaskGenerator:
        self.load()
        async for task in super()._execute(**kwargs):
            yield task
        yield None

    def load(self):
        """Main function to return an item."""
        item = {}
        for field, default in self.default_rule.items():
            item.update({field: default})

        for field, rule in self.xpath_rule.items():
            item.update({field: self.sel.xpath(rule).getall()})

        for field, rule in self.css_rule.items():
            item.update({field: self.sel.css(rule).getall()})

        for field, rule in self.re_rule.items():
            item.update({field: self.sel.re(rule)})
        self.content.update(self.process(item))
        return self.content

    def process(self, item):
        """Call field processors."""
        for field, processors in self.field_processors.items():
            if isinstance(processors, list):
                for processor in processors:
                    item[field] = processor(item[field])
            else:
                item[field] = processors(item[field])

        return item


class Processors(object):

    @staticmethod
    def get_first(values):
        if values:
            return values[0]
        else:
            return None

    @staticmethod
    def strip(value):
        if isinstance(value,list):
            value = [str.strip(v) for v in value]
        elif value:
            value = str.strip(value)
        return value
    


class TitleItem(ParselItem):
    css_rule = {'title': 'title::text'}
    field_processors = {'title': Processors.get_first}

    def custom_process(self, content):
        content.update({'info': 'this is TitleItem'})
