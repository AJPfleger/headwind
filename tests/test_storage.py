from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import Mock

import pytest
from headwind.spec import Run, Commit, Metric
from headwind.storage import Storage


def test_make_filename() -> None:
    act = Storage._make_filename(Commit(hash="ABCDEFG" + "Y" * 33))
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


def test_storage(dummy_run: Run, tmp_path: Path) -> None:
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    storage = Storage(storage_dir)
    storage.store_run(dummy_run)

    exp_file = storage_dir / Storage._make_filename(dummy_run.commit)
    assert exp_file.exists()

    raw = exp_file.read_text()
    assert raw == dummy_run.json(indent=2)


    run_read = storage.get(dummy_run.commit)
    assert run_read == dummy_run

    with pytest.raises(AssertionError):
        storage.get(Commit(hash="J"*40))

@pytest.fixture
def stored_runs(dummy_runs, tmp_path) -> Storage:
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    storage = Storage(storage_dir)
    for run in dummy_runs:
        storage.store_run(run)
    return storage

def test_iterate(dummy_runs: List[Run], stored_runs: Storage):
    act = list(stored_runs.iterate(dummy_runs[9].commit))
    exp = list(reversed(dummy_runs[:10]))
    assert exp == act

    act = list(stored_runs.iterate(dummy_runs[-1].commit))
    exp = list(reversed(dummy_runs[10:]))
    assert exp == act

def test_iterate_all(dummy_runs: List[Run], stored_runs: Storage):
    exp = sorted(dummy_runs, key=lambda r: r.commit.hash)
    act = list(stored_runs.iterate_all())
    assert exp == act

def test_find_branch_tips(dummy_runs: List[Run], stored_runs: Storage):
    tips = stored_runs.find_branch_tips()
    assert tips["main"] == dummy_runs[int(len(dummy_runs)/2-1)].commit
    assert tips["feature"] == dummy_runs[-1].commit

def test_dataframe(dummy_runs: List[Run], stored_runs: Storage):
    print()
    df = stored_runs.dataframe()

    print(df.head())
    print(df.tail())
