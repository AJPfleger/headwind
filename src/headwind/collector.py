import subprocess

import pydantic
from headwind.spec import Spec, CollectorModel, CollectorType, CollectorResult


class CollectorError(BaseException):
    exc: pydantic.error_wrappers.ValidationError

    def __init__(self, exc: pydantic.error_wrappers.ValidationError):
        self.exc = exc


class Collector:
    def __init__(self, model: CollectorModel):
        self._model = model

    def run(self) -> CollectorResult:
        if self._model.type == CollectorType.Python:
            raise NotImplementedError("Currently not implemented")
        else:
            result = subprocess.run(self._model.arg, shell=True, capture_output=True, encoding="utf-8").stdout
            try:
                return CollectorResult.parse_raw(result)
            except pydantic.error_wrappers.ValidationError as e:
                raise CollectorError(e)
