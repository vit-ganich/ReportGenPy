import functools
import time


def measure_time(foo):
    """Decorator for time measuring"""
    @functools.wraps(foo)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        foo(*args, **kwargs)
        print("|%s| time: %1.1f sec" % (foo.__name__, time.time() - start_time))
    return wrapper


if __name__ == "main":
    pass