import os
import re
from datetime import date
import tomlkit
import semver
from pathlib import Path


def get_servers(root_dir):
    src_dir = Path(root_dir) / "src"
    return [
        d for d in src_dir.iterdir() if d.is_dir() and (d / "pyproject.toml").exists()
    ]


def parse_changelog(changelog_path):
    with open(changelog_path, "r") as f:
        content = f.read()

    unreleased_match = re.search(
        r"## \[Unreleased\](.*?)(?=## \[|$)", content, re.DOTALL
    )
    if not unreleased_match:
        return None

    unreleased = unreleased_match.group(1).strip()

    changes = {"major": [], "minor": [], "patch": []}
    current_type = None
    for line in unreleased.split("\n"):
        if line.startswith("### Major"):
            current_type = "major"
        elif line.startswith("### Minor"):
            current_type = "minor"
        elif line.startswith("### Patch"):
            current_type = "patch"
        elif line.strip() and current_type:
            changes[current_type].append(line.strip())

    if any(changes.values()):
        if changes["major"]:
            return "major"
        elif changes["minor"]:
            return "minor"
        else:
            return "patch"
    return None


def bump_version(current_version, bump_type):
    ver = semver.VersionInfo.parse(current_version)
    if bump_type == "major":
        return str(ver.bump_major())
    elif bump_type == "minor":
        return str(ver.bump_minor())
    elif bump_type == "patch":
        return str(ver.bump_patch())
    return current_version


def update_pyproject(pyproject_path, new_version):
    with open(pyproject_path, "r") as f:
        doc = tomlkit.parse(f.read())
    doc["project"]["version"] = new_version
    with open(pyproject_path, "w") as f:
        f.write(tomlkit.dumps(doc))


def update_changelog(changelog_path, new_version):
    today = date.today().isoformat()
    with open(changelog_path, "r") as f:
        content = f.read()

    unreleased_match = re.search(
        r"## \[Unreleased\](.*?)(?=## \[|$)", content, re.DOTALL
    )
    if not unreleased_match:
        return

    unreleased_content = unreleased_match.group(1).strip()

    new_section = f"## [{new_version}] - {today}\n{unreleased_content}\n"

    content = content.replace(
        unreleased_match.group(0),
        f"## [Unreleased]\n\n### Major\n\n### Minor\n\n### Patch\n\n{new_section}",
    )

    with open(changelog_path, "w") as f:
        f.write(content)


def bump_versions(root_dir="."):
    servers = get_servers(root_dir)
    pr = os.environ.get("PR")
    merge = os.environ.get("MERGE")
    release = os.environ.get("RELEASE")

    for server in servers:
        changelog_path = server / "CHANGELOG.md"
        if not changelog_path.exists():
            continue

        bump_type = parse_changelog(changelog_path)
        if not bump_type:
            continue

        pyproject_path = server / "pyproject.toml"
        with open(pyproject_path, "r") as f:
            doc = tomlkit.parse(f.read())
        current_version = doc["project"]["version"]

        new_version = bump_version(current_version, bump_type)

        if pr:
            new_version += ".dev" + pr
        elif merge:
            new_version += "rc" + merge

        update_pyproject(pyproject_path, new_version)

        if release:
            update_changelog(changelog_path, new_version)
