from datetime import datetime
from pathlib import Path
from re import I
import shutil
from sys import prefix
from typing import Union
import functools
import contextlib
from concurrent.futures import ProcessPoolExecutor, as_completed
import re

import numpy as np
import jinja2
from wasabi import msg
import rich.progress
import pandas

from headwind.spec import Metric, Spec
from headwind.storage import Storage

current_depth = 0
current_url = "/"


@contextlib.contextmanager
def push_depth(n: int = 1):
    global current_depth
    current_depth += n
    yield
    current_depth -= n


@contextlib.contextmanager
def push_url(url: Path):
    global current_url
    prev = current_url
    current_url = url
    with push_depth(len(current_url.parts)):
        yield
    current_url = prev


def prefix_url(prefix: str):
    def wrapped(url: Union[str, Path]):
        if isinstance(url, str):
            url = Path(url)
        assert isinstance(url, Path)
        return url_for(prefix / url)

    return wrapped


# def static_url(url: Union[str, Path]) -> Path:
#     if isinstance(url, str):
#         url = Path(url)
#     assert isinstance(url, Path)
#     return url_for("/static" / url)


def url_for(url: Union[str, Path]) -> Path:
    if isinstance(url, str):
        url = Path(url)
    assert isinstance(url, Path)

    prefix = Path(".")
    for _ in range(current_depth):
        prefix = prefix / ".."

    # print(prefix / url)

    return prefix / url


def path_sanitize(path: str) -> str:
    return path.replace("/", "_")


# static_url = prefix_url("static")


def static_url(url: Union[str, Path]) -> Path:
    if isinstance(url, str):
        url = Path(url)
    assert isinstance(url, Path)
    return url_for("static" / url)


def metric_url(metric: Metric) -> Path:
    return url_for(
        Path("metric")
        / path_sanitize(metric.group or "other")
        / path_sanitize(metric.name)
    )


def group_url(group: str) -> Path:
    return url_for(Path("metric") / group)


def is_group_active(group: str) -> bool:
    return str(url_for(current_url)).startswith(str(group_url(group)))


def get_current_url():
    global current_url
    return current_url


def smart_truncate(s, n):
    if len(s) <= n:
        return s

    if "/" in s:
        # looks like a path
        parts = s.split("/")
        return f"{parts[0]}/.../{parts[-1]}"

    n_2 = int(int(n) / 2 - 3)
    n_1 = int(n - n_2 - 3)
    return "{0}...{1}".format(s[:n_1], s[-n_2:])


github_project: str = None


def issue_links(s):
    def rep(m):
        num = m.group(1)
        return f'<a target="blank" href="https://github.com/{github_project}/issues/{num}">#{num}</a>'

    r, _ = re.subn(r"#(\d+)", rep, s)
    return r


def first_line(s):
    return s.split("\n")[0]


def dateformat(d, fmt):
    assert isinstance(d, datetime)
    return d.strftime(fmt)


def make_environment() -> jinja2.Environment:
    env = jinja2.Environment(loader=jinja2.PackageLoader(package_name="headwind"))

    env.globals["static_url"] = static_url
    env.globals["metric_url"] = metric_url
    env.globals["group_url"] = group_url

    env.globals["url_for"] = url_for
    env.globals["current_url"] = get_current_url
    env.globals["is_group_active"] = is_group_active

    env.filters["smart_truncate"] = smart_truncate
    env.filters["issue_links"] = issue_links
    env.filters["first_line"] = first_line
    env.filters["dateformat"] = dateformat

    return env


def copy_static(output: Path) -> None:
    static = Path(__file__).parent / "static"
    assert static.exists()
    dest = output / "static"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(static, dest)


def process_metric(
    metric: Metric,
    df: pandas.DataFrame,
    output: Path,
    metrics_by_group,
    github_project: str,
    num_commits: int,
):
    url = metric_url(metric)
    # print(url)
    page = output / url / "index.html"

    env = make_environment()
    env.globals["metrics"] = metrics_by_group
    env.globals["github_project"] = github_project

    metric_tpl = env.get_template("metric.html.j2")

    fs = (15, 5)
    sl = slice(None, 100)

    if not page.parent.exists():
        page.parent.mkdir(parents=True)

    metric_plots = []

    tpl_df_cols = ["branch", "commit", "date", "message", metric.name]
    tpl_df = df[tpl_df_cols].copy()
    # tpl_df.commit = tpl_df.commit.str[:7]
    tpl_df.columns = ["branch", "commit", "date", "message", "value"]

    chart_data = []
    for row in tpl_df.itertuples():
        chart_data.append(
            {
                "x": f"{row.commit[:7]} {row.date.strftime('%Y-%m-%d')}",
                "y": row.value,
                "commit": row.commit,
                "message": row.message,
            }
        )

    chart_data = chart_data[:num_commits]

    with push_url(url):
        page.write_text(
            metric_tpl.render(
                metric=metric,
                plots=metric_plots,
                dataframe=tpl_df,
                chart_data=chart_data,
            )
        )

    return metric


def make_report(spec: Spec, storage: Storage, output: Path) -> None:
    print(storage.get_branches())
    msg.info("Begin report generation")
    global github_project
    github_project = spec.github_project

    with rich.progress.Progress() as progress:
        task = progress.add_task("Creating dataframe", total=storage.num_runs())
        update = lambda: progress.advance(task)
        df, metrics_by_group = storage.dataframe(
            with_metrics=True, progress_callback=update
        )

    metrics_by_group = {
        g: list(filter(lambda m: spec.report_filter(m, df), ms))
        for g, ms in metrics_by_group.items()
    }

    msg.good("Dataframe created")

    env = make_environment()
    env.globals["metrics"] = metrics_by_group
    env.globals["github_project"] = spec.github_project

    copy_static(output)

    global current_url

    # start page
    tpl = env.get_template("index.html.j2")
    current_url = "/"
    (output / "index.html").write_text(tpl.render())

    group_tpl = env.get_template("group.html.j2")

    for group, metrics in metrics_by_group.items():
        msg.info(f"Group: {group}")

        group_plots = []

        with ProcessPoolExecutor() as ex:
            futures = [
                ex.submit(
                    process_metric,
                    m,
                    df,
                    output,
                    metrics_by_group,
                    spec.github_project,
                    spec.report_num_commits,
                )
                for m in metrics
            ]
            for f in rich.progress.track(as_completed(futures), total=len(futures)):
                metric = f.result()
                print(metric.name)
            msg.good(f"Completed group {group}")

        # for metric in rich.progress.track(metrics):
        #     process_metric(metric, df, output, env)

        url = group_url(group)
        page = output / url / "index.html"

        with push_url(url):
            page.write_text(group_tpl.render(group=group))
