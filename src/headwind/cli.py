from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from headwind.collector import CollectorError, run_collectors
from headwind.config import find_config_file, Config
from headwind.git import get_current_commit, get_parent_commit
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
    config_file: Optional[Path] = None,
) -> None:
    commit = Commit(hash=str(commit_in))
    parent = Commit(hash=str(parent_in))
    if config_file is None:
        config_file = find_config_file()

    config = Config.load(config_file)

    msg.info(f"#jobs: {jobs}")
    msg.info(f"on commit:     {commit}")
    msg.info(f"parent commit: {parent}")
    msg.info(f"loading config from {config_file}")

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

    # print(run)

    storage = Storage(config.storage_dir)

    storage.store_run(run)

    # for result in results:


# @app.command("schema")
# def schema() -> None:
#     print(CollectorResult.schema_json(indent=2))
