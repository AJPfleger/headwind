import contextlib
import sys
from concurrent.futures import Future, Executor
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Lock
from typing import Callable, Any, Iterator, TypeVar

_T = TypeVar("_T")


class SerialExecutor(Executor):
    def __init__(self) -> None:
        self._shutdown = False
        self._shutdownLock = Lock()

    # This is GARBAGE
    if sys.version_info >= (3, 9):
        def submit(self, __fn: Callable[..., _T], *args: Any, **kwargs: Any) -> Future[_T]:
            return self._submit(__fn, *args,
                                **kwargs)
    else:
        def submit(self, fn: Callable[..., _T], *args: Any, **kwargs: Any) -> Future[_T]:
            return self._submit(fn, *args,
                                **kwargs)

    def _submit(self, fn: Callable[..., _T], *args: Any, **kwargs: Any) -> Future[_T]:
        with self._shutdownLock:
            if self._shutdown:
                raise RuntimeError("Executor is shut down")

            f: Future[_T] = Future()

            try:
                result = fn(*args, **kwargs)
                f.set_result(result)
            except BaseException as e:
                f.set_exception(e)

            return f

    def shutdown(self, *args: Any, **kwargs: Any) -> None:
        with self._shutdownLock:
            self._shutdown = True


@contextlib.contextmanager
def make_executor(jobs: int) -> Iterator[Executor]:
    if jobs > 1:
        with ThreadPoolExecutor() as te:
            yield te
    else:
        with SerialExecutor() as se:
            yield se
