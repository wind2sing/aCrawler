
class SkipTaskError(Exception):
    """Prevent the task from execution and skip it (considered as a success).
    """
    pass


class ReScheduleError(Exception):
    """Prevent the task from execution and reschedult it (add it back to scheduler).
    """

    def __init__(self, defer: int = 0, recrawl: int = None, *args, **kwargs):
        self.defer = defer
        self.recrawl = recrawl
        super().__init__(*args, **kwargs)
