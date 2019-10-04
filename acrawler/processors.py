import re
from datetime import datetime

from acrawler.exceptions import DropFieldError


class Processors(object):
    """ Processors are used to spawn field processing functions for ParselItem.
    All the methods are static.
    """

    @staticmethod
    def first():
        """ get the first element from the values
        """

        def _f(values):
            if isinstance(values, list) and values:
                return values[0]
            else:
                return values

        return _f

    @staticmethod
    def strip():
        """ strip every string in values
        """

        def _f(value):
            if isinstance(value, list):
                return [_f(v) for v in value]
            elif isinstance(value, dict):
                return {k: _f(v) for k, v in value.items()}
            elif isinstance(value, str):
                return str.strip(value)
            else:
                return value

        return _f

    @staticmethod
    def map(func):
        """ apply function to every item of filed's values list
        """

        def _f(values):
            return [func(v) for v in values]

        return _f

    @staticmethod
    def filter(func=bool):
        """ pick from those elements of the values list for which function returns true
        """

        def _f(values):
            return [v for v in values if func(v)]

        return _f

    @staticmethod
    def drop(func=bool):
        def _f(values):
            if func(values):
                raise DropFieldError

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
    def default(default, fn=bool):
        def _f(value):
            if bool(value):
                return value
            else:
                return default

        return _f

    @staticmethod
    def try_(*fns):
        def _f(value):
            for fn in fns:
                try:
                    return fn(value)
                except Exception:
                    pass

        return _f

