import functools
from pathlib import Path
from typing import Dict, Any, cast

import yaml
from pydantic import BaseModel, validator

CONFIG_FILE_NAME = ".headwind.yml"


@functools.cache
def find_config_file() -> Path:
    to_try = [Path.cwd()] + list(Path.cwd().parents)
    for current in to_try:
        candidate = current / CONFIG_FILE_NAME
        # print(candidate)
        if candidate.exists():
            return candidate
    raise ValueError("Unable to find config file")


class Config(BaseModel):
    config_file: Path
    storage_dir: Path

    @validator("storage_dir")
    def validate_storage_dir(cls, value: Path, values: Dict[str, Any]) -> Path:
        path = cast(Path, values["config_file"]).parent / value
        assert path.exists(), f"Storage path not found: {path}"
        assert path.is_dir(), f"Path {path} is not a directory"
        return path

    @classmethod
    def load(cls, path: Path) -> "Config":
        assert path.exists(), "Target file not found"

        with path.open() as fh:
            data = yaml.safe_load(fh)
            data["config_file"] = path
            return cls(**data)
