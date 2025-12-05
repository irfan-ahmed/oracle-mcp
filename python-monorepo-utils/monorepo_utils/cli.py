import click
from .bump_versions import bump_versions
from .create_release import create_release
from .check_changelogs import check_changelogs
from .install_hooks import install_hooks


@click.group()
def main():
    pass


@main.command()
def bump_versions_cmd():
    """Bump versions for MCP servers."""
    bump_versions()


@main.command()
def create_release_cmd():
    """Create a new release branch."""
    create_release()


@main.command()
@click.option(
    "--staged", is_flag=True, help="Check staged changes instead of the current commit."
)
def check_changelogs_cmd(staged):
    """Check CHANGELOG.md updates for changes."""
    check_changelogs(staged)


@main.command()
def install_hooks_cmd():
    """Install git hooks."""
    install_hooks()


if __name__ == "__main__":
    main()
