import pytest
import git
from pathlib import Path
from monorepo_utils.check_changelogs import (
    get_changed_servers_from_commit,
    is_changelog_changed_in_commit,
    check_commit_changelogs,
    get_changed_servers_from_staged,
    is_changelog_changed_in_staged,
    check_staged_changelogs,
    check_changelogs,
)


@pytest.fixture
def temp_repo(tmp_path):
    repo = git.Repo.init(tmp_path)
    (tmp_path / "src").mkdir()
    return repo, tmp_path


def test_get_changed_servers_from_commit(temp_repo):
    repo, path = temp_repo
    server_dir = path / "src" / "server1"
    server_dir.mkdir(parents=True)
    file1 = server_dir / "file.txt"
    file1.write_text("content")
    repo.index.add([str(file1)])
    commit = repo.index.commit("Add file")

    changed = get_changed_servers_from_commit(repo, commit)
    assert changed == {"server1"}


def test_is_changelog_changed_in_commit(temp_repo):
    repo, path = temp_repo
    server_dir = path / "src" / "server1"
    server_dir.mkdir(parents=True)
    changelog = server_dir / "CHANGELOG.md"
    changelog.write_text("changes")
    repo.index.add([str(changelog)])
    commit = repo.index.commit("Update changelog")

    assert is_changelog_changed_in_commit(repo, commit, "server1")


def test_check_commit_changelogs(temp_repo):
    repo, path = temp_repo
    server_dir = path / "src" / "server1"
    server_dir.mkdir(parents=True)
    file1 = server_dir / "file.txt"
    file1.write_text("content")
    changelog = server_dir / "CHANGELOG.md"
    changelog.write_text("changes")
    repo.index.add([str(file1), str(changelog)])
    commit = repo.index.commit("Changes with changelog")

    # Should not raise
    check_commit_changelogs(path)

    # Now without changelog change
    file2 = server_dir / "file2.txt"
    file2.write_text("content2")
    repo.index.add([str(file2)])
    commit2 = repo.index.commit("Changes without changelog")

    with pytest.raises(
        ValueError, match="Changes detected in server1 but no update to CHANGELOG.md"
    ):
        check_commit_changelogs(path)


def test_get_changed_servers_from_staged(temp_repo):
    repo, path = temp_repo
    server_dir = path / "src" / "server1"
    server_dir.mkdir(parents=True)
    file1 = server_dir / "file.txt"
    file1.write_text("content")
    repo.index.add([str(file1)])

    changed = get_changed_servers_from_staged(repo)
    assert changed == {"server1"}


def test_is_changelog_changed_in_staged(temp_repo):
    repo, path = temp_repo
    server_dir = path / "src" / "server1"
    server_dir.mkdir(parents=True)
    changelog = server_dir / "CHANGELOG.md"
    changelog.write_text("changes")
    repo.index.add([str(changelog)])

    assert is_changelog_changed_in_staged(repo, "server1")


def test_check_staged_changelogs(temp_repo):
    repo, path = temp_repo
    server_dir = path / "src" / "server1"
    server_dir.mkdir(parents=True)
    file1 = server_dir / "file.txt"
    file1.write_text("content")
    changelog = server_dir / "CHANGELOG.md"
    changelog.write_text("changes")
    repo.index.add([str(file1), str(changelog)])

    # Should not raise
    check_staged_changelogs(path)

    # Remove changelog from stage
    repo.index.remove([str(changelog)])

    with pytest.raises(
        ValueError, match="Staged changes in server1 but no update to CHANGELOG.md"
    ):
        check_staged_changelogs(path)


def test_check_changelogs_commit_mode(temp_repo):
    repo, path = temp_repo
    server_dir = path / "src" / "server1"
    server_dir.mkdir(parents=True)
    file1 = server_dir / "file.txt"
    file1.write_text("content")
    repo.index.add([str(file1)])
    commit = repo.index.commit("Changes without changelog")

    with pytest.raises(ValueError):
        check_changelogs()


def test_check_changelogs_staged_mode(temp_repo):
    repo, path = temp_repo
    server_dir = path / "src" / "server1"
    server_dir.mkdir(parents=True)
    file1 = server_dir / "file.txt"
    file1.write_text("content")
    repo.index.add([str(file1)])

    with pytest.raises(ValueError):
        check_changelogs(staged=True)
