import os
import tempfile
from pathlib import Path
import pytest
import tomlkit
from monorepo_utils.bump_versions import (
    get_servers,
    parse_changelog,
    bump_version,
    update_pyproject,
    update_changelog,
    bump_versions,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def create_server_dir(base_dir, name, version="1.0.0", changelog_content=""):
    server_dir = base_dir / "src" / name
    server_dir.mkdir(parents=True)
    pyproject_path = server_dir / "pyproject.toml"
    doc = tomlkit.document()
    doc.add("project", tomlkit.table())
    doc["project"]["version"] = version
    with open(pyproject_path, "w") as f:
        f.write(tomlkit.dumps(doc))

    if changelog_content:
        changelog_path = server_dir / "CHANGELOG.md"
        with open(changelog_path, "w") as f:
            f.write(changelog_content)

    return server_dir


def test_get_servers(temp_dir):
    create_server_dir(temp_dir, "server1")
    create_server_dir(temp_dir, "server2")
    servers = get_servers(temp_dir)
    assert len(servers) == 2
    assert set(s.name for s in servers) == {"server1", "server2"}


def test_parse_changelog_no_unreleased(temp_dir):
    changelog_content = "## [1.0.0] - 2023-01-01\n- Initial release"
    server_dir = create_server_dir(
        temp_dir, "server", changelog_content=changelog_content
    )
    assert parse_changelog(server_dir / "CHANGELOG.md") is None


def test_parse_changelog_with_changes(temp_dir):
    changelog_content = """
## [Unreleased]

### Major
- Breaking change

### Minor
- New feature

### Patch
- Bug fix
"""
    server_dir = create_server_dir(
        temp_dir, "server", changelog_content=changelog_content
    )
    assert parse_changelog(server_dir / "CHANGELOG.md") == "major"


def test_parse_changelog_only_patch(temp_dir):
    changelog_content = """
## [Unreleased]

### Patch
- Bug fix
"""
    server_dir = create_server_dir(
        temp_dir, "server", changelog_content=changelog_content
    )
    assert parse_changelog(server_dir / "CHANGELOG.md") == "patch"


def test_bump_version():
    assert bump_version("1.2.3", "major") == "2.0.0"
    assert bump_version("1.2.3", "minor") == "1.3.0"
    assert bump_version("1.2.3", "patch") == "1.2.4"
    assert bump_version("1.2.3", None) == "1.2.3"


def test_update_pyproject(temp_dir):
    server_dir = create_server_dir(temp_dir, "server", version="1.0.0")
    pyproject_path = server_dir / "pyproject.toml"
    update_pyproject(pyproject_path, "1.1.0")
    with open(pyproject_path, "r") as f:
        doc = tomlkit.parse(f.read())
    assert doc["project"]["version"] == "1.1.0"


def test_update_changelog(temp_dir):
    changelog_content = """
## [Unreleased]

### Minor
- New feature

## [1.0.0] - 2023-01-01
"""
    server_dir = create_server_dir(
        temp_dir, "server", changelog_content=changelog_content
    )
    changelog_path = server_dir / "CHANGELOG.md"
    update_changelog(changelog_path, "1.1.0")
    with open(changelog_path, "r") as f:
        updated = f.read()
    assert "## [Unreleased]" in updated
    assert "### Major" in updated
    assert "### Minor" in updated
    assert "### Patch" in updated
    assert "## [1.1.0] - " in updated
    assert "- New feature" in updated


def test_bump_versions(temp_dir, monkeypatch):
    create_server_dir(
        temp_dir,
        "server",
        changelog_content="""
## [Unreleased]

### Minor
- New feature
""",
    )

    monkeypatch.setattr(os, "environ", {})

    bump_versions(temp_dir)

    pyproject_path = temp_dir / "src" / "server" / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        doc = tomlkit.parse(f.read())
    assert doc["project"]["version"] == "1.1.0"


def test_bump_versions_with_pr(temp_dir, monkeypatch):
    create_server_dir(
        temp_dir,
        "server",
        version="1.0.0",
        changelog_content="""
## [Unreleased]

### Patch
- Fix
""",
    )

    monkeypatch.setattr(os, "environ", {"PR": "123"})

    bump_versions(temp_dir)

    pyproject_path = temp_dir / "src" / "server" / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        doc = tomlkit.parse(f.read())
    assert doc["project"]["version"] == "1.0.1.dev123"


def test_bump_versions_with_merge(temp_dir, monkeypatch):
    create_server_dir(
        temp_dir,
        "server",
        version="1.0.0",
        changelog_content="""
## [Unreleased]

### Patch
- Fix
""",
    )

    monkeypatch.setattr(os, "environ", {"MERGE": "1"})

    bump_versions(temp_dir)

    pyproject_path = temp_dir / "src" / "server" / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        doc = tomlkit.parse(f.read())
    assert doc["project"]["version"] == "1.0.1rc1"


def test_bump_versions_with_release(temp_dir, monkeypatch):
    create_server_dir(
        temp_dir,
        "server",
        version="1.0.0",
        changelog_content="""
## [Unreleased]

### Minor
- New feature
""",
    )

    monkeypatch.setattr(os, "environ", {"RELEASE": "true"})

    bump_versions(temp_dir)

    pyproject_path = temp_dir / "src" / "server" / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        doc = tomlkit.parse(f.read())
    assert doc["project"]["version"] == "1.1.0"

    changelog_path = temp_dir / "src" / "server" / "CHANGELOG.md"
    with open(changelog_path, "r") as f:
        content = f.read()
    assert "## [1.1.0]" in content
    assert "## [Unreleased]" in content
