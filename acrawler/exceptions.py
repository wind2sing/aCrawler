class SkipTaskError(Exception):
    """Prevent the task from execution and skip it (considered as a success).

    If this exception is raised, execution/handling stops but posterior Handlers will
    continue to handle the task.

    """

    pass


class SkipTaskImmediatelyError(SkipTaskError):
    """Prevent the task from execution and skip it (considered as a success).

    If this exception is raised, execution/handling stops and posterior Handlers won't 
    continue to handle the task.

    """

    pass


class ReScheduleError(Exception):
    """Prevent the task from execution and reschedult it (add it back to scheduler).

    If this exception is raised, execution/handling stops but posterior Handlers will
    continue to handle the task.
    """

    def __init__(self, defer: int = 0, recrawl: int = None):
        self.defer = defer
        self.recrawl = recrawl
        super().__init__(defer, recrawl)


class ReScheduleImmediatelyError(ReScheduleError):
    """Prevent the task from execution and reschedult it (add it back to scheduler).

    If this exception is raised, execution/handling stops and posterior Handlers won't 
    continue to handle the task.
    """

    pass


class ResponseStatusError(Exception):
    """ Indicate that the Request failed with incorrect Response's status.
    """

    def __init__(self, status: int):
        self.status = status
        super().__init__(status)

    def __str__(self):
        return f"<{self.status}>"


class DropFieldError(Exception):
    pass

