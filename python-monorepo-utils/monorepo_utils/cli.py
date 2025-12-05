import click
from .bump_versions import bump_versions
from .create_release import create_release
from .check_changelogs import check_changelogs
from .install_hooks import install_hooks


class CustomGroup(click.Group):
    def format_help(self, ctx, formatter):
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        formatter.write_paragraph()

        formatter.write_heading("Commands:")
        rows = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None:
                continue
            rows.append((subcommand, cmd.get_short_help_str()))

        formatter.write_dl(rows)

        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd:
                formatter.write_paragraph()
                formatter.write_text(f"{subcommand} options:")
                cmd.format_options(ctx, formatter)


@click.group(cls=CustomGroup)
def main():
    """Monorepo utilities CLI."""
    pass


@main.command(name="bump-versions")
def bump_versions_cmd():
    """Bump versions for MCP servers."""
    bump_versions()


@main.command(name="create-release")
def create_release_cmd():
    """Create a new release branch."""
    create_release()


@main.command(name="check-changelogs")
@click.option(
    "--staged", is_flag=True, help="Check staged changes instead of the current commit."
)
def check_changelogs_cmd(staged):
    """Check CHANGELOG.md updates for changes."""
    check_changelogs(staged)


@main.command(name="install-hooks")
def install_hooks_cmd():
    """Install git hooks."""
    install_hooks()


if __name__ == "__main__":
    main()
