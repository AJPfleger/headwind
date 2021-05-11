import hashlib
from datetime import datetime

import pytest
import random

from headwind.spec import Commit, Run, Metric
from headwind.storage import Storage

from headwind.test import generate_dummy_data


@pytest.fixture
def dummy_runs():
    return generate_dummy_data(42, 100, ("main", "feature"))


@pytest.fixture
def stored_runs(dummy_runs, tmp_path) -> Storage:
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    storage = Storage(storage_dir)
    for run in dummy_runs:
        storage.store_run(run)
    return storage
