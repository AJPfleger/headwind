from headwind.spec import Commit


def get_current_commit() -> Commit:
    return Commit(hash="x" * 40)


def get_parent_commit() -> Commit:
    return Commit(hash="y" * 40)
