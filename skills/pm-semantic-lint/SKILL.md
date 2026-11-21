---
name: pm-semantic-lint
description: Read every product file (vision, items of any status, PDR/ADR decisions) and find problems only the content reveals — contradictions, duplicates, missing relationships, stale references — then fix them with the user. Token-heavy, unlike /pm-lint. Use when the user runs /pm-semantic-lint or asks to check product specs for contradictions, duplicates or inconsistencies.
---

# pm-semantic-lint

Finds inconsistencies in the *content* of the product files. `/pm-lint` checks structure with local scripts and costs no tokens; this skill reads and compares everything, so it is slow and token-heavy. Run the bundled script (path relative to this skill's base directory) from the project root; pass `--product-dir <path>` if the product directory isn't `./product`.

## Steps

1. **Structure first.** Run `/pm-lint`'s token-free checks:

   ```bash
   python3 <skill-base-dir>/../pm-lint/scripts/check_duplicates.py
   python3 <skill-base-dir>/../pm-lint/scripts/check_relations.py
   python3 <skill-base-dir>/../pm-lint/scripts/check_decisions.py
   ```

   If any of them reports a problem, tell the user and suggest running `/pm-lint` first: duplicate IDs and broken links make the semantic review unreliable. Continue only if the user wants to anyway.

2. **Read everything.**

   ```bash
   python3 <skill-base-dir>/scripts/corpus.py
   ```

   It prints an index (ID, kind, status, title, path) and then the full content of `product/vision.md`, every decision and every item, whatever its status, in a fixed order. Read all of it before judging anything.

3. **Find problems.** Compare the files against each other and keep track of the evidence for each finding: the exact sentences, quoted from each file involved.
   - **Contradiction:** two files require incompatible things (behaviour, limits, data, scope). Check open items against each other, against `done` items (shipped behaviour), against decisions, and against the vision.
   - **Duplicate / overlap:** two items describe the same work, or a large part of it.
   - **Missing relationship:** the bodies make a dependency, a replacement or a strong link obvious (e.g. "requires the export API from …"), but the frontmatter lacks the `blocks` / `blocked_by`, `supersedes` / `superseded_by` or `related_to` entry.
   - **Stale reference:** an item still relies on something a later decision changed, or on a `deprecated` item.

   A contradiction with a `done` item isn't always a mistake: the open item may be meant to change shipped behaviour. Then the finding is that it should declare `supersedes` (or the user should say so explicitly in its body).

   Don't report differences in wording, missing detail in early `idea` items, or matters of taste. Report only what you can back with quotes.

4. **Report.** List every finding before fixing anything, grouped by kind, most serious first. For each one give the IDs and titles involved, the quoted evidence and a one-line explanation. If nothing was found, say so and stop.

5. **Fix with the user.** Go through the findings one at a time. Propose a fix and apply it only once the user confirms; the user may also skip a finding. Typical fixes:
   - edit an item's body to remove the contradiction (never edit a decision's outcome: if a decision is wrong, capture a new `question` with `/pm-capture`)
   - add a missing relationship, always on both sides (`blocks` + `blocked_by`, `supersedes` + `superseded_by`, `related_to` on each item)
   - mark a duplicate as `deprecated`, with `superseded_by` pointing at the item that replaces it (and `supersedes` on that item)
   - capture an open question with `/pm-capture` when the right answer needs a decision, and link it with `blocks` to the items it holds up

6. **Tidy up.** If any fix changed a title, `blocks`, `blocked_by` or a status, run the deterministic follow-ups:

   ```bash
   python3 <skill-base-dir>/../pm-lint/scripts/sync_slugs.py
   python3 <skill-base-dir>/scripts/sync_ready_status.py
   ```

   Then summarize what was found, what was fixed and what was skipped.
