from pathlib import Path

from headwind.storage import Storage

import matplotlib.pyplot as plt
import numpy as np

def make_report(storage: Storage, output: Path) -> None:
    print(storage.get_branches())

    plot_dir = output / "plots"
    if not plot_dir.exists():
        plot_dir.mkdir(parents=True)

    df = storage.dataframe()


    # print(df.columns)
    for branch, bdf in df.groupby("branch"):
        # print(bdf.head())
        # print(bdf.columns)
        for col in bdf.columns:
            if not col.startswith("metric"): continue

            sl = slice(-50, None)
            # sl = slice(None, None)
            fig, ax = plt.subplots(figsize=(15, 5))
            commits = bdf.commit[sl]
            dates = bdf.date[sl]
            ci = np.arange(len(commits))
            # ax.plot(bdf.date, bdf[col][sl])

            ax.plot(ci, bdf[col][sl])
            ax.set_xticks(ci)

            labels = [d.strftime("%Y-%m-%d") + " - " + c[:7] for c, d in zip(commits, dates)]

            ax.set_xticklabels(labels, rotation=45, ha="right")


            fig.tight_layout()
            fig.savefig(plot_dir / f"{branch}_{col}.svg")



