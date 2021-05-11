import hashlib
import random
from datetime import datetime
from typing import List

from headwind.spec import Run, Commit, Metric


def make_commit() -> Commit:
    return Commit(date=datetime.now(),hash=hashlib.sha1(str(random.random()).encode("utf8")).hexdigest())


def generate_dummy_data(seed: int, n: int, branches: List[str]) -> List[Run]:
    random.seed(seed)

    runs = []
    for branch in branches:
        # parent = Commit(hash=None)
        for _ in range(n):
            commit = make_commit()

            run = Run(
                commit=commit,
                # parent=parent,
                parent=None,  # this should be determined automatically
                branch=branch,
                date=datetime.now(),
                results=[
                    Metric(
                        name="metric.a.uniform",
                        group="group_a",
                        value=random.uniform(5, 20),
                        unit="seconds",
                    ),
                    Metric(
                        name="metric.b.gauss",
                        group="group_a",
                        value=random.gauss(0, 4),
                        unit="MB",
                    ),
                    Metric(
                        name="metric.c.gauss",
                        group="group_b",
                        value=random.gauss(-3, 2),
                        unit="MB",
                    ),
                    Metric(
                        name="metric.d.beta",
                        group="group_b",
                        value=random.betavariate(2, 5),
                        unit="us",
                    ),
                    Metric(
                        name="metric.d.gamma",
                        group="group_c",
                        value=random.gammavariate(2, 5),
                        unit="ns",
                    ),
                ],
            )

            runs.append(run)
            # parent = commit

    return runs
