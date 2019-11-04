import re
from datetime import datetime, date

from acrawler.exceptions import DropFieldError, SkipTaskImmediatelyError


class Processors(object):
    """ Processors are used to spawn field processing functions for ParselItem.
    All the methods are static.
    """

    functions = {}

    @classmethod
    def register(cls):
        def decorator(target):
            cls.functions[target.__name__] = target
            return target

        return decorator

    @classmethod
    def use(cls, func_dict):
        cls.functions.update(func_dict)

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
        """If func return false, drop the Field."""

        def _f(value):
            if not func(value):
                raise DropFieldError
            else:
                return value

        return _f

    @staticmethod
    def drop_item(func=bool):
        """If func return false, drop the Item."""

        def _f(value):
            if not func(value):
                raise SkipTaskImmediatelyError
            else:
                return value

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
    def re_groups(regex, default=None):
        def _f(value):
            match = re.search(regex, value)
            if match:
                return match.groups(default)
            return None

        return _f

    @staticmethod
    def re_groupdict(regex, default=None):
        def _f(value):
            match = re.search(regex, value)
            if match:
                return match.groupdict(default)
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

    @staticmethod
    def replace(old, new, count=-1):
        def _f(value):
            return value.replace(old, new, count)

        return _f

    @staticmethod
    def to_datetime(error_drop=False, error_keep=False, with_time=False, regex=None):
        """extract datetime, return None if not matched

        :param error_drop: drop the field if not matched, defaults to False
        :type error_drop: bool, optional
        :param error_keep: keep the original value if not matched, defaults to False
        :type error_keep: bool, optional
        :param with_time: regex with time parsing, defaults to False
        :type with_time: bool, optional
        :param regex: provided custom regex, defaults to None
        :type regex: str, optional
        """
        if not regex:
            if with_time:
                regex = r".*(\d\d\d\d)\D+(0?[1-9]|1[0-2])\D+(0?[1-9]|[12][0-9]|3[01])\D+(00|[0-9]|1[0-9]|2[0-3]):([0-9]|[0-5][0-9]):([0-9]|[0-5][0-9]).*"
            else:
                regex = r".*(\d\d\d\d)\D+(0?[1-9]|1[0-2])\D+(0?[1-9]|[12][0-9]|3[01]).*"

        pattern = re.compile(regex)

        def _f(value):
            match = pattern.match(value or "")
            if match:
                return datetime(*map(int, match.groups()))
            else:
                if error_drop:
                    raise DropFieldError
                elif error_keep:
                    return value
                else:
                    return None

        return _f

    @staticmethod
    def to_date(error_drop=False, error_keep=False, regex=None):
        """extract date, return None if not matched

        :param error_drop: drop the field if not matched, defaults to False
        :type error_drop: bool, optional
        :param error_keep: keep the original value if not matched, defaults to False
        :type error_keep: bool, optional
        :param with_time: regex with time parsing, defaults to False
        :type with_time: bool, optional
        :param regex: provided custom regex, defaults to None
        :type regex: str, optional
        """
        if not regex:
            regex = r".*(\d\d\d\d)\D+(0?[1-9]|1[0-2])\D+(0?[1-9]|[12][0-9]|3[01]).*"

        pattern = re.compile(regex)

        def _f(value):
            match = pattern.match(value or "")
            if match:
                return date(*map(int, match.groups()))
            else:
                if error_drop:
                    raise DropFieldError
                elif error_keep:
                    return value
                else:
                    return None

        return _f
