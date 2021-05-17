from pathlib import Path
from re import I
import shutil
from sys import prefix
from typing import Union
import functools
import contextlib
from concurrent.futures import ThreadPoolExecutor

import matplotlib.pyplot as plt
import numpy as np
import jinja2
from wasabi import msg
import rich.progress

from headwind.spec import Metric
from headwind.storage import Storage

current_depth = 0
current_url = None


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


static_url = prefix_url("static")


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


def make_environment() -> jinja2.Environment:
    env = jinja2.Environment(loader=jinja2.PackageLoader(package_name="headwind"))

    env.globals["static_url"] = static_url
    env.globals["metric_url"] = metric_url
    env.globals["group_url"] = group_url

    env.globals["url_for"] = url_for
    env.globals["current_url"] = lambda: current_url
    env.globals["is_group_active"] = is_group_active

    return env


def copy_static(output: Path) -> None:
    static = Path(__file__).parent / "static"
    assert static.exists()
    dest = output / "static"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(static, dest)


def make_report(storage: Storage, output: Path) -> None:
    print(storage.get_branches())
    msg.info("Begin")

    plt.interactive(False)

    plot_dir = output / "plots"
    if not plot_dir.exists():
        plot_dir.mkdir(parents=True)

    msg.info("Creating dataframe")
    df, metrics_by_group = storage.dataframe(with_metrics=True)
    msg.good("Dataframe created")

    env = make_environment()

    copy_static(output)

    common = dict(metrics=metrics_by_group)

    global current_url

    # start page
    tpl = env.get_template("index.html.j2")
    current_url = "/"
    (output / "index.html").write_text(tpl.render(**common))

    metric_tpl = env.get_template("metric.html.j2")
    group_tpl = env.get_template("group.html.j2")

    for group, metrics in metrics_by_group.items():
        msg.info(f"Group: {group}")

        group_plots = []

        fs = (15, 5)
        sl = slice(None, 100)

        group_figs = {}

        for metric in rich.progress.track(metrics):
            url = metric_url(metric)
            print(url)
            page = output / url / "index.html"

            if not page.parent.exists():
                page.parent.mkdir(parents=True)

            metric_plots = []

            if not metric.name in group_figs:
                group_figs[metric.name] = plt.subplots(figsize=fs)

            for branch, bdf in df.groupby("branch"):
                fig, ax = plt.subplots(figsize=fs)
                _, bax = group_figs[metric.name]
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

            with push_url(url):
                page.write_text(
                    metric_tpl.render(metric=metric, plots=metric_plots, **common)
                )

        for metric, (bfig, bax) in group_figs.items():
            bax.legend()
            bax.set_title(f"{metric}")
            bfig.tight_layout()
            plot_url = (
                plot_dir.relative_to(output) / f"{group}_{path_sanitize(metric)}.svg"
            )
            if not plot_url.parent.exists():
                plot_url.parent.mkdir(parents=True)
            bfig.savefig(output / plot_url)
            plt.close(bfig)
            group_plots.append(plot_url)

        url = group_url(group)
        page = output / url / "index.html"

        with push_url(url):
            page.write_text(group_tpl.render(group=group, plots=group_plots, **common))

    # for branch, bdf in df.groupby("branch"):
    #     # print(bdf.head())
    #     # print(bdf.columns)
    #     for col in bdf.columns:
    #         # if not col.startswith("metric"): continue
    #         if col not in metrics:
    #             continue

    #         url = metric_url(col)

    #         metric_dir = output / url
    #         if not metric_dir.exists():
    #             metric_dir.mkdir(parents=True)

    #         page = metric_dir / "index.html"

    #         sl = slice(-50, None)
    #         # sl = slice(None, None)
    #         fig, ax = plt.subplots(figsize=(15, 5))
    #         commits = bdf.commit[sl]
    #         dates = bdf.date[sl]
    #         ci = np.arange(len(commits))
    #         # ax.plot(bdf.date, bdf[col][sl])

    #         ax.plot(ci, bdf[col][sl])
    #         ax.set_xticks(ci)

    #         labels = [
    #             d.strftime("%Y-%m-%d") + " - " + c[:7] for c, d in zip(commits, dates)
    #         ]

    #         ax.set_xticklabels(labels, rotation=45, ha="right")

    #         fig.tight_layout()
    #         plot_url = plot_dir.relative_to(output) / f"{branch}_{col}.svg"
    #         fig.savefig(output / plot_url)

    #         tpl = env.get_template("metric.html.j2")
    #         with push_depth(2):
    #             with push_url(metric_url(col)):
    #                 page.write_text(
    #                     tpl.render(metric=col, plot=plot_url.name, **common)
    #                 )
