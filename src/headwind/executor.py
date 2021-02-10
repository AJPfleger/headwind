import contextlib
from concurrent.futures.thread import ThreadPoolExecutor
from threading import Lock
from concurrent.futures import Future, Executor


class SerialExecutor(Executor):
    def __init__(self) -> None:
        self._shutdown = False
        self._shutdownLock = Lock()

    def submit(self, fn, *args, **kwargs):

        with self._shutdownLock:
            if self._shutdown:
                raise RuntimeError("Executor is shut down")

        f = Future()

        try:
            result = fn(*args, **kwargs)
            f.set_result(result)
        except BaseException as e:
            f.set_exception(e)

        return f

    def shutdown(self, *args, **kwargs):
        with self._shutdownLock:
            self._shutdown = True


@contextlib.contextmanager
def make_executor(jobs: int):
    if jobs > 1:
        with ThreadPoolExecutor() as te:
            yield te
    else:
        with SerialExecutor() as se:
            yield se
