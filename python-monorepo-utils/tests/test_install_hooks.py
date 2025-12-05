import os
from pathlib import Path
import pytest
from monorepo_utils.install_hooks import install_hooks


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


def test_install_hooks(temp_dir):
    # Create .git directory
    git_dir = temp_dir / ".git"
    git_dir.mkdir()

    install_hooks(temp_dir)

    hook_path = temp_dir / ".git" / "hooks" / "pre-commit"
    assert hook_path.exists()
    assert hook_path.is_file()

    with open(hook_path, "r") as f:
        content = f.read()
    assert content == "#!/bin/sh\nmono-utils check-changelogs --staged\n"

    # Check permissions (executable)
    mode = os.stat(hook_path).st_mode
    assert mode & 0o111 == 0o111  # Executable bits set
