import functools
from datetime import datetime, date


def measure_time(foo):
    """Decorator for time measuring"""
    @functools.wraps(foo)
    def wrapper(*args, **kwargs):
        start_time = datetime.now().time()
        foo(*args, **kwargs)
        finish_time = datetime.now().time()
        diff = datetime.combine(date.min, finish_time) - datetime.combine(date.min, start_time)
        print("|{}| time: {}".format(foo.__name__, diff))
    return wrapper