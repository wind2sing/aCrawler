import logging
from collections import MutableMapping
from typing import AsyncGenerator, Callable


from parselx import SelectorX

from .task import Task
from ..utils import to_asyncgen, partial, get_logger


_Function = Callable
_TaskGenerator = AsyncGenerator[Task, None]

logger = get_logger("item")


class Item(Task, MutableMapping):
    """Item is a Task that execute :meth:`custom_process` work. Extending from MutableMapping
    so it provide a dictionary interface. Also you can use `Item.content` to directly access content.
    """

    rule: dict = None

    def __init__(
        self,
        sel: SelectorX = None,
        rule: dict = None,
        extra: dict = None,
        priority=0,
        meta=None,
        family=None,
        exetime=0,
        **kwargs,
    ):
        super().__init__(
            priority=priority, meta=meta, family=family, exetime=exetime, **kwargs
        )

        self.sel = sel
        self.rule = rule or self.rule
        self.extra = extra or {}

        #: Item stores information in the `content`, which is a dictionary.
        self.content: dict = {}
        self.content.update(self.extra)

        #: extra: During initialing, :attr:`content` will be updated from extra at first.
        self.extra = extra or {}

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

    async def _execute(self, **kwargs) -> _TaskGenerator:
        async for task in self._process():
            yield task

    async def _process(self):
        if self.rule:
            val = self.sel.g(self.rule)
            if isinstance(val, dict):
                self.update(val)
            else:
                self["val"] = val
        async for task in to_asyncgen(self.process):
            yield task

    def process(self):
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
            sel = Selector(sel_text)
        else:
            sel = None
        super().__setstate__(state)
        self.__dict__["sel"] = sel

    def __str__(self):
        return str(self.content)

