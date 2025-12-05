import os
from pathlib import Path
import pytest
import git
from monorepo_utils.create_release import (
    get_servers,
    aggregate_changes,
    determine_bump_type,
    get_latest_tag,
    bump_version,
    create_release,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def mock_repo(temp_dir):
    repo = git.Repo.init(temp_dir)
    yield repo


def create_server_dir(base_dir, name, changelog_content=""):
    server_dir = base_dir / "src" / name
    server_dir.mkdir(parents=True)
    if changelog_content:
        changelog_path = server_dir / "CHANGELOG.md"
        with open(changelog_path, "w") as f:
            f.write(changelog_content)
    (server_dir / "pyproject.toml").touch()  # Just to mark as server
    return server_dir


def test_aggregate_changes(temp_dir):
    create_server_dir(
        temp_dir,
        "server1",
        changelog_content="""
## [Unreleased]

### Major
- Break1

### Minor
- Feat1
""",
    )
    create_server_dir(
        temp_dir,
        "server2",
        changelog_content="""
## [Unreleased]

### Patch
- Fix1
""",
    )

    aggregated = aggregate_changes(temp_dir)
    assert aggregated["major"] == ["- Break1"]
    assert aggregated["minor"] == ["- Feat1"]
    assert aggregated["patch"] == ["- Fix1"]


def test_determine_bump_type():
    assert (
        determine_bump_type({"major": ["change"], "minor": [], "patch": []}) == "major"
    )
    assert (
        determine_bump_type({"major": [], "minor": ["change"], "patch": []}) == "minor"
    )
    assert (
        determine_bump_type({"major": [], "minor": [], "patch": ["change"]}) == "patch"
    )
    assert determine_bump_type({"major": [], "minor": [], "patch": []}) is None


def test_get_latest_tag(mock_repo):
    mock_repo.create_tag("v1.0.0")
    mock_repo.create_tag("v2.0.0")
    mock_repo.create_tag("invalid")
    assert get_latest_tag(mock_repo) == "2.0.0"


def test_get_latest_tag_no_tags(mock_repo):
    assert get_latest_tag(mock_repo) == "0.0.0"


def test_create_release(temp_dir, monkeypatch):
    create_server_dir(
        temp_dir,
        "server",
        changelog_content="""
## [Unreleased]

### Minor
- New feature
""",
    )

    # Mock git repo
    repo = git.Repo.init(temp_dir)
    repo.create_tag("v1.0.0")

    # Mock print
    printed = []
    monkeypatch.setattr("builtins.print", lambda msg: printed.append(msg))

    create_release(temp_dir)

    assert "release-1.1.0" in repo.branches
    assert any("Created release branch: release-1.1.0" in p for p in printed)


def test_create_release_no_changes(temp_dir, monkeypatch):
    create_server_dir(temp_dir, "server", changelog_content="## [Unreleased]")

    # Mock git repo
    git.Repo.init(temp_dir)

    # Mock print
    printed = []
    monkeypatch.setattr("builtins.print", lambda msg: printed.append(msg))

    create_release(temp_dir)

    assert any("No changes found. No release needed." in p for p in printed)
