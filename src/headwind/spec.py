from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Any, Dict, IO, List, Optional, Union

from pydantic import BaseModel, validator, constr, conlist
import pydantic
from pydantic.class_validators import root_validator
import json
import yaml


class CollectorType(str, Enum):
    Python = "python"
    Command = "command"


class CollectorModel(BaseModel):
    type: CollectorType
    arg: str

    class Config:
        extra = "forbid"


class Spec(BaseModel):
    collectors: List[CollectorModel]

    class Config:
        extra = "forbid"

    @validator("collectors")
    def at_least_one_collector(
        cls, v: List[CollectorModel], **kwargs: Any
    ) -> List[CollectorModel]:
        assert len(v) > 0, "At least one collector needs to be given."
        return v


SpecValidationError = pydantic.error_wrappers.ValidationError


def load_spec(file: IO[str]) -> Spec:
    values = yaml.safe_load(file)
    if not isinstance(values, dict):
        raise ValueError("Invalid spec")

    return Spec(**values)


class Metric(BaseModel):
    name: str
    group: Optional[str]
    value: float
    unit: str

    @validator("group")
    def _(cls, v: Optional[str], **kwargs: Any) -> Optional[str]:
        if v is not None:
            assert len(v) > 0, "Group name cannot be empty"
        return v


class CollectorResult(BaseModel):
    metrics: conlist(Metric, min_items=1)


class Commit(BaseModel):
    hash: constr(min_length=40, max_length=40)

    # @validator("hash")
    # def _(cls, v: str, **kwargs: Any) -> str:
    #     assert len(v) == 40, "Commit hash has invalid length"
    #     returned v


class Run(BaseModel):
    commit: Commit
    parent: Commit
    branch: constr(min_length=1)
    date: datetime
    results: conlist(Metric, min_items=1)

    context: Dict[str, Any]

    @validator("context")
    def _(cls, v: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        try:
            json.dumps(v)
            return v
        except (TypeError, ValueError, OverflowError) as e:
            raise e
