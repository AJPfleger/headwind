from datetime import datetime
from typing import Optional

from headwind.spec import Commit

import subprocess


def _get_hash(rev: str) -> str:
    return subprocess.check_output(["git", "rev-parse", rev], encoding="utf8").strip()


def get_commit_date(rev: str) -> datetime:
    return datetime.fromisoformat(
        subprocess.check_output(
            ["git", "show", "-s", "--format=%cI", rev], encoding="utf8"
        ).strip()
    )


def get_commit_message(rev: str) -> str:
    return subprocess.check_output(
        ["git", "log", "-n", "1", "--pretty=format:%s", "HEAD"], encoding="utf8"
    ).strip()


def get_current_commit() -> Commit:
    return Commit(
        hash=_get_hash("HEAD"),
        date=get_commit_date("HEAD"),
        message=get_commit_message("HEAD"),
    )


def get_parent_commit() -> Optional[Commit]:
    try:
        return Commit(
            hash=_get_hash("HEAD^"),
            date=get_commit_date("HEAD^"),
            message=get_commit_message("HEAD^"),
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 128:
            return None
        raise e


def get_branch() -> str:
    return subprocess.check_output(
        ["git", "branch", "--show-current"], encoding="utf8"
    ).strip()
