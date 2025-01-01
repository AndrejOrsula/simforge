import contextlib
import os
import sys
from functools import wraps
from typing import Any, Callable, TextIO


class StreamRedirect(contextlib.ContextDecorator):
    def __init__(self, source: TextIO | Any, target: str | TextIO | Any):
        self._target = target
        self._source_fd = source.fileno()
        self._dup_source_fd = None
        self._stream = None

    def __enter__(self):
        self._dup_source_fd = os.dup(self._source_fd)
        if isinstance(self._target, str):
            self._stream = open(self._target, "w")
        else:
            self._stream = self._target
        os.dup2(self._stream.fileno(), self._source_fd)

    def __exit__(self, exc_type, exc_value, traceback):
        os.dup2(
            self._dup_source_fd,  # type: ignore
            self._source_fd,
        )
        os.close(
            self._dup_source_fd,  # type: ignore
        )
        if isinstance(self._target, str) and self._stream is not None:
            self._stream.close()


class StdoutSuppress(StreamRedirect):
    def __init__(self):
        super().__init__(source=sys.stdout, target=os.devnull)


class StderrSuppress(StreamRedirect):
    def __init__(self):
        super().__init__(source=sys.stderr, target=os.devnull)


def suppress_stdout(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with StdoutSuppress():
            return fn(*args, **kwargs)

    return wrapper


def suppress_stderr(fn: Callable):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with StderrSuppress():
            return fn(*args, **kwargs)

    return wrapper
