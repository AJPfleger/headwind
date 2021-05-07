from headwind.storage import Storage

import matplotlib.pyplot as plt
import numpy as np

def make_report(storage: Storage) -> None:
    print(storage.get_branches())

    df = storage.dataframe()


    # print(df.columns)
    for branch, bdf in df.groupby("branch"):
        # print(bdf.head())
        # print(bdf.columns)
        for col in bdf.columns:
            if not col.startswith("metric"): continue

            # sl = slice(-100, None)
            sl = slice(None, None)
            fig, ax = plt.subplots(figsize=(15, 5))
            commits = bdf.commit[sl]
            # ci = np.arange(len(commits))
            ax.plot(bdf.date, bdf[col][sl])

            # ax.set_xticks(ci)
            # ax.set_xticklabels([c[:7] for c in commits], rotation=45, ha="right")


            fig.tight_layout()
            fig.savefig(f"report/{branch}_{col}.png")



