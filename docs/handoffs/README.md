# UFC EDGE — Handoff Lifecycle

Status: **AUTHORITATIVE POLICY**

New handoffs should live under this tree rather than accumulating at repository root.

Preferred lifecycle:

- `active/` — only work currently in progress;
- `completed/` — recently completed milestone handoffs still useful operationally;
- `historical/` — older context retained for archaeology, not current instruction.

Legacy root handoffs were deliberately left in their existing paths during Repository Organization V1 because they may be referenced by prior workflows, PR descriptions, or chat handoffs. They are **historical/completed context**, not current authority. Future sessions must begin with `../../PROJECT_STATUS.md`.

When a later path-migration explicitly moves legacy handoffs, update every Markdown/workflow/code reference and preserve clear `Superseded by` metadata where applicable.
