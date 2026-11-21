# `pm-ai`

Framework to manage product-management specifications - _spec_ as in spec-driven developments.

This repository is aimed to be installed as user-level agent-skills, and be compatible with Claude Code and Codex.

## Skills

- [`pm-init`](./skills/pm-init/): scaffolds product-related directories in an existing repository
- [`pm-status`](./skills/pm-status/): shows the user what is ready to be picked up, in progress and blocked
  - lists ready items in the order `/pm-next` picks them, and blocked items with their open blockers
  - groups items by their `status` as written and never changes files: stale statuses are `/pm-lint`'s concern
- [`pm-capture`](./skills/pm-capture/): guides the user to capture a new product item
- [`pm-refine`](./skills/pm-refine/): guides the user to clarify and refine a new product item requirements
  - moves the item from `idea` to `clarifying`, then to `ready` (or `ready-but-blocked`) once the user approves it
  - an item is ready when its problem and proposed behaviour are filled in, it lists acceptance criteria, and it has no open questions
  - adds and removes relationships between items on both sides at once (`scripts/relate.py`), refusing cycles
- [`pm-next`](./skills/pm-next/): pick next unblocked ready item for an agent
  - claims it by moving it to `in-progress`, so concurrent agents never pick the same item
  - prefers the item that unblocks the most open work, then the oldest
  - picks features and technical items only: questions are answered by people
- [`pm-complete`](./skills/pm-complete/): marks a product item as done, unblocks dependents
  - for a question, records its outcome as a decision:
    - PDR: `product/decisions/pdrs/`
    - ADR: `product/decisions/adrs/`
- [`pm-deprecate`](./skills/pm-deprecate/): marks a product item as deprecated, and potentially superseded by another feature
  - helps user to capture the rationale behind the deprecation of a previously implemented idea, in a `## Deprecation` section
  - links the replacement (an existing item, or a new one captured on the spot) with `supersedes` / `superseded_by`
  - reviews each item it was blocking: move the link to the replacement, drop it, or deprecate that item too
- [`pm-lint`](./skills/pm-lint/): checks integrity of product-related files:
  - ensure in-file titles are aligned with the file names (items and decisions)
  - detect items or decisions with the same ID
  - detect cyclic dependencies
  - detect contradictory dependencies
  - check questions and their decision records point at each other
  - switch items between `ready` and `ready-but-blocked` as their blockers change
- [`pm-semantic-lint`](./skills/pm-semantic-lint/): heavy duty check that finds contradictory items by inspecting their body
  - reads the vision, every item (whatever its status) and every decision; token-heavy, unlike the local `pm-lint` scripts
  - finds contradictions, duplicates, missing relationships and stale references, quoting the evidence
  - reports everything first, then fixes findings one by one once the user confirms

## Item

Represents a product-related unit.

### Types

- feature: a capability a user sees
  - examples: "export reports as CSV", "support dark mode", etc.

- technical: a "non-functional" requirement
  - examples: "add rate limits to the API", "migrate DB to Postgres 17", etc.

- question: an open issue that must be resolved to unblock work
  - examples: "should support multi-tenant accounts?", "should exports be sync or async?", etc.
  - output: it produces a feature decision (PDR, Product Decision Record) or an technical decision (ADR, Architecture Decision Record)

### Lifecycle

1. `idea`: a vaguely captured thought or intent
2. `clarifying`: a unit still in the process of being explored
3. either:
   - `ready`: a unit ready to be implemented
   - `ready-but-blocked`: a unit that would be ready, but at least one of its blockers is neither `done` nor `deprecated`
4. `in-progress`: a unit in the process of being built
5. `done`: a deployed unit
6. `deprecated`: the unit is no longer deployed

`ready` and `ready-but-blocked` are derived from the blockers, so skills never pick between them by hand: they set either one and run `scripts/sync_ready_status.py`, which sets the right one deterministically. A blocker counts whether it is declared on the blocked item (`blocked_by`) or on the blocker (`blocks`).

### Frontmatter possible values

- `type`: feature | technical | question
- `status`: idea | clarifying | ready | ready-but-blocked | in-progress | done | deprecated
- `related_to`: IDs of other tickets
- `blocks`: IDs of other tickets
- `blocked_by`: IDs of other tickets
- `supersedes`: IDs of other tickets
- `superseded_by`: IDs of other tickets
- `completed`: when the item was marked as done (set by `/pm-complete`)
- `decision`: questions only, the ID of the decision that answered it (set by `/pm-complete`)
- `deprecated`: when the item was deprecated (set by `/pm-deprecate`)

## Decision

The outcome of a `question` item, created by `/pm-complete`:

- `product/decisions/pdrs/PDR-nnnn-<slug>.md`: a Product Decision Record, for decisions that change what users see or can do
- `product/decisions/adrs/ADR-nnnn-<slug>.md`: an Architecture Decision Record, for decisions that change how the system is built

PDRs and ADRs are numbered independently. A decision's `question` field and the question's `decision` field point at each other.

## Installation

The skills are installed at user level (available in every project) by symlinking each `skills/<name>/` folder into the agents' user skill directories:

| Agent       | User skills directory |
|-------------|-----------------------|
| Claude Code | `~/.claude/skills/`   |
| Codex       | `~/.agents/skills/`   |

Because they are symlinks, the installed skills always run the code checked out in this repository: edit, `git pull` or switch branches here and every project picks up the change immediately. The skills also rely on the shared `scripts/` directory at the repository root, which they find by following the symlink back here — so keep the clone in place after installing.

### Install

```bash
git clone <repo-url> ~/projects/pm-ai
~/projects/pm-ai/install.sh
```

Repeat on each device. Re-run `install.sh` after adding or removing a skill: it links new skills, removes links to skills that no longer exist, and leaves correct links alone. It never overwrites anything that isn't a symlink into this repository; such conflicts are reported and make the script exit with status 1.

To install into other directories, set `CLAUDE_SKILLS_DIR` and/or `CODEX_SKILLS_DIR`:

```bash
CODEX_SKILLS_DIR=/somewhere/else ./install.sh
```

### pm-lint hook

`install.sh` also registers a hook that runs `/pm-lint`'s checks whenever a turn changes product frontmatter:

| Agent       | Hooks file                | Override with     |
|-------------|---------------------------|-------------------|
| Claude Code | `~/.claude/settings.json` | `CLAUDE_SETTINGS` |
| Codex       | `~/.codex/hooks.json`     | `CODEX_HOOKS`     |

Only the hook's own entries are added or removed; every other setting and hook in those files is kept. Codex runs a new or changed hook only once you trust it: run `/hooks` in Codex after installing (and again after an update changes the hook).

How it behaves:

1. When you submit a prompt (`UserPromptSubmit`), it fingerprints the frontmatter of every file in `product/items/` and `product/decisions/`. Projects without a `product/items/` directory are ignored.
2. When the agent stops (`Stop`), it checks whether any frontmatter changed during the turn (edited, created or deleted files; body-only edits don't count). If so, it runs the same checks as `/pm-lint` (duplicate IDs, file names, relationships, decisions, ready statuses), without changing anything.
3. If the checks find problems, the agent isn't allowed to stop: it gets the report and runs `/pm-lint`, which asks you before fixing anything. If problems remain after that, you only get a warning, so the hook can't loop.

Snapshots are kept in `${XDG_STATE_HOME:-~/.local/state}/pm-ai/hooks/` and cleaned up after 7 days.

### Update

```bash
git -C ~/projects/pm-ai pull
```

### Uninstall

```bash
~/projects/pm-ai/install.sh --uninstall
```

This removes only the symlinks that point into this repository, and the pm-lint hook entries from the agents' hooks files.

## Development

### Prerequisites

- [Nix](https://nixos.org/download/) with flakes enabled: provides every tool needed (Python 3.14 with pytest, `uv`, `markdownlint`) and the git hooks
- [direnv](https://direnv.net/) with [nix-direnv](https://github.com/nix-community/nix-direnv) (optional): loads the development shell automatically when you `cd` into the repository

### Set up

```bash
git clone <repo-url> ~/projects/pm-ai
cd ~/projects/pm-ai
```

Then enter the development shell, either automatically with direnv:

```bash
echo 'use flake' > .envrc   # only if the clone has no .envrc yet
direnv allow
```

or manually, in each new terminal:

```bash
nix develop
```

The first time takes a while, as Nix builds the shell; later loads are cached. Entering the shell also installs the git pre-commit hook.

To try your changes from other projects, install the skills from this clone (see [Installation](#installation)). They are symlinks, so every edit is live immediately.

### Repository layout

| Path                       | Contents                                                                                                                                                                             |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `skills/<name>/SKILL.md`   | The skill's instructions, as read by the agent                                                                                                                                       |
| `skills/<name>/scripts/`   | Python scripts the skill runs                                                                                                                                                        |
| `skills/<name>/templates/` | Files the skill copies into a project (`vision.md`, `item.md`, `decision.md`, ...)                                                                                                   |
| `scripts/`                 | Code shared by every skill: frontmatter parsing and editing (`pm_items.py`), slugs (`pm_common.py`), the blocking graph and `/pm-next` order (`pm_graph.py`), `sync_ready_status.py` |
| `tests/<name>/`            | Tests for a skill's scripts (`tests/pm_lint/`, ...); `tests/scripts/` tests the shared code                                                                                          |
| `tests/conftest.py`        | Fixtures shared by all tests: a temporary `product/` directory, `write_item`, `write_decision`, ...                                                                                  |
| `hooks/`                   | The pm-lint agent hook (`pm_lint_hook.py`) and the script that registers it in the agents' settings (`register_hooks.py`)                                                            |
| `install.sh`               | Installs the skills by symlinking them, and registers the hook (see [Installation](#installation))                                                                                   |

Skill scripts import the shared code by adding the repository's `scripts/` directory to `sys.path`, found from their own real location (`Path(__file__).resolve().parents[3] / "scripts"`), which is why installed skills must stay symlinked to this clone.

`SKILL.md` files never point outside their own skill directory (no `<skill-base-dir>/../../scripts/...`): agents may normalize such a path as text, which skips the symlink and lands in `~/.claude/`. A skill that needs a shared script gets a small wrapper in its own `scripts/` that runs it (`pm-refine/scripts/relate.py`, `pm-lint/scripts/sync_ready_status.py`, ...). `tests/test_installed_skill_paths.py` enforces this.

### Conventions

- **Deterministic work goes in scripts.** Anything that must always give the same result (IDs, file names, frontmatter edits, status changes) is a Python script the skill runs; `SKILL.md` keeps the steps that need judgment or the user's input.
- **Scripts use only the standard library**, so they run with any `python3` in any project, without installing anything.
- **Tests first.** Write the tests for new script logic, check that they fail for the right reason, then implement until they pass.

### Checks

Run the tests from the development shell:

```bash
pytest
```

The pre-commit hook runs on every commit:

- `markdownlint` on Markdown files (line length is not checked)
- `pytest`, when a Python file changed

To run the same checks as CI would, in a clean sandbox:

```bash
nix flake check
```

The sandbox only sees files tracked by git, so `git add` new files first, or they will be missing from the check.
