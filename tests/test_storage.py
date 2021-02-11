from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from headwind.spec import Run, Commit, Metric
from headwind.storage import Storage


def test_make_filename() -> None:
    run = Mock()
    run.commit = Mock()
    run.commit.hash = "ABCDEFG" + "Y" * 33
    run.date = datetime(year=2021, month=2, day=10, hour=16, minute=42, second=3)

    act = Storage._make_filename(run)
    assert "ABCDEFG" + "Y" * 33 + ".json" == act


@pytest.fixture
def dummy_run() -> Run:
    return Run(
        commit=Commit(hash="X" * 40),
        parent=Commit(hash="X" * 40),
        branch="main",
        date=datetime.now(),
        results=[Metric(name="a.metric", value=42, unit="X")],
    )


def test_store(dummy_run: Run, tmp_path: Path) -> None:
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    storage = Storage(storage_dir)
    storage.store_run(dummy_run)

    exp_file = storage_dir / Storage._make_filename(dummy_run)
    assert exp_file.exists()

    raw = exp_file.read_text()
    assert raw == dummy_run.json(indent=2)
