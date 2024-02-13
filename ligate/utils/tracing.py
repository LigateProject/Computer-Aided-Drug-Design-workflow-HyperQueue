import contextlib
import functools
import logging
import time
from typing import Optional


ACTIVE_TRACES = []


def format_traces() -> str:
    return " > ".join([f"[{trace}]" for trace in ACTIVE_TRACES])


@contextlib.contextmanager
def trace(name: str, level=logging.DEBUG):
    ACTIVE_TRACES.append(name)
    key = format_traces()

    start = time.time()
    logging.log(level, f"{key}: starting")

    try:
        yield
        duration = time.time() - start
        logging.log(level, f"{key}: finished in {duration:.3f}s")
    except:
        duration = time.time() - start
        logging.error(f"{key}: failed in {duration:.3f}s")
        raise
    finally:
        ACTIVE_TRACES.pop()


def trace_fn(name: Optional[str] = None, level=logging.DEBUG):
    def wrapper(f):
        @functools.wraps(f)
        def fn(*args, **kwargs):
            trace_name = name or f.__name__
            with trace(name=trace_name, level=level):
                return f(*args, **kwargs)

        return fn

    return wrapper
