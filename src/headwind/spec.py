from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, IO, List, Optional, cast, Callable
import textwrap
from matplotlib.pyplot import text

from pydantic import BaseModel, validator, Field, root_validator
import pydantic
import json
import yaml
import pandas


class CollectorType(str, Enum):
    Python = "python"
    Command = "command"


class CollectorModel(BaseModel):
    type: CollectorType
    arg: str

    class Config:
        extra = "forbid"


class Metric(BaseModel):
    name: str
    group: Optional[str]
    value: Optional[float]
    unit: str

    @validator("group")
    def _(cls, v: Optional[str], **kwargs: Any) -> Optional[str]:
        if v is not None:
            assert len(v) > 0, "Group name cannot be empty"
        return v

    def __hash__(self):
        return hash(self.name)


class ReportFilter:
    fn: Optional[Callable[[Metric, pandas.DataFrame], bool]]

    def __init__(self, fn: Optional[Callable[[Metric, pandas.DataFrame], bool]]):
        self.fn = fn

    def __call__(self, metric: Metric, df: pandas.DataFrame) -> bool:
        if self.fn is None:
            return True
        return self.fn(metric, df)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: str):
        v = textwrap.dedent(v)
        l = {}
        exec(v, {}, l)
        return cls(l["func"])


class Spec(BaseModel):
    collectors: List[CollectorModel]
    spec_file: Path
    storage_dir: Path
    report_filter: ReportFilter = ReportFilter(None)
    github_project: Optional[str] = None

    class Config:
        extra = "forbid"

    @validator("collectors")
    def at_least_one_collector(
        cls, v: List[CollectorModel], **kwargs: Any
    ) -> List[CollectorModel]:
        assert len(v) > 0, "At least one collector needs to be given."
        return v

    @root_validator
    def root_validator(slc, values: Dict[str, Any]):
        assert "spec_file" in values
        spec_file = cast(Path, values["spec_file"])
        assert spec_file.exists()
        assert "storage_dir" in values
        path = spec_file.parent / values["storage_dir"]
        path = path.absolute()
        if not path.exists():
            path.mkdir(parents=True)
        assert path.is_dir(), f"Path {path} is not a directory"
        values["storage_dir"] = path
        return values


SpecValidationError = pydantic.error_wrappers.ValidationError


def load_spec(file: IO[str]) -> Spec:
    values = yaml.safe_load(file)
    if not isinstance(values, dict):
        raise ValueError("Invalid spec")

    values["spec_file"] = file.name
    return Spec(**values)


class CollectorResult(BaseModel):
    metrics: List[Metric] = Field(..., min_items=1)

    @validator("metrics")
    def _(cls, v: List[Metric], **kwargs: Any) -> List[Metric]:
        names = set(m.name for m in v)
        assert len(names) == len(v), "Metrics have duplicate names"
        return v


class Commit(BaseModel):
    date: datetime
    hash: str = Field(min_length=40, max_length=40)
    message: str


class Run(BaseModel):
    commit: Commit
    parent: Optional[Commit]
    branch: str = Field(..., min_length=1)
    date: datetime
    results: List[Metric] = Field(..., min_items=1)

    context: Dict[str, Any] = {}

    @validator("context")
    def validate_context(cls, v: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        try:
            json.dumps(v)
            return v
        except (TypeError, ValueError, OverflowError) as e:
            raise e

    @validator("results")
    def validate_results(cls, v: List[Metric], **kwargs: Any) -> List[Metric]:
        names = set(m.name for m in v)
        assert len(names) == len(v), "Metrics have duplicate names"
        return v
