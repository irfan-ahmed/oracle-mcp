import os
from pathlib import Path


def install_hooks(root_dir="."):
    hooks_dir = Path(root_dir) / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    pre_commit_path = hooks_dir / "pre-commit"
    with open(pre_commit_path, "w") as f:
        f.write("#!/bin/sh\nmono-utils check-changelogs --staged\n")

    os.chmod(pre_commit_path, 0o755)
    print("Installed pre-commit hook.")
