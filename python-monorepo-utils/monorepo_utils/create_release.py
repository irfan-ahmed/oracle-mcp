import os
import re
from pathlib import Path
import git
import semver
import subprocess


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


def git_push(branch_name):
    try:
        print(f"Now pushing {branch_name} to origin\n")
        # Construct the git push command
        command = ["git", "push", "-u", "origin", branch_name]

        # Execute the command
        process = subprocess.Popen(
            command,
            cwd=".",  # Set the working directory for the command
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Decode output as text (UTF-8 by default)
        )

        # Communicate with the process and get output
        stdout, stderr = process.communicate()

        # Print the output
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)

        # Check the return code for success or failure
        if process.returncode != 0:
            print(f"Git push failed with exit code: {process.returncode}")
            return False
        else:
            return True

    except FileNotFoundError:
        print(
            "Error: 'git' command not found. Please ensure Git is installed and in your PATH."
        )
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


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

    repo.git.checkout(branch_name)
    print(f"Checked out to {branch_name}")

    git_push(branch_name)
    print(f"Pushed {branch_name} to origin")
