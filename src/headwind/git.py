from headwind.spec import Commit

import subprocess


def get_current_commit() -> Commit:
    return Commit(hash=subprocess.check_output(["git", "rev-parse", "HEAD"], encoding="utf8").strip())

def get_parent_commit() -> Commit:
    return Commit(hash=subprocess.check_output(["git", "rev-parse", "HEAD^"], encoding="utf8").strip())

def get_branch() -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], encoding="utf8").strip()
