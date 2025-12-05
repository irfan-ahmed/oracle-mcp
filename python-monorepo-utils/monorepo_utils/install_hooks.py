import os
from pathlib import Path


def install_hooks(root_dir="."):
    hooks_dir = Path(root_dir) / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    pre_push_path = hooks_dir / "pre-push"
    with open(pre_push_path, "w") as f:
        f.write(
            f'#!/bin/sh\npython3 "{Path(__file__).parent / "check_changelogs.py"}" --pre-push\n'
        )

    os.chmod(pre_push_path, 0o755)
    print("Installed pre-push hook.")
