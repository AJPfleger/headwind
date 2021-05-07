import hashlib
from datetime import datetime

import pytest
import random

from headwind.spec import Commit, Run, Metric


def make_commit() -> Commit:
    return Commit(hash=hashlib.sha1(str(random.random()).encode("utf8")).hexdigest())

@pytest.fixture
def dummy_runs():
    random.seed(42)
    runs = []
    for branch in ("main", "feature"):
        parent = Commit(hash=None)
        for _ in range(100):
            commit = make_commit()

            run = Run(
                commit=commit,
                parent=parent,
                branch=branch,
                date=datetime.now(),
                results=[
                    Metric(name="metric.a.uniform", group="group_a",value=random.uniform(5, 20),unit="seconds"),
                    Metric(name="metric.b.gauss", group="group_a", value=random.gauss(0, 4), unit="MB"),
                    Metric(name="metric.c.gauss", group="group_b", value=random.gauss(-3, 2), unit="MB"),
                    Metric(name="metric.d.beta", group="group_b", value=random.betavariate(2, 5), unit="us"),
                    Metric(name="metric.d.gamma", group="group_c", value=random.gammavariate(2, 5), unit="ns"),
                ]
            )

            runs.append(run)
            parent = commit

    return runs
