from concurrent.futures import wait
from datetime import datetime
from pathlib import Path

import typer
from headwind.collector import Collector, CollectorError
from headwind.executor import make_executor
from wasabi import msg

from headwind.spec import load_spec, CollectorResult, Run, Commit

app = typer.Typer(add_completion=False)


@app.command()
def publish() -> None:
    raise NotImplementedError()


@app.command("collect")
def collect_cmd(spec_file: typer.FileText, jobs: int = typer.Option(1, "--jobs", "-j")) -> None:
    msg.info(f"#jobs: {jobs}")
    if jobs > 1:
        msg.warn("If you're running benchmarks from the collect call, concurrency can affect results")

    assert jobs > 0, "Jobs value must be positive"
    spec = load_spec(spec_file)

    msg.good("Spec loaded successfully")
    msg.divider()

    collectors = map(Collector, spec.collectors)

    with make_executor(jobs) as ex:
        try:
            with msg.loading("Collecting..."):
                fs = [ex.submit(c.run) for c in collectors]
                wait(fs)
                results = [f.result() for f in fs]
        except CollectorError as e:
            msg.fail("Collector returned invalid format")
            typer.echo(str(e.exc))
            return

    msg.good("Collection completed")
    print(results)

    run = Run(
        commit=Commit(hash="x" * 40),
        parent=Commit(hash="x" * 40),
        branch="master",
        date=datetime.now(),
        results=results,
        context={},
    )

    # for result in results:

# @app.command("schema")
# def schema() -> None:
#     print(CollectorResult.schema_json(indent=2))
