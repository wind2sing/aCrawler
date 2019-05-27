
class SkipTaskError(Exception):
    """Prevent the task from execution and skip it (considered as a success).
    """
    pass


