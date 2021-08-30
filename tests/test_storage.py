from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import Mock

import pytest
from headwind.spec import Run, Commit, Metric
from headwind.storage import Storage


def test_make_filename() -> None:
    act = Storage._make_filename(
        Commit(hash="ABCDEFG" + "Y" * 33, date=datetime.now(), message="blub")
    )
    assert "ABCDEFG" + "Y" * 33 + ".json" == act


@pytest.fixture
def dummy_run() -> Run:
    return Run(
        commit=Commit(hash="X" * 40, date=datetime.now(), message="blubb"),
        parent=Commit(hash="X" * 40, date=datetime.now(), message="blubb"),
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
        storage.get(Commit(hash="J" * 40, date=datetime.now(), message="blubb"))


def test_iterate(dummy_runs: List[Run], stored_runs: Storage):
    mid = int(len(dummy_runs) / 2)
    act = list(stored_runs.iterate(dummy_runs[mid - 1].commit))
    exp = list(reversed(dummy_runs[:mid]))
    assert exp == act

    act = list(stored_runs.iterate(dummy_runs[-1].commit))
    exp = list(reversed(dummy_runs[mid:]))
    assert exp == act


def test_iterate_all(dummy_runs: List[Run], stored_runs: Storage):
    exp = sorted(dummy_runs, key=lambda r: r.commit.hash)
    act = list(stored_runs.iterate_all())
    assert exp == act


def test_find_branch_tips(dummy_runs: List[Run], stored_runs: Storage):
    tips = stored_runs.find_branch_tips()
    assert tips["main"] == dummy_runs[int(len(dummy_runs) / 2 - 1)].commit
    assert tips["feature"] == dummy_runs[-1].commit

    assert stored_runs.find_branch_tips() == stored_runs.find_branch_tips_slow()


def test_dataframe(dummy_runs: List[Run], stored_runs: Storage):
    print()
    df = stored_runs.dataframe()

    print(df.head())
    print(df.tail())


def test_get_branch_tip(stored_runs: Storage, dummy_runs: List[Run]) -> None:
    mid = int(len(dummy_runs) / 2)
    exp1 = dummy_runs[mid - 1]
    exp2 = dummy_runs[-1]

    act1 = stored_runs.get_branch_tip(exp1.branch)
    assert act1 == exp1.commit

    act2 = stored_runs.get_branch_tip(exp2.branch)
    assert act2 == exp2.commit

    slow = stored_runs.find_branch_tips_slow()

    for branch, exp in slow.items():
        act = stored_runs.get_branch_tip(branch)
        assert act == exp


def test_get_branches(stored_runs: Storage) -> None:
    assert sorted(stored_runs.get_branches()) == sorted(["main", "feature"])


def test_metrics(stored_runs: Storage, dummy_runs: List[Run]) -> None:
    exp = {}
    for run in dummy_runs:
        for m in run.results:
            m2 = m.copy()
            m2.value = None
            if m2.group is not None:
                exp.setdefault(m2.group, set())
                exp[m2.group].add(m2)
            else:
                exp.setdefault("other", set())
                exp["other"].add(m2)

    # exp = sorted(exp, key=lambda m: m.name)
    exp = {k: sorted(v, key=lambda m: m.name) for k, v in exp.items()}

    act = stored_runs.get_metrics()
    # act = sorted(act, key=lambda m: m.name)

    assert exp == act


def test_count(stored_runs: Storage, dummy_runs: List[Run]) -> None:
    assert stored_runs.num_runs() == len(dummy_runs)
