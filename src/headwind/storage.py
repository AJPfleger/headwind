import json
import re
from pathlib import Path
from typing import Iterator, Dict, List

import yaml
import pandas

from headwind.spec import Run, Commit


class Storage:
    base_dir: Path

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        assert self.base_dir.exists(), "Storage directory does not exist"

    @staticmethod
    def _make_filename(commit: Commit) -> str:
        # return f"{run.commit.hash[:7]}_{run.date.strftime('%Y-%m-%dT%H-%M-%S')}.json"
        return f"{commit.hash}.json"

    def store_run(self, run: Run) -> None:
        tip = self.get_branch_tip(run.branch)
        run.parent = tip
        filename = self._make_filename(run.commit)
        target_file = self.base_dir / filename

        with target_file.open("w") as fh:
            fh.write(run.json(indent=2))

        with self._get_branch_file(run.branch).open("w") as fh:
            fh.write(run.commit.json(indent=2))


    def get(self, commit: Commit) -> Run:
        filename = self._make_filename(commit)
        file = self.base_dir / filename
        assert file.exists()
        with file.open("r") as fh:
            return Run(**json.load(fh))
            # return Run(**yaml.safe_load(fh.read()))

    def iterate_all(self) -> Iterator[Run]:
        for f in sorted(self.base_dir.iterdir()):
            if not f.is_file(): continue
            if f.name.startswith("branch_"): continue
            with f.open("r") as fh:
                yield Run(**json.load(fh))

    def _get_branch_file(self, branch: str) -> Path:
        return self.base_dir / f"branch_{branch}.json"

    def get_branch_tip(self, branch: str) -> Commit:
        filename = self._get_branch_file(branch)
        if not filename.exists(): return Commit(hash=None)
        with filename.open("r") as fh:
            return Commit(**json.load(fh))

    def get_branches(self) -> List[str]:
        out = []
        for f in self.base_dir.iterdir():
            if not f.name.startswith("branch_"): continue
            m = re.match(r"^branch_(.*).json$", f.name)
            out.append(m.group(1))
            # out.append(f.read_text().strip())
        return out

    def find_branch_tips(self) -> Dict[str, Commit]:
        return {b: self.get_branch_tip(b) for b in self.get_branches()}

    def find_branch_tips_slow(self) -> Dict[str, Commit]:
        by_parent = {}
        origins: List[Run] = []
        for run in self.iterate_all():
            if run.parent.hash is None:
                origins.append(run)
            else:
                by_parent[run.parent.hash] = run

        tips = {}

        for origin in origins:
            candidate: Run = origin
            error = True
            for _ in range(100000): # some large number for protection
                next_candidate = by_parent.get(candidate.commit.hash)
                # print("candidate:", candidate.commit.hash, "next:", next_candidate)
                if next_candidate is None:
                    tips[candidate.branch] = candidate.commit
                    error = False
                    break
                candidate = next_candidate
            if error:
                raise RuntimeError("Infinite loop")

        return tips


    def iterate(self, start: Commit) -> Iterator[Run]:
        current = self.get(start)
        yield current
        while current.parent.hash is not None:
            current = self.get(current.parent)
            yield current

    def dataframe(self) -> pandas.DataFrame:
        tips = self.find_branch_tips()
        tip: Commit


        def iterator() -> Iterator[Dict[str, float]]:
            for tip in tips.values():
                for run in self.iterate(tip):
                    # for m in run.results:
                    #     print(m.name)
                    d =  dict([(m.name, m.value) for m in run.results])
                    d["branch"] = run.branch
                    d["commit"] = run.commit.hash
                    d["parent"] = run.parent.hash
                    yield d

        df = pandas.DataFrame.from_records(iterator())
        return df

