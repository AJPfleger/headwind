import contextlib
from concurrent.futures import Future, Executor
from typing import Callable, Any, Iterator, TypeVar, TYPE_CHECKING

_T = TypeVar("_T")

class SerialExecutor(Executor):
    def __init__(self) -> None: ...
    def submit(
        self, __fn: Callable[..., _T], *args: Any, **kwargs: Any
    ) -> Future[_T]: ...

@contextlib.contextmanager
def make_executor(jobs: int) -> Iterator[Executor]: ...
