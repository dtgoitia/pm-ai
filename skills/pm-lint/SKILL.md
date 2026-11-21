---
name: pm-lint
description: Check product item and decision files for corruption — duplicate IDs, file names whose slug no longer matches the item title, circular or out-of-sync relationships (blocks/blocked_by, supersedes/superseded_by), questions and decision records (PDR/ADR) that don't point at each other, stale `ready` / `ready-but-blocked` statuses — and help fix them. Use when the user runs /pm-lint or asks to check, validate, or clean up the product/ items.
---

# pm-lint

Detects inconsistencies in `product/items/` and in the decision records (PDRs in `product/decisions/pdrs/`, ADRs in `product/decisions/adrs/`). Run the bundled scripts (paths relative to this skill's base directory) from the project root; pass `--product-dir <path>` if the product directory isn't `./product`.

## Steps

1. **Duplicate IDs.**

   ```bash
   python3 <skill-base-dir>/scripts/check_duplicates.py
   ```

   Lists on stderr every item or decision ID used by more than one file (exit code 1 if any). For each duplicate, show the user the files involved and help them decide which item keeps the ID. The other one gets a new ID, updated in both its frontmatter and file name, and in every reference that meant it:
   - item: new ID from `/pm-capture`'s `next_id.py`; references in `related_to` / `blocks` / `blocked_by` / `supersedes` / `superseded_by`, and in the `question` field of its decision
   - decision: new ID from `/pm-complete`'s `next_decision_id.py`; reference in its question's `decision` field Don't change IDs without the user's confirmation.

2. **File names vs. titles.** For items and decisions alike, the frontmatter `title` is the source of truth; the file name must be `<id>-<slug>.md`.

   ```bash
   python3 <skill-base-dir>/scripts/sync_slugs.py --dry-run
   ```

   Show the user the planned renames, then apply them by running the script without `--dry-run`. Report any skipped files (stderr) with their reason — a file-name ID that differs from the frontmatter ID needs the user to decide which one is correct.

3. **Relationships.**

   ```bash
   python3 <skill-base-dir>/scripts/check_relations.py
   ```

   Lists on stderr (exit code 1 if any):
   - **self-references** — an item listing itself in any relationship field
   - **unknown IDs** — references to items that don't exist
   - **out-of-sync pairs** — `A blocked_by B` without `B blocks A` (or the reverse), and likewise for `supersedes` / `superseded_by`
   - **cycles** — in the blocking graph (`A blocks B blocks … blocks A`) and in the supersession graph (`A supersedes B supersedes … supersedes A`)

   `related_to` has no direction, so it can't form a meaningful cycle; it is only checked for self-references and unknown IDs.

   Don't fix these automatically — each needs a decision only the user can make. For each problem, show the items involved (titles included) and propose a fix, then edit the frontmatter once the user confirms:
   - out of sync: either add the missing inverse entry, or remove the stale one if the relationship no longer holds
   - cycle: ask which link in the cycle is wrong and remove it from both sides of the pair
   - self-reference / unknown ID: remove the entry, or correct it if it's a typo for an existing ID

4. **Decisions.**

   ```bash
   python3 <skill-base-dir>/scripts/check_decisions.py
   ```

   A decision answers one question: its `question` field names the question, and the question's `decision` field names it back. Lists on stderr (exit code 1 if any):
   - **misplaced** — a PDR outside `product/decisions/pdrs/`, or an ADR outside `product/decisions/adrs/`
   - **missing question** — a decision without a `question` field
   - **unknown ID** — a `question` or `decision` field naming something that doesn't exist
   - **not a question** — a decision answering a feature or technical item, or such an item having a `decision` field
   - **out of sync** — one side of the link doesn't point back, or points elsewhere
   - **missing decision** — a `done` question without a `decision`

   Don't fix these automatically. A misplaced decision is moved to its kind's directory (`git mv` when the project uses git) once the user confirms. For the rest, show the files involved (titles included), propose a fix and edit the frontmatter once the user confirms. For a missing decision, offer to write one the way `/pm-complete` does (step 3 of its instructions).

5. **Ready statuses.** Run this only once step 3 reports no problems: unknown IDs and one-sided `blocks` / `blocked_by` pairs would make the result wrong.

   ```bash
   python3 <skill-base-dir>/scripts/sync_ready_status.py --dry-run
   ```

   It runs the repository's shared `scripts/sync_ready_status.py`. An item is `ready-but-blocked` while at least one of its blockers (from its `blocked_by` or another item's `blocks`) is neither `done` nor `deprecated`, and `ready` otherwise; no other status is touched. The fix is deterministic, so show the user the planned changes and apply them by running the script without `--dry-run`.

6. **Summarize** what was found and what was fixed.
