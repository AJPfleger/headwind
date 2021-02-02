from pathlib import Path
from enum import Enum
from typing import Any, Dict, IO, List, Optional, Union

from pydantic import BaseModel, validator
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
    metrics: List[Metric]
