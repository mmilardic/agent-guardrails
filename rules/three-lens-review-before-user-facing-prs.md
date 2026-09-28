---
name: three-lens-review-before-user-facing-prs
description: A correctness pass is not a review. Any user-facing change gets the three-lens review on the applied tree before the PR opens, and a second pass on the fixes.
type: feedback
---

"Reviewed" means the [three-lens review](../review/three-lens-review.md): UX and web/phone parity; code
quality and tests; compatibility with released app versions, security and docs. A correctness pass on
the diff alone doesn't count, and a report must say which one ran.

**Why:** a correctness pass approved a batch of user-facing PRs; the three-lens review then found three
real problems in them, including a compatibility check that could have passed while phones in the field
were still sending the old field.

**How to apply:** run it on the applied tree before opening the PR, verify each finding before fixing
it, then run one targeted pass over only what the fixes changed.
