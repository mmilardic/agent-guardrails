# Brief: <the outcome, in one line>

Written before an agent starts. The agent works from this file, not from my memory of a conversation.
Every brief is linked from one queue file, which holds the priority order, the rules every session
follows, and a parked-debt list where each item is either scheduled or explicitly killed.

## Background you need

- What exists today and where (paths, not paraphrase).
- Decisions already made, with dates, so they don't get re-litigated.
- What was tried and rejected, and why.

## Scope

- **PR A**: the smallest slice that ships on its own. Ships first.
- **PR B**: …
- **Out of scope**: what not to touch, even if it looks related.

## Done means

- Verified at runtime (browser or emulator), not only compiled. The report separates the two.
- Three-lens review run on the applied tree, then a second pass on whatever the fixes changed.
- User-facing text in every supported language; the help article updated in the same PR.
- PR text written. The merge is mine.

## House rules that bind this work

- Links to the rules that apply, for example [column-drop-is-two-prs](../rules/column-drop-is-two-prs.md).
