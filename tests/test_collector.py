import subprocess
from unittest.mock import Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from headwind.collector import run_collector, CollectorError
from headwind.spec import CollectorType, CollectorResult, Metric


def test_run_collector(monkeypatch: MonkeyPatch) -> None:
    model = Mock()
    model.type = CollectorType.Python

    with pytest.raises(NotImplementedError):
        run_collector(model)

    model.type = CollectorType.Command

    with monkeypatch.context() as m:
        ret = Mock()
        ret.stdout = "blubb"
        run = Mock(return_value=ret)
        m.setattr(subprocess, "run", run)
        with pytest.raises(CollectorError):
            run_collector(model)

        exp = CollectorResult(
            metrics=[
                Metric(name="some.value", value=42.42, unit="plumbus"),
                Metric(name="some.value2", value=42.42, unit="plumbus"),
            ]
        )

        ret.stdout = exp.json()
        act = run_collector(ret)

        assert exp == act
