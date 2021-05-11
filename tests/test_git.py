import subprocess
from datetime import datetime

from headwind.git import get_current_commit, get_parent_commit, get_branch


def test_get_current_commit():
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], encoding="utf8"
    ).strip()
    date = datetime.fromisoformat(
        subprocess.check_output(
            ["git", "show", "-s", "--format=%cI", "HEAD"], encoding="utf8"
        ).strip()
    )

    c = get_current_commit()
    assert c.hash == commit
    assert c.date == date


def test_get_parent_commit():
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD^"], encoding="utf8"
    ).strip()
    date = datetime.fromisoformat(
        subprocess.check_output(
            ["git", "show", "-s", "--format=%cI", "HEAD^"], encoding="utf8"
        ).strip()
    )

    c = get_parent_commit()
    assert c.hash == commit
    assert c.date == date


def test_get_branch():
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], encoding="utf8"
    ).strip()
    assert get_branch() == branch
