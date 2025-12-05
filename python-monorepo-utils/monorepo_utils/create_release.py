import os
import re
from pathlib import Path
import git
import semver


def get_servers(root_dir):
    src_dir = Path(root_dir) / "src"
    return [
        d for d in src_dir.iterdir() if d.is_dir() and (d / "pyproject.toml").exists()
    ]


def aggregate_changes(root_dir):
    servers = get_servers(root_dir)
    aggregated = {"major": [], "minor": [], "patch": []}

    for server in servers:
        changelog_path = server / "CHANGELOG.md"
        if not changelog_path.exists():
            continue

        with open(changelog_path, "r") as f:
            content = f.read()

        unreleased_match = re.search(
            r"## \[Unreleased\](.*?)(?=## \[|$)", content, re.DOTALL
        )
        if not unreleased_match:
            continue

        unreleased = unreleased_match.group(1).strip()

        current_type = None
        for line in unreleased.split("\n"):
            if line.startswith("### Major"):
                current_type = "major"
            elif line.startswith("### Minor"):
                current_type = "minor"
            elif line.startswith("### Patch"):
                current_type = "patch"
            elif line.strip() and current_type:
                aggregated[current_type].append(line.strip())

    return aggregated


def determine_bump_type(aggregated):
    if aggregated["major"]:
        return "major"
    elif aggregated["minor"]:
        return "minor"
    elif aggregated["patch"]:
        return "patch"
    return None


def get_latest_tag(repo):
    tags = [t.name for t in repo.tags if semver.VersionInfo.isvalid(t.name.lstrip("v"))]
    if not tags:
        return "0.0.0"
    tags.sort(key=lambda t: semver.VersionInfo.parse(t.lstrip("v")))
    return tags[-1].lstrip("v")


def bump_version(current_version, bump_type):
    ver = semver.VersionInfo.parse(current_version)
    if bump_type == "major":
        return str(ver.bump_major())
    elif bump_type == "minor":
        return str(ver.bump_minor())
    elif bump_type == "patch":
        return str(ver.bump_patch())
    return current_version


def create_release(root_dir="."):
    aggregated = aggregate_changes(root_dir)
    bump_type = determine_bump_type(aggregated)
    if not bump_type:
        print("No changes found. No release needed.")
        return

    repo = git.Repo(root_dir)
    current_version = get_latest_tag(repo)
    new_version = bump_version(current_version, bump_type)

    branch_name = f"release-{new_version}"
    repo.create_head(branch_name)
    print(f"Created release branch: {branch_name}")
