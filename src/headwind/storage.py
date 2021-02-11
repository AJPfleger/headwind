from pathlib import Path

from headwind.spec import Run


class Storage:
    base_dir: Path

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        assert self.base_dir.exists(), "Storage directory does not exist"

    @staticmethod
    def _make_filename(run: Run) -> str:
        # return f"{run.commit.hash[:7]}_{run.date.strftime('%Y-%m-%dT%H-%M-%S')}.json"
        return f"{run.commit.hash}.json"

    def store_run(self, run: Run) -> None:
        filename = self._make_filename(run)
        target_file = self.base_dir / filename

        with target_file.open("w") as fh:
            fh.write(run.json(indent=2))
