import tempfile

import pytest
import pydantic

from headwind.spec import Metric, MetricType


def test_metric() -> None:
    m = Metric(type=MetricType.Python, arg="my.module.func", name="x")
    assert m is not None
    with pytest.raises(pydantic.error_wrappers.ValidationError):
        m = Metric(type="NOPE", arg="my.module.func", name="x")

    with pytest.raises(pydantic.error_wrappers.ValidationError):
        m = Metric(type="NOPE", arg=42, name="x")

    with pytest.raises(pydantic.error_wrappers.ValidationError):
        m = Metric(type=MetricType.Command, arg="nonexistant file", name="x")

    with tempfile.NamedTemporaryFile() as f:
        m = Metric(type=MetricType.Command, arg=f.name, name="x")


def test_metric_context() -> None:
    c = {"a": 2, "b": "something"}
    m = Metric(type=MetricType.Python, arg="blubb", name="works", context=c)

    class Custom:
        pass

    c = {"a": Custom(), "b": "something"}
    with pytest.raises(pydantic.error_wrappers.ValidationError):
        m = Metric(type=MetricType.Python, arg="blubb", name="works", context=c)
