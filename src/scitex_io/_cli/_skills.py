"""`scitex-io skills` — list / get / install agent-facing skills.

Self-contained. No scitex-dev runtime dep — walks the package's own
`_skills/scitex-io/` directory directly.
"""

from __future__ import annotations

import os as _os
import sys as _sys
from pathlib import Path

import click

PKG = "scitex-io"

# ---------------------------------------------------------------------------
# Plugin port: SCITEX_IO_SKILLS_DEST
#
# The default destination for `skills install` is the canonical skills
# directory managed by scitex-dev (~/.scitex/dev/skills/).  Per the
# local-state-directories rule (§9.5), scitex-io must not hardcode
# another package's namespace, so consumers set this env var from their
# own tree:
#
#     export SCITEX_IO_SKILLS_DEST=~/.scitex/dev/skills
#
# The hardcoded fallback is retained for one minor version (backward
# compat, §8) and will be removed in the next release.
# ---------------------------------------------------------------------------
_ENV_SKILLS_DEST = "SCITEX_IO_SKILLS_DEST"


def _default_skills_dest() -> Path:
    """Return the skills installation target directory.

    Precedence (highest first):
      1. ``SCITEX_IO_SKILLS_DEST`` env var
      2. ``~/.scitex/dev/skills/`` (legacy — deprecated, one-version back-compat)
    """
    env = _os.environ.get(_ENV_SKILLS_DEST)
    if env:
        return Path(env).expanduser()

    # Deprecation: hardcoded fallback to dev's namespace (§9.5, §8).
    _sys.stderr.write(
        "scitex-io: WARNING ~/.scitex/dev/skills/ fallback is deprecated.\n"
        f"  Set {_ENV_SKILLS_DEST}=<dest> to suppress this warning.\n"
        "  This fallback will be removed in the next release.\n"
    )
    return Path.home() / ".scitex" / "dev" / "skills"


def _skills_root() -> Path:
    """Resolve the bundled `_skills/scitex-io/` directory."""
    import scitex_io

    pkg_dir = Path(scitex_io.__file__).parent
    return pkg_dir / "_skills" / PKG


def _list_skill_files(root: Path) -> list[Path]:
    """All `.md` files under `_skills/scitex-io/` (recursive), excluding SKILL.md."""
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.md") if p.is_file() and p.name != "SKILL.md")


@click.group(name="skills", invoke_without_command=True)
@click.pass_context
def skills_group(ctx) -> None:
    """Agent-facing skills bundled with scitex-io.

    \b
    Examples:
      $ scitex-io skills list
      $ scitex-io skills get 01_installation
      $ scitex-io skills install                  # → ~/.scitex/dev/skills/scitex-io/
      $ scitex-io skills install --claude-symlink # also expose to ~/.claude/skills/scitex/
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@skills_group.command(name="list")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
def skills_list(as_json: bool) -> None:
    """List skill files bundled with this package.

    \b
    Example:
      $ scitex-io skills list
      $ scitex-io skills list --json
    """
    root = _skills_root()
    files = _list_skill_files(root)
    if as_json:
        import json as _json

        click.echo(
            _json.dumps(
                [{"name": p.stem, "path": str(p)} for p in files],
                indent=2,
            )
        )
        return
    if not files:
        click.echo(f"no skills found at {root}", err=True)
        raise SystemExit(1)
    for p in files:
        rel = p.relative_to(root)
        click.echo(f"{p.stem:36s}  {rel}")


@skills_group.command(name="get")
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
def skills_get(name: str, as_json: bool) -> None:
    """Print the contents of a skill file by NAME (e.g. `01_installation`).

    \b
    Example:
      $ scitex-io skills get 01_installation
      $ scitex-io skills get 02_quick-start --json
    """
    root = _skills_root()
    target_stem = name[:-3] if name.endswith(".md") else name
    match = next((p for p in _list_skill_files(root) if p.stem == target_stem), None)
    if match is None:
        click.echo(f"skill not found: {name}", err=True)
        available = ", ".join(p.stem for p in _list_skill_files(root)[:8])
        click.echo(f"available: {available}…", err=True)
        raise SystemExit(1)
    if as_json:
        import json as _json

        click.echo(
            _json.dumps(
                {
                    "name": match.stem,
                    "path": str(match),
                    "content": match.read_text(encoding="utf-8"),
                },
                indent=2,
            )
        )
        return
    click.echo(match.read_text(encoding="utf-8"))


@skills_group.command(name="install")
@click.option(
    "--dest",
    type=click.Path(),
    default=None,
    help="Destination dir (default: $SCITEX_IO_SKILLS_DEST or ~/.scitex/dev/skills/scitex-io/).",
)
@click.option(
    "--no-link",
    "no_link",
    is_flag=True,
    help="Copy files instead of symlinking. Default is symlink.",
)
@click.option(
    "--claude-symlink",
    is_flag=True,
    help="Also expose at ~/.claude/skills/scitex/ for Claude Code consumers.",
)
@click.option("--dry-run", is_flag=True, help="Preview without copying/linking.")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
def skills_install(
    dest: str | None,
    no_link: bool,
    claude_symlink: bool,
    dry_run: bool,
    yes: bool,
) -> None:
    """Install this package's skills into a target directory.

    \b
    Default destination (precedence order):
      1. --dest <path>
      2. $SCITEX_IO_SKILLS_DEST env var
      3. ~/.scitex/dev/skills/  (deprecated, one-version back-compat)

    Default action: symlink the entire `_skills/scitex-io/` dir so
    add/rename/delete in source propagates immediately.

    \b
    Example:
      $ scitex-io skills install
      $ scitex-io skills install --claude-symlink
      $ scitex-io skills install --no-link --dest /tmp/scitex-io-skills
    """
    del yes  # accepted for §2 compliance; install is non-interactive
    src = _skills_root().resolve()
    if not src.is_dir():
        click.echo(f"no skills directory at {src}", err=True)
        raise SystemExit(1)

    base = Path(dest).expanduser() if dest else _default_skills_dest()
    target = base / PKG

    if dry_run:
        action = "copy" if no_link else "symlink"
        click.echo(f"would {action} {src} → {target}")
        if claude_symlink:
            link = Path.home() / ".claude" / "skills" / "scitex"
            click.echo(f"would symlink {link} → {base}")
        return

    base.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        import shutil as _shutil

        _shutil.rmtree(target)

    if no_link:
        import shutil as _shutil

        _shutil.copytree(src, target)
        click.echo(f"copied {src} → {target}")
    else:
        _os.symlink(src, target, target_is_directory=True)
        click.echo(f"linked {target} → {src}")

    if claude_symlink:
        link = Path.home() / ".claude" / "skills" / "scitex"
        link.parent.mkdir(parents=True, exist_ok=True)
        if link.is_symlink():
            link.unlink()
        if not link.exists():
            _os.symlink(base.resolve(), link, target_is_directory=True)
            click.echo(f"linked {link} → {base}")
        else:
            click.echo(
                f"warning: {link} exists and is not a symlink — skipping",
                err=True,
            )
