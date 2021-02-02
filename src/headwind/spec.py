from pathlib import Path
from enum import Enum
from typing import Any, Dict, IO, List, Optional, Union

from pydantic import BaseModel, validator
from pydantic.class_validators import root_validator
import json
import yaml


class MetricType(Enum):
    Python = 1
    Command = 2


class Metric(BaseModel):
    type: MetricType
    arg: str
    name: str
    context: Dict[str, Any] = {}

    @validator("arg")
    def arg_exists(cls, v: str, values: Any, **kwargs: Any) -> Union[Path, str]:
        assert "type" in values
        if values["type"] == MetricType.Command:
            p = Path(v)
            assert p.exists()
            return p
        return v

    @validator("context")
    def is_json_serializable(cls, v: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        try:
            s = json.dumps(v)
            return v
        except:
            raise ValueError("Context is not JSON serializable")


class Spec(BaseModel):
    metric: List[Metric]

    @validator("metric")
    def at_least_one_metric(cls, v: List[Metric], **kwargs: Any) -> List[Metric]:
        assert len(v) > 0
        return v


def load_spec(file: IO[str]) -> Spec:
    values = yaml.safe_load(file)
    return Spec(**values)