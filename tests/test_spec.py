import io

import pytest
import pydantic

from headwind.spec import CollectorModel, CollectorType, SpecValidationError, load_spec, Spec


def test_collector() -> None:
    c = CollectorModel(type=CollectorType.Python, arg="my.module.func")
    assert c is not None

    with pytest.raises(pydantic.error_wrappers.ValidationError):
        CollectorModel(type="NOPE", arg="my.module.func")

    with pytest.raises(pydantic.error_wrappers.ValidationError):
        CollectorModel(type="NOPE", arg=42)

    c = CollectorModel(type="python", arg="some-module")
    assert c is not None

    with pytest.raises(pydantic.error_wrappers.ValidationError):
        CollectorModel(type="invali", arg="some-module")


def test_spec() -> None:
    s = Spec(collectors=[{'type': 'command', 'arg': 'echo 42'}])
    assert s is not None


def test_load_spec() -> None:
    buf = io.StringIO()
    buf.write("")

    with pytest.raises(ValueError):
        load_spec(buf)

    buf = io.StringIO()
    buf.write("wrong: 54")
    buf.seek(0)

    with pytest.raises(SpecValidationError):
        load_spec(buf)

    buf = io.StringIO()
    buf.write(
        """
collectors:
    - type: python
      arg: some.module
""".strip()
    )
    buf.seek(0)

    s = load_spec(buf)

    assert len(s.collectors) == 1

    assert s.collectors[0].type == CollectorType.Python
    assert s.collectors[0].arg == "some.module"

    buf = io.StringIO()
    buf.write(
        """
beep: "nope"
collectors:
    - type: python
      arg: some.module
""".strip()
    )
    buf.seek(0)

    with pytest.raises(SpecValidationError):
        load_spec(buf)
