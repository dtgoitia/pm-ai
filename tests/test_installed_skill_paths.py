"""Skills installed as symlinks must work however the agent resolves their paths.

Claude Code hands a skill its base directory as the symlink path
(`~/.claude/skills/<name>`). `<skill-base-dir>/../..` from there reaches this
repository only if `..` is resolved physically; an agent that normalizes the
path as text lands in `~/.claude/`. So every path a SKILL.md gives must
exist under both readings, and the wrappers that reach the shared `scripts/`
must run from the symlinked location.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from pm_items import parse_frontmatter

SKILLS = sorted(p for p in (REPO / "skills").iterdir() if (p / "SKILL.md").is_file())
PATH_RE = re.compile(r"<skill-base-dir>(/[^\s`\"']+)")


@pytest.fixture
def installed(tmp_path: Path) -> Path:
    """A `skills/` directory with every skill symlinked into it, as install.sh does."""
    skills = tmp_path / "home" / ".claude" / "skills"
    skills.mkdir(parents=True)
    for skill in SKILLS:
        (skills / skill.name).symlink_to(skill, target_is_directory=True)
    return skills


def skill_paths() -> list[tuple[str, str]]:
    return [
        (skill.name, match)
        for skill in SKILLS
        for match in PATH_RE.findall((skill / "SKILL.md").read_text(encoding="utf-8"))
    ]


@pytest.mark.parametrize(("skill", "rel"), skill_paths())
def test_skill_md_paths_exist_when_normalized_as_text(installed, skill, rel):
    path = str(installed / skill) + rel

    assert os.path.exists(path), f"{skill}: {path} does not exist"
    assert os.path.exists(os.path.normpath(path)), (
        f"{skill}: <skill-base-dir>{rel} escapes the installed skills directory; "
        "point SKILL.md at a wrapper inside the skill instead"
    )


def run_installed(installed: Path, product: Path, skill: str, script: str, *args: str):
    return subprocess.run(
        [sys.executable, str(installed / skill / "scripts" / script), "--product-dir", str(product), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=installed.parent,
    )


def item(write_item, item_id, status, **fields):
    return write_item(f"{item_id}-x.md", id=item_id, title=item_id, type="feature", status=status, **fields)


def test_relate_wrapper_runs_from_symlinked_skill(installed, product, write_item):
    a = item(write_item, "F-0001", "clarifying")
    b = item(write_item, "F-0002", "clarifying")

    result = run_installed(installed, product, "pm-refine", "relate.py", "add", "F-0001", "blocks", "F-0002")

    assert result.returncode == 0, result.stderr
    assert parse_frontmatter(a.read_text())["blocks"] == ["F-0002"]
    assert parse_frontmatter(b.read_text())["blocked_by"] == ["F-0001"]


@pytest.mark.parametrize("skill", ["pm-lint", "pm-semantic-lint"])
def test_sync_ready_status_wrapper_runs_from_symlinked_skill(installed, product, write_item, skill):
    item(write_item, "F-0001", "clarifying", blocks=["F-0002"])
    blocked = item(write_item, "F-0002", "ready", blocked_by=["F-0001"])

    result = run_installed(installed, product, skill, "sync_ready_status.py")

    assert result.returncode == 0, result.stderr
    assert parse_frontmatter(blocked.read_text())["status"] == "ready-but-blocked"
