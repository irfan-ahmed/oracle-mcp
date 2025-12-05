import git
from pathlib import Path
import argparse
import re


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


def determine_category(title):
    title_lower = title.lower()
    if any(
        title_lower.startswith(word)
        for word in ["chore", "patch", "doc", "test", "style"]
    ):
        return "Patch"
    elif any(
        title_lower.startswith(word) for word in ["minor", "fix", "refactor", "perf"]
    ):
        return "Minor"
    elif any(title_lower.startswith(word) for word in ["feat", "major", "breaking"]):
        return "Major"
    return "Patch"


def update_changelog_with_entry(changelog_path, category, title):
    with open(changelog_path, "r") as f:
        content = f.read()

    # Find unreleased section
    unreleased_match = re.search(
        r"## \[Unreleased\](.*?)(?=## \[|$)", content, re.DOTALL
    )
    if not unreleased_match:
        print(f"No unreleased section found in {changelog_path}. Skipping update.")
        return

    # Pattern for the specific subsection
    pattern = r"### " + category + r"\n(.*?)(?=### |$)"
    match = re.search(pattern, unreleased_match.group(1), re.DOTALL)
    if match:
        old_content = match.group(1)
        new_line = "- " + title + "\n"
        new_content = old_content + new_line if old_content.strip() else new_line
        new_unreleased = re.sub(
            pattern,
            "### " + category + "\n" + new_content,
            unreleased_match.group(1),
            flags=re.DOTALL,
        )
        content = content.replace(unreleased_match.group(1), new_unreleased)

        with open(changelog_path, "w") as f:
            f.write(content)
        print(f"Updated {changelog_path} in {category} section with '- {title}'")
    else:
        print(
            f"No {category} subsection found in unreleased for {changelog_path}. Skipping update."
        )


def check_changelogs(staged=False):
    if staged:
        check_staged_changelogs()
    else:
        check_commit_changelogs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-push", action="store_true")
    args = parser.parse_args()

    if args.pre_push:
        repo = git.Repo(".")
        head_commit = repo.head.commit
        changed_servers = get_changed_servers_from_commit(repo, head_commit)
        missing = [
            server
            for server in changed_servers
            if not is_changelog_changed_in_commit(repo, head_commit, server)
        ]

        if missing:
            title = head_commit.message.splitlines()[0].strip()
            category = determine_category(title)

            for server in missing:
                changelog_path = Path("src") / server / "CHANGELOG.md"
                update_changelog_with_entry(changelog_path, category, title)
                repo.git.add(str(changelog_path))

            repo.git.commit("--amend", "--no-edit")
            print("Amended the head commit with CHANGELOG updates.")
