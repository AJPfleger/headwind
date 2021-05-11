import subprocess
from concurrent.futures import wait
from typing import List, cast

import pydantic
from headwind.executor import make_executor

from headwind.spec import CollectorModel, CollectorType, CollectorResult


class CollectorError(BaseException):
    exc: pydantic.error_wrappers.ValidationError

    def __init__(self, exc: pydantic.error_wrappers.ValidationError):
        self.exc = exc


def run_collector(model: CollectorModel) -> CollectorResult:
    if model.type == CollectorType.Python:
        raise NotImplementedError("Currently not implemented")
    else:
        # print("Running", model.arg)
        # result = subprocess.run(
        #     model.arg, shell=True, capture_output=True, encoding="utf-8"
        # ).stdout
        result = subprocess.check_output(model.arg, shell=True, encoding="utf-8")
        # print("Raw result:")
        # print(result)
        try:
            return cast(CollectorResult, CollectorResult.parse_raw(result))
        except pydantic.error_wrappers.ValidationError as e:
            raise CollectorError(e)


def run_collectors(
    collectors: List[CollectorModel], jobs: int
) -> List[CollectorResult]:
    with make_executor(jobs) as ex:
        fs = [ex.submit(run_collector, c) for c in collectors]
        wait(fs)
        results = [f.result() for f in fs]

    return results
