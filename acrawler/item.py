import logging
from collections import MutableMapping
from typing import AsyncGenerator, Callable

from parselx import SelectorX

from acrawler.exceptions import DropFieldError, SkipTaskImmediatelyError
from acrawler.task import Task
from acrawler.utils import to_asyncgen, partial
from acrawler.processors import Processors

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

    def __init__(
        self,
        extra: dict = None,
        extra_from_meta=False,
        log=None,
        store=None,
        family=None,
        **kwargs,
    ):
        dont_filter = kwargs.pop("dont_filter", True)
        ignore_exception = kwargs.pop("ignore_exception", True)
        super().__init__(
            dont_filter=dont_filter,
            ignore_exception=ignore_exception,
            family=family,
            **kwargs,
        )
        self.extra = extra or {}
        if extra_from_meta:
            self.extra.update(self.meta)

        # Item stores information in the `content`, which is a dictionary.
        self.content: dict = {}
        self.content.update(self.extra)

        self.log = log or self.log
        self.store = store or self.store

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
            logger.info(f"{self.content}")

    async def _process(self):
        async for task in to_asyncgen(self.custom_process):
            yield task

    def custom_process(self):
        """can be rewritten for customed futhur processing of the item.
        """

    def __getstate__(self):
        state = super().__getstate__()
        sel = state.pop("sel", None)
        if sel:
            state["__sel_text"] = sel.get()
        return state

    def __setstate__(self, state):
        sel_text = state.pop("__sel_text", None)
        if sel_text:
            sel = SelectorX(sel_text)
        else:
            sel = None
        super().__setstate__(state)
        self.__dict__["sel"] = sel

    def __str__(self):
        return str(self.content)


class DefaultItem(Item):
    """Any python dictionary yielded from a task's execution will be cathed as :class:`DefaultItem`.

    It's the same as :class:`Item`. But its families has one more member 'DefaultItem'.
    """


class ParselXItem(Item):
    """The Item work with parselx library."""

    rule = {}

    def __init__(
        self,
        sel: "SelectorX" = None,
        rule=None,
        text=None,
        family=None,
        extra=None,
        extra_from_meta=False,
        log=None,
        store=None,
        **kwargs,
    ):
        super().__init__(
            extra=extra,
            extra_from_meta=extra_from_meta,
            log=log,
            store=store,
            family=family,
            **kwargs,
        )
        self.sel = sel
        self.rule = rule or self.rule

    async def _execute(self, **kwargs) -> _TaskGenerator:
        if self.sel:
            await self._load()
            async for task in super()._execute(**kwargs):
                yield task

    async def _load(self):
        result = self.sel.g(self.rule)
        if isinstance(result, dict):
            self.content.update(result)
        else:
            self.content.update({"item": result})
        return self.content

    async def load(self):
        return self._load()



class ParselItem(Item):
    """The item working with Parsel.

    The item receives Parsel's selector and several rules.
    The selector will process item's fields with these rules.
    Finally, it will call processors to process each field.

    """

    default = {}
    css = {}
    xpath = {}
    re = {}
    inline = {}

    inline_divider = None

    _bindmap = {}

    def __init__(
        self,
        selector=None,
        extra=None,
        css=None,
        xpath=None,
        re=None,
        default=None,
        inline=None,
        inline_divider=None,
        bindmap=None,
        **kwargs,
    ):
        super().__init__(extra=extra, **kwargs)
        self.css = css or self.css
        self.xpath = xpath or self.xpath
        self.re = re or self.re
        self.inline = inline or self.inline
        self.inline_divider = inline_divider or self.inline_divider

        self.sel = selector
        self.default_rules = default or self.default

        self.css_rules_first = {}
        self.xpath_rules_first = {}
        self.re_rules_first = {}

        self.css_rules = {}
        self.xpath_rules = {}
        self.re_rules = {}
        self.field_processors = {}

    async def _execute(self, **kwargs) -> _TaskGenerator:
        if self.sel:
            await self._load()
            async for task in super()._execute(**kwargs):
                yield task
        yield None

    async def load(self):
        # this method can be called without going through scheduler
        return [task async for task in self._execute()]

    async def _parse_rules(self):
        for field, rule_ in self.css.items():
            if isinstance(rule_, str):
                rule = rule_
            elif isinstance(rule_, list):
                rule = rule_[0]
                li = self.field_processors.setdefault(field, [])
                li.extend(rule_[1:])
            if rule[0] == "[" and rule[-1] == "]":
                self.css_rules[field] = rule[1:-1]
            else:
                self.css_rules_first[field] = rule

        for field, rule_ in self.xpath.items():
            if isinstance(rule_, str):
                rule = rule_
            elif isinstance(rule_, list):
                rule = rule_[0]
                li = self.field_processors.setdefault(field, [])
                li.extend(rule_[1:])
            if rule[0] == "[" and rule[-1] == "]":
                self.xpath_rules[field] = rule[1:-1]
            else:
                self.xpath_rules_first[field] = rule

        for field, rule_ in self.re.items():
            if isinstance(rule_, str):
                rule = rule_
            elif isinstance(rule_, list):
                rule = rule_[0]
                li = self.field_processors.setdefault(field, [])
                li.extend(rule_[1:])
            if rule[0] == "[" and rule[-1] == "]":
                self.re_rules[field] = rule[1:-1]
            else:
                self.re_rules_first[field] = rule

        self.field_processors.update(self._bindmap)

    async def _parse_inline(self):
        for field, rule_ in self.inline.items():

            if isinstance(rule_, list):
                rule = rule_[0]
                li = self.field_processors.setdefault(field, [])
                li.extend(rule_[1:])
            else:
                rule = rule_

            if not issubclass(rule, ParselItem):
                raise Exception(f"inline rule must use ParselItem type! :{rule}")

            css_div = rule.inline_divider
            if css_div:
                value = []
                for sel in self.sel.css(css_div):
                    item = rule(sel)
                    await item.load()
                    value.append(item.content)
            else:
                item = rule(self.sel)
                await item.load()
                value = item.content
            self[field] = value

    async def _load(self):
        # Main function to return an item.
        await self._parse_rules()
        await self._parse_inline()
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


        self.process(item)
        return self.content

    def process(self, item):
        # Call field processors.
        for field, processors in self.field_processors.items():
            for processor in processors:
                if isinstance(processor, str):
                    li = processor.split(":", 1)
                    func_name = li[0]
                    args = li[1].split(",") if len(li) == 2 else []

                    processor = partial(
                        Processors.functions[func_name], *args, new_args_before=True
                    )

                self._on_field(field, processor)

    def _on_field(self, field, processor=lambda x: x, dest_field: str = None):
        try:
            dest_field = dest_field or field
            val = processor(self[field])
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

            if "_bindmap" not in cls.__dict__:
                cls._bindmap = {}
            lis = cls._bindmap.setdefault(field, [])
            if not isinstance(lis, list):
                lis = [lis]
            if map:
                lis.append(Processors.map(func))
            else:
                lis.append(func)
            return func

        return decorator
