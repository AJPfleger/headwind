import random
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import pytest
from click.testing import Result
from headwind.spec import Commit, Metric, Run
from headwind.storage import Storage


def test_run(stored_runs: Storage, dummy_runs: List[Run]):
    # assert len(dummy_runs) == 2*10

    mid = int(len(dummy_runs) / 2)

    tips = stored_runs.find_branch_tips()
    loaded_runs = sum(
        [list(reversed(list(stored_runs.iterate(t)))) for t in tips.values()], []
    )

    print()
    print(len(loaded_runs))

    assert loaded_runs[0].parent is None
    assert loaded_runs[mid].parent is None

    for run_prev, run in zip(loaded_runs[:mid], loaded_runs[1:mid]):
        assert run_prev.commit == run.parent
        assert run.parent is not None

    for run_prev, run in zip(loaded_runs[mid:], loaded_runs[mid + 1 :]):
        assert run_prev.commit == run.parent
        assert run.parent is not None
