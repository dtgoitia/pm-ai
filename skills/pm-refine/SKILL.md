---
name: pm-refine
description: Clarify and refine a product item's requirements with the user (problem, proposed behaviour, acceptance criteria, open questions, relationships to other items) until it is ready to implement. Use when the user runs /pm-refine or wants to clarify, flesh out, refine or get an idea/item ready.
---

# pm-refine

Guides the user through refining an `idea` or `clarifying` item in `product/items/` until it is ready to implement. Run the bundled scripts from the project root (paths relative to this skill's base directory); pass `--product-dir <path>` if the product directory isn't `./product`. Only `idea` and `clarifying` items can be refined.

## Steps

1. **Pick the item.** If the user didn't name one, list the `idea` and `clarifying` items (ID, title, status) and ask which one to refine.

2. **Start.**

   ```bash
   python3 <skill-base-dir>/scripts/refine_item.py start <ID>
   ```

   This moves an `idea` to `clarifying`; an item already `clarifying` is left as is. Any other status is refused: say so and stop.

3. **Check where it stands.**

   ```bash
   python3 <skill-base-dir>/scripts/refine_item.py check <ID>
   ```

   `missing` lists what keeps the item from being ready. Read the item, then work through the gaps with the user, one section at a time:
   - **Problem:** who has the problem, and why it matters.
   - **Proposed behaviour:** what the user will see or what the system will do. Keep it about behaviour, not implementation.
   - **Acceptance criteria:** a list of concrete, checkable statements (`- [ ] …`), one per item. They define when the item is done.
   - **Open questions:** the decisions still missing. Each question the user answers is removed from the list and its answer written into the right section. Unanswered ones stay listed, and the item stays `clarifying`.

   Ask questions and propose wording, but write only what the user agrees to; don't invent requirements. Edit the item's body directly, then re-run `check`.

4. **Relationships.** When the conversation reveals that this item depends on, unblocks, replaces or relates to another item, edit the relationship with the shared script, which writes both items at once and refuses cycles:

   ```bash
   python3 <skill-base-dir>/scripts/relate.py add|remove <A> <relation> <B>
   ```

   `<relation>` is one of `blocks`, `blocked_by`, `supersedes`, `superseded_by` or `related_to`. Never edit these fields by hand. If the other item doesn't exist yet, offer `/pm-capture` first.

5. **Ready.** When `check` reports nothing `missing`, show the user the refined item (problem, behaviour, acceptance criteria) and ask them to approve it as ready. Only with their explicit approval run:

   ```bash
   python3 <skill-base-dir>/scripts/refine_item.py ready <ID>
   ```

   It sets `ready`, or `ready-but-blocked` if one of its blockers is still open (it names them). Never set either status by hand. If the user doesn't approve, leave the item `clarifying` and note what's left in `## Open questions`.

6. **Summarize** the item's status and what changed, and what's still open if it isn't ready.
