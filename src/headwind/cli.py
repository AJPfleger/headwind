from datetime import datetime

import typer
from headwind.collector import CollectorError, run_collectors
from headwind.git import get_current_commit, get_parent_commit, get_branch
from headwind.storage import Storage
from wasabi import msg

from headwind.spec import load_spec, Run, Commit


app = typer.Typer(add_completion=False)


@app.command()
def publish() -> None:
    raise NotImplementedError()


@app.command("collect")
def collect_cmd(
    spec_file: typer.FileText,
    jobs: int = typer.Option(1, "--jobs", "-j"),
    commit_in: str = typer.Option(
        get_current_commit().hash, "--commit", show_default=True
    ),
    parent_in: str = typer.Option(
        get_parent_commit().hash, "--parent", show_default=True
    ),
    branch: str = typer.Option(
        get_branch(), "--branch", show_default=True
    ),
) -> None:
    commit = Commit(hash=str(commit_in))
    parent = Commit(hash=str(parent_in))

    msg.info(f"#jobs: {jobs}")
    msg.info(f"on commit:     {commit}")
    msg.info(f"parent commit: {parent}")

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
        commit=commit,
        parent=parent,
        branch=branch,
        date=datetime.now(),
        results=sum((r.metrics for r in results), []),
        context={},
    )

    # print(run)

    storage = Storage(spec.storage_dir)

    storage.store_run(run)

    # for result in results:


# @app.command("schema")
# def schema() -> None:
#     print(CollectorResult.schema_json(indent=2))
