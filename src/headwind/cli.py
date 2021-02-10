from datetime import datetime

import typer
from headwind.collector import CollectorError, run_collectors
from wasabi import msg

from headwind.spec import load_spec, Run, Commit

app = typer.Typer(add_completion=False)


@app.command()
def publish() -> None:
    raise NotImplementedError()


@app.command("collect")
def collect_cmd(
    spec_file: typer.FileText, jobs: int = typer.Option(1, "--jobs", "-j")
) -> None:
    msg.info(f"#jobs: {jobs}")
    if jobs > 1:
        msg.warn(
            "If you're running benchmarks from the collect call,"
            " concurrency can affect results"
        )

    assert jobs > 0, "Jobs value must be positive"
    spec = load_spec(spec_file)

    msg.good("Spec loaded successfully")
    msg.divider()

    try:
        with msg.loading("Collecting..."):
            results = run_collectors(spec.collectors, jobs=jobs)
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
        results=sum((r.metrics for r in results), []),
        context={},
    )

    print(run)

    # for result in results:


# @app.command("schema")
# def schema() -> None:
#     print(CollectorResult.schema_json(indent=2))
