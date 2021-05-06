import subprocess

from headwind.git import get_current_commit, get_parent_commit, get_branch



def test_get_current_commit():
    commit  = subprocess.check_output(["git", "rev-parse", "HEAD"], encoding="utf8").strip()
    assert get_current_commit().hash == commit

def test_get_parent_commit():
    commit  = subprocess.check_output(["git", "rev-parse", "HEAD^"], encoding="utf8").strip()
    assert get_parent_commit().hash == commit

def test_get_branch():
    branch= subprocess.check_output(["git", "branch", "--show-current"], encoding="utf8").strip()
    assert get_branch() == branch

