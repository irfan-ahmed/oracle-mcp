import git
from pathlib import Path


def get_changed_servers_from_commit(repo, commit):
    if commit.parents:
        diff = commit.diff(commit.parents[0])
    else:
        diff = commit.diff(None)

    changed_servers = set()
    for item in diff:
        path_str = item.a_path or item.b_path
        path = Path(path_str)
        if path.parts and path.parts[0] == "src" and len(path.parts) > 1:
            server_name = path.parts[1]
            changed_servers.add(server_name)
    return changed_servers


def is_changelog_changed_in_commit(repo, commit, server_name):
    if commit.parents:
        diff = commit.diff(commit.parents[0])
    else:
        diff = commit.diff(None)

    changelog_path = Path("src") / server_name / "CHANGELOG.md"
    for item in diff:
        path_str = item.a_path or item.b_path
        if Path(path_str) == changelog_path:
            return True
    return False


def check_commit_changelogs(root_dir="."):
    repo = git.Repo(root_dir)
    commit = repo.head.commit
    changed_servers = get_changed_servers_from_commit(repo, commit)
    for server in changed_servers:
        if not is_changelog_changed_in_commit(repo, commit, server):
            raise ValueError(
                f"Changes detected in {server} but no update to CHANGELOG.md"
            )


def get_changed_servers_from_staged(repo):
    diff = repo.index.diff("HEAD")
    changed_servers = set()
    for item in diff:
        path_str = item.a_path
        path = Path(path_str)
        if path.parts and path.parts[0] == "src" and len(path.parts) > 1:
            server_name = path.parts[1]
            changed_servers.add(server_name)
    return changed_servers


def is_changelog_changed_in_staged(repo, server_name):
    diff = repo.index.diff("HEAD")
    changelog = f"src/{server_name}/CHANGELOG.md"
    for item in diff:
        if item.a_path == changelog:
            return True
    return False


def check_staged_changelogs(root_dir="."):
    repo = git.Repo(root_dir)
    changed_servers = get_changed_servers_from_staged(repo)
    for server in changed_servers:
        if not is_changelog_changed_in_staged(repo, server):
            raise ValueError(
                f"Staged changes in {server} but no update to CHANGELOG.md"
            )


def check_changelogs(staged=False):
    if staged:
        check_staged_changelogs()
    else:
        check_commit_changelogs()
