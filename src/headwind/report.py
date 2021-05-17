from pathlib import Path
from re import I
import shutil
from sys import prefix
from typing import Union
import functools
import contextlib
from concurrent.futures import ProcessPoolExecutor, as_completed

import matplotlib.pyplot as plt
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

def make_environment() -> jinja2.Environment:
    env = jinja2.Environment(loader=jinja2.PackageLoader(package_name="headwind"))

    env.globals["static_url"] = static_url
    env.globals["metric_url"] = metric_url
    env.globals["group_url"] = group_url

    env.globals["url_for"] = url_for
    env.globals["current_url"] = get_current_url
    env.globals["is_group_active"] = is_group_active

    return env


def copy_static(output: Path) -> None:
    static = Path(__file__).parent / "static"
    assert static.exists()
    dest = output / "static"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(static, dest)

def process_metric(metric: Metric, df: pandas.DataFrame, output: Path, metrics_by_group 
):
    url = metric_url(metric)
    # print(url)
    page = output / url / "index.html"

    env = make_environment()
    env.globals["metrics"] = metrics_by_group

    plot_dir = output / "plots"
    if not plot_dir.exists():
        plot_dir.mkdir(parents=True)

    metric_tpl = env.get_template("metric.html.j2")

    fs = (15, 5)
    sl = slice(None, 100)

    if not page.parent.exists():
        page.parent.mkdir(parents=True)

    metric_plots = []

    bfig, bax = plt.subplots(figsize=fs)

    for branch, bdf in df.groupby("branch"):
        fig, ax = plt.subplots(figsize=fs)
        bdf = bdf[::-1]
        commits = bdf.commit[sl]
        dates = bdf.date[sl]
        ci = np.arange(len(commits))

        ax.plot(ci, bdf[metric.name][sl])
        ax.set_xticks(ci)
        bax.set_xticks(ci)

        bax.plot(ci, bdf[metric.name][sl], label=branch)

        labels = [
            d.strftime("%Y-%m-%d") + " - " + c[:7]
            for c, d in zip(commits, dates)
        ]

        ax.set_xlabel("Commits")
        ax.set_ylabel(f"value [{metric.unit}]")

        ax.set_xticklabels(labels, rotation=45, ha="right")
        bax.set_xticklabels(labels, rotation=45, ha="right")

        ax.set_title(f"{metric.name} on {branch}")

        fig.tight_layout()
        plot_url = (
            plot_dir.relative_to(output)
            / f"{branch}_{path_sanitize(metric.name)}.svg"
        )
        if not plot_url.parent.exists():
            plot_url.parent.mkdir(parents=True)
        fig.savefig(output / plot_url)
        plt.close(fig)
        metric_plots.append(plot_url)

    tpl_df_cols = ["branch", "commit", "date", metric.name]
    tpl_df = df[tpl_df_cols].copy()
    tpl_df.commit = tpl_df.commit.str[:7]
    tpl_df.columns = ["branch", "commit", "date", "value"]

    with push_url(url):
        page.write_text(
            metric_tpl.render(metric=metric, plots=metric_plots, dataframe=tpl_df)
        )

    bax.legend()
    bax.set_title(f"{metric.name}")
    bfig.tight_layout()
    plot_url = (
        plot_dir.relative_to(output) / f"{metric.group}_{path_sanitize(metric.name)}.svg"
    )
    if not plot_url.parent.exists():
        plot_url.parent.mkdir(parents=True)
    bfig.savefig(output / plot_url)
    plt.close(bfig)

    return metric, plot_url

def make_report(spec: Spec, storage: Storage, output: Path) -> None:
    print(storage.get_branches())
    msg.info("Begin")

    plt.interactive(False)

    msg.info("Creating dataframe")
    df, metrics_by_group = storage.dataframe(with_metrics=True)

    metrics_by_group = {g: list(filter(lambda m: spec.report_filter(m, df), ms)) for g, ms in metrics_by_group.items()}

    msg.good("Dataframe created")

    env = make_environment()
    env.globals["metrics"] = metrics_by_group

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
            futures = [ex.submit(process_metric, m, 
            df,
             output
             , metrics_by_group
             ) for m in metrics]
            for f in rich.progress.track(as_completed(futures), total=len(futures)):
                metric, plot_url = f.result()
                group_plots.append(plot_url)
                print(metric.name)

        # for metric in rich.progress.track(metrics):
        #     process_metric(metric, df, output, env)

        url = group_url(group)
        page = output / url / "index.html"

        with push_url(url):
            page.write_text(group_tpl.render(group=group, plots=group_plots))
