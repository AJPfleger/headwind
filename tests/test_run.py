import random
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import pytest
from click.testing import Result
from headwind.spec import Commit, Metric, Run
from headwind.storage import Storage


def test_run(dummy_runs: List[Run]):
    # assert len(dummy_runs) == 2*10

    mid = int(len(dummy_runs)/2)

    assert dummy_runs[0].parent.hash is None
    assert dummy_runs[mid].parent.hash is None


    for run_prev, run in zip(dummy_runs[:mid], dummy_runs[1:mid]):
        assert run_prev.commit == run.parent

    for run_prev, run in zip(dummy_runs[mid:], dummy_runs[mid+1:]):
        assert run_prev.commit == run.parent
